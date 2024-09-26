"""MatterbeamHttp target class."""

from __future__ import annotations

from singer_sdk import typing as th
from singer_sdk.sinks import Sink
from singer_sdk.target_base import Target

from target_matterbeam_http.sinks import MatterbeamHttpSink


class TargetMatterbeamHttp(Target):
    """Sample target for MatterbeamHttp."""

    name = "target-matterbeam-http"

    config_jsonschema = th.PropertiesList(
        th.Property("api_token", th.StringType, secret=True, required=True),
        th.Property("api_url", th.StringType, secret=True, required=True),
    ).to_dict()

    def get_sink_class(self, stream_name: str) -> type[Sink]:
        """Get sink for a stream.

        Developers can override this method to return a custom Sink type depending
        on the value of `stream_name`. Optional when `default_sink_class` is set.

        Args:
            stream_name: Name of the stream.

        Raises:
            ValueError: If no :class:`singer_sdk.sinks.Sink` class is defined.

        Returns:
            The sink class to be used with the stream.
        """

        return MatterbeamHttpSink


if __name__ == "__main__":
    TargetMatterbeamHttp.cli()
