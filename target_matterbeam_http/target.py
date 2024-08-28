"""MatterbeamHttp target class."""

from __future__ import annotations

from singer_sdk import typing as th
from singer_sdk.target_base import Target

from target_matterbeam_http.sinks import (
    MatterbeamHttpSink,
)


class TargetMatterbeamHttp(Target):
    """Sample target for MatterbeamHttp."""

    name = "target-matterbeam-http"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "api_token",
            th.StringType,
            secret=True,
        ),
        th.Property(
            "dataset_name",
            th.StringType,
        ),
    ).to_dict()

    default_sink_class = MatterbeamHttpSink


if __name__ == "__main__":
    TargetMatterbeamHttp.cli()
