# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Diagnostic tools backed by GCP Cloud Monitoring (spec.md §3, §5.3).

Used by the telemetry sub-agent (app/telemetry_agent.py), not called
directly by the top-level triage agent.
"""

from datetime import UTC, datetime, timedelta

from google.cloud import monitoring_v3

from app.models import HeartbeatResult, MetricPoint, NodeMetricsResult

_LOOKBACK = timedelta(minutes=30)


def _time_interval(alert_time: str) -> monitoring_v3.TimeInterval:
    end = datetime.fromisoformat(alert_time.replace("Z", "+00:00"))
    start = end - _LOOKBACK
    interval = monitoring_v3.TimeInterval()
    interval.end_time.FromDatetime(end.astimezone(UTC))
    interval.start_time.FromDatetime(start.astimezone(UTC))
    return interval, start, end


def _query_series(
    client: monitoring_v3.MetricServiceClient,
    project_id: str,
    metric_type: str,
    node_name: str,
    interval: monitoring_v3.TimeInterval,
) -> list[MetricPoint]:
    results = client.list_time_series(
        request={
            "name": f"projects/{project_id}",
            "filter": (
                f'metric.type = "{metric_type}" AND '
                f'resource.labels.node_name = "{node_name}"'
            ),
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        }
    )
    points = []
    for series in results:
        for point in series.points:
            points.append(
                MetricPoint(
                    timestamp=point.interval.end_time.ToDatetime().isoformat(),
                    value=point.value.double_value or point.value.int64_value,
                )
            )
    return sorted(points, key=lambda p: p.timestamp)


def gcp_node_metrics_check(project_id: str, node_name: str, alert_time: str) -> dict:
    """Fetches GKE node CPU and memory utilization around the alert time.

    Args:
        project_id: GCP project ID hosting the Cloud Monitoring metrics.
        node_name: Name of the GKE node to fetch metrics for.
        alert_time: ISO-8601 UTC timestamp the alert fired at; metrics are
            fetched for a 30-minute window ending at this time.

    Returns:
        dict with CPU and memory utilization time series for the window.
    """
    try:
        interval, start, end = _time_interval(alert_time)
        client = monitoring_v3.MetricServiceClient()
        cpu_series = _query_series(
            client, project_id, "kubernetes.io/node/cpu/allocatable_utilization", node_name, interval
        )
        mem_series = _query_series(
            client,
            project_id,
            "kubernetes.io/node/memory/allocatable_utilization",
            node_name,
            interval,
        )
    except Exception as e:
        return NodeMetricsResult(
            node_name=node_name, window_start="", window_end="", error=str(e)
        ).model_dump()

    return NodeMetricsResult(
        node_name=node_name,
        window_start=start.isoformat(),
        window_end=end.isoformat(),
        cpu_utilization_series=cpu_series,
        memory_utilization_series=mem_series,
    ).model_dump()


def gcp_heartbeat_check(project_id: str, node_name: str, alert_time: str) -> dict:
    """Checks how recently a GKE node last reported telemetry, as a liveness proxy.

    Args:
        project_id: GCP project ID hosting the Cloud Monitoring metrics.
        node_name: Name of the GKE node to check.
        alert_time: ISO-8601 UTC timestamp the alert fired at.

    Returns:
        dict with the last sample time and whether the node is currently reporting.
    """
    try:
        interval, _, end = _time_interval(alert_time)
        client = monitoring_v3.MetricServiceClient()
        series = _query_series(
            client, project_id, "kubernetes.io/node/cpu/allocatable_utilization", node_name, interval
        )
    except Exception as e:
        return HeartbeatResult(node_name=node_name, error=str(e)).model_dump()

    if not series:
        return HeartbeatResult(node_name=node_name, is_reporting=False).model_dump()

    last_sample = datetime.fromisoformat(series[-1].timestamp)
    seconds_since = (end.astimezone(UTC) - last_sample.astimezone(UTC)).total_seconds()

    return HeartbeatResult(
        node_name=node_name,
        last_sample_time=series[-1].timestamp,
        seconds_since_last_sample=seconds_since,
        is_reporting=seconds_since < 300,
    ).model_dump()
