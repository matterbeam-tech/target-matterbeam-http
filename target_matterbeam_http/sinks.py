"""MatterbeamHttp target sink class, which handles writing streams."""

from __future__ import annotations
from datetime import date, datetime

from singer_sdk.sinks import BatchSink, RecordSink

import json
import requests


def json_serial(obj):
    """JSON serializer for objects not serializable by default"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    raise TypeError("Type %s not serializable" % type(obj))


class MatterbeamHttpBatchSink(BatchSink):

    def process_batch(self, context: dict) -> None:
        """Process a batch with the given batch context.

        Args:
            context: Stream partition or context dictionary.
        """

        api_token = self.config.get("api_token")
        base_url = self.config.get("api_url")

        requests.put(
            f"{base_url}/datasets/{self.stream_name}/records",
            json=json.dumps(context["records"], default=json_serial),
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
            json=json.dumps(record, default=json_serial),
            headers={
                "Authorization": f"Token {api_token}",
                "Content-Type": "application/json",
            },
        )
