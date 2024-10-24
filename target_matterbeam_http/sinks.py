"""Matterbeam HTTP target sink class, which handles writing streams."""

from __future__ import annotations

import datetime
import decimal
import json
from functools import cached_property
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Sequence
from urllib.parse import urlparse

import backoff
import requests  # type: ignore[import-untyped]
from singer_sdk.exceptions import FatalAPIError, RetriableAPIError
from singer_sdk.sinks import BatchSink

if TYPE_CHECKING:
    from singer_sdk import Target
    from singer_sdk.helpers.types import Context

DEFAULT_REQUEST_TIMEOUT = 300  # 5 minutes


class CustomJSONEncoder(json.JSONEncoder):
    """JSON serializer for objects not serializable by default."""

    def default(self, obj: dict) -> dict:
        """A serializable representation of obj."""
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()

        return json.JSONEncoder.default(self, obj)


class HttpBatchSink(BatchSink):
    """HTTP Batch sink class."""

    _requests_session: requests.Session | None

    #: Optional flag to disable HTTP redirects.
    allow_redirects: bool = False

    #: Response code reference for rate limit retries.
    extra_retry_statuses: Sequence[int] = [HTTPStatus.TOO_MANY_REQUESTS]

    #: HTTP method to use for requests.
    http_method = "POST"

    def __init__(
        self,
        target: Target,
        stream_name: str,
        schema: dict,
        key_properties: Sequence[str] | None,
    ) -> None:
        """Initialize target sink."""
        super().__init__(target, stream_name, schema, key_properties)

        self._requests_session = requests.Session()

    @property
    def endpoint(self) -> str:
        """Get the stream entity URL."""
        raise NotImplementedError

    @property
    def http_headers(self) -> dict:
        """Return headers dict to be used for HTTP requests.

        Returns:
            Dictionary of HTTP headers to use as a base for every request.
        """
        return {}

    @property
    def requests_session(self) -> requests.Session:
        """Get requests session.

        Returns:
            The :class:`requests.Session` object for HTTP requests.
        """
        if not self._requests_session:
            self._requests_session = requests.Session()

        return self._requests_session

    @property
    def timeout(self) -> int:
        """Return the request timeout limit in seconds.

        The default timeout is 300 seconds, or as defined by DEFAULT_REQUEST_TIMEOUT.

        Returns:
            The request timeout limit as number of seconds.
        """
        return DEFAULT_REQUEST_TIMEOUT

    @property
    def url_base(self) -> str:
        """The base request URL."""
        raise NotImplementedError

    @cached_property
    def user_agent(self) -> str:
        """Get the user agent string for the stream.

        Returns:
            The user agent string.
        """
        return self.config.get("user_agent", "matterbeam-tap/0.0.0")

    def get_url_params(
        self,
        context: Context | None,  # noqa: ARG002
    ) -> dict[str, Any] | str:
        """Return a dictionary or string of URL query parameters.

        Args:
            context: Stream partition or context dictionary.

        Returns:
            Dictionary or encoded string with URL query parameters to use in the
                request.
        """
        return {}

    @backoff.on_exception(
        backoff.expo, requests.exceptions.RequestException, max_tries=5
    )
    def make_request(
        self,
        prepared_request: requests.PreparedRequest,
        context: Context | None,  # noqa: ARG002
    ) -> requests.Response:
        """Make a request using the prepared request object.

        Args:
            prepared_request: The prepared request object.
            context: Stream partition or context dictionary.

        Returns:
            The response object.
        """
        resp = self.requests_session.send(
            prepared_request, timeout=self.timeout, allow_redirects=self.allow_redirects
        )

        self.validate_response(resp)
        self.logger.debug("Response received successfully.")

        return resp

    def prepare_request(
        self,
        context: Context | None,
    ) -> requests.PreparedRequest:
        """Prepare a request object.

        Args:
            context: Stream partition or context dictionary.

        Returns:
            Build a request with the stream's URL, path, query parameters,
            HTTP headers and authenticator.
        """
        headers = self.http_headers
        http_method = self.http_method
        url = self.endpoint

        data = self.get_request_payload(context=context)
        params = self.get_url_params(context=context)

        request = requests.Request(
            headers=headers,
            json=data,
            method=http_method,
            params=params,
            url=url,
        )

        return self.requests_session.prepare_request(request)

    def get_request_payload(
        self,
        context: Context | None,
    ) -> dict | None:
        """Prepare the data payload for the REST API request."""
        records = []

        if context is not None:
            records = context["records"]

        return json.loads(json.dumps(records, cls=CustomJSONEncoder))

    def process_batch(self, context: Context) -> None:
        """Process a batch with the given batch context.

        Args:
            context: Stream partition or context dictionary.
        """
        prepared_request = self.prepare_request(context=context)
        self.make_request(context=context, prepared_request=prepared_request)

    def response_error_message(self, response: requests.Response) -> str:
        """Build error message for invalid http statuses.

        WARNING - Override this method when the URL path may contain secrets or PII

        Args:
            response: A :class:`requests.Response` object.

        Returns:
            str: The error message
        """
        full_path = urlparse(response.url).path

        error_type = (
            "Client"
            if HTTPStatus.BAD_REQUEST
            <= response.status_code
            < HTTPStatus.INTERNAL_SERVER_ERROR
            else "Server"
        )

        return (
            f"{response.status_code} {error_type} Error: "
            f"{response.reason} for path: {full_path}"
        )

    def validate_response(self, response: requests.Response) -> None:
        """Validate HTTP response.

        Checks for error status codes and whether they are fatal or retriable.

        Args:
            response: A :class:`requests.Response` object.

        Raises:
            FatalAPIError: If the request is not retriable.
            RetriableAPIError: If the request is retriable.
        """
        if (
            response.status_code in self.extra_retry_statuses
            or response.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR
        ):
            msg = self.response_error_message(response)
            raise RetriableAPIError(msg, response)

        if (
            HTTPStatus.BAD_REQUEST
            <= response.status_code
            < HTTPStatus.INTERNAL_SERVER_ERROR
        ):
            msg = self.response_error_message(response)
            raise FatalAPIError(msg)


class MatterbeamHttpSink(HttpBatchSink):
    """Matterbeam HTTP sink class."""

    http_method = "PUT"

    @property
    def endpoint(self) -> str:
        """Get the stream entity URL."""
        return f"{self.url_base}/datasets/{self.stream_name}/records"

    @property
    def http_headers(self) -> dict:
        """Return headers dict to be used for HTTP requests.

        Returns:
            Dictionary of HTTP headers to use as a base for every request.
        """
        return {
            "Authorization": f"Token {self.config['api_token']}",
            "Content-Type": "application/json",
        }

    @property
    def url_base(self) -> str:
        """The base request URL."""
        return self.config["api_url"]
