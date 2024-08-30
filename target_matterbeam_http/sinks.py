"""MatterbeamHttp target sink class, which handles writing streams."""

from __future__ import annotations
from typing import Sequence
from singer_sdk import Target
from singer_sdk.sinks import RecordSink

import requests


class MatterbeamHttpSink(RecordSink):
    """MatterbeamHttp target sink class."""

    def process_record(self, record: dict, context: dict) -> None:
        """Process the record.

        Args:
            record: Individual record in the stream.
            context: Stream partition or context dictionary.
        """

        api_token = self.config.get("api_token")
        base_url = self.config.get("api_url")

        response = requests.put(
            f"{base_url}/datasets/{self.stream_name}/record",
            json=record,
            headers={
                "Authorization": f"Token {api_token}",
                "Content-Type": "application/json",
            },
        )

        print(response.text)
