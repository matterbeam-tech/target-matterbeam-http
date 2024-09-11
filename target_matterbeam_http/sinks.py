"""MatterbeamHttp target sink class, which handles writing streams."""

from __future__ import annotations
from singer_sdk.sinks import BatchSink, RecordSink

import requests

from target_matterbeam_http.utils.debug import debug_requests_on

debug_requests_on()


class MatterbeamHttpBatchSink(BatchSink):

    def process_batch(self, context: dict) -> None:
        """Process a batch with the given batch context.

        Args:
            context: Stream partition or context dictionary.
        """

        api_token = self.config.get("api_token")
        base_url = self.config.get("api_url")

        records = context["records"]
        dataset_name = f"{self.stream_name}__batched"

        requests.put(
            f"{base_url}/datasets/{dataset_name}/records",
            json=records,
            headers={
                "Authorization": f"Token {api_token}",
                "Content-Type": "application/json",
            },
        )


class MatterbeamHttpRecordSink(RecordSink):

    def process_record(self, record: dict, context: dict) -> None:
        """Process the record.

        Args:
            record: Individual record in the stream.
            context: Stream partition or context dictionary.
        """

        api_token = self.config.get("api_token")
        base_url = self.config.get("api_url")

        requests.put(
            f"{base_url}/datasets/{self.stream_name}/record",
            json=record,
            headers={
                "Authorization": f"Token {api_token}",
                "Content-Type": "application/json",
            },
        )
