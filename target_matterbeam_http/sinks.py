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

        print("Processing record: {}".format(record))

        api_token = self.config.get("api_token")
        dataset_name = self.config.get("dataset_name")

        response = requests.put(
            f"https://dev-api.matterbeam.com/datasets/{dataset_name}/record",
            json=record,
            headers={
                "Authorization": f"Token {api_token}",
                "Content-Type": "application/json",
            },
        )

        print(response.text)
