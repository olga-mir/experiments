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
"""Typed data contracts for the alert triage agent.

See ../spec.md for the design rationale behind each contract.
"""

from enum import Enum

from pydantic import BaseModel, Field


class Alert(BaseModel):
    """Workflow entrypoint payload — the incoming monitoring alert."""

    host_id: str = Field(description="GKE node name, e.g. gke-cluster1-pool1-abcd1234-xyz0")
    cluster_name: str
    project_id: str
    location: str = Field(description="GKE cluster zone or region")
    alert_type: str = Field(description="e.g. high_cpu, node_not_ready, disk_pressure")
    timestamp: str = Field(description="ISO-8601 UTC timestamp")
    raw_payload: dict | None = None


class GkeTarget(BaseModel):
    """Addressing info for a GKE node — no credentials, see spec.md §5.2."""

    project_id: str
    location: str
    cluster_name: str
    node_name: str


class NodeCondition(BaseModel):
    type: str
    status: str
    reason: str | None = None
    message: str | None = None
    last_transition_time: str | None = None


class NodeStatusResult(BaseModel):
    node_name: str
    found: bool
    conditions: list[NodeCondition] = Field(default_factory=list)
    capacity: dict[str, str] = Field(default_factory=dict)
    allocatable: dict[str, str] = Field(default_factory=dict)
    unschedulable: bool = False
    taints: list[dict] = Field(default_factory=list)
    error: str | None = None


class ContainerStatus(BaseModel):
    name: str
    ready: bool
    restart_count: int
    last_termination_reason: str | None = None


class PodSummary(BaseModel):
    name: str
    namespace: str
    phase: str
    ready: bool
    restart_count: int
    container_statuses: list[ContainerStatus] = Field(default_factory=list)


class PodStatusResult(BaseModel):
    node_name: str
    pods: list[PodSummary] = Field(default_factory=list)
    error: str | None = None


class MetricPoint(BaseModel):
    timestamp: str
    value: float


class NodeMetricsResult(BaseModel):
    node_name: str
    window_start: str
    window_end: str
    cpu_utilization_series: list[MetricPoint] = Field(default_factory=list)
    memory_utilization_series: list[MetricPoint] = Field(default_factory=list)
    error: str | None = None


class HeartbeatResult(BaseModel):
    node_name: str
    last_sample_time: str | None = None
    seconds_since_last_sample: float | None = None
    is_reporting: bool = False
    error: str | None = None


class TelemetryAnalysisResult(BaseModel):
    """Typed output of the telemetry sub-agent — see spec.md §5.4."""

    summary: str
    anomaly_detected: bool
    contributing_metrics: list[str] = Field(default_factory=list)


class MaintenanceWindow(BaseModel):
    host_id: str
    maintenance_start: str
    maintenance_end: str | None = None


class MaintenanceCheckResult(BaseModel):
    under_maintenance: bool
    window: MaintenanceWindow | None = None


class RootCauseCategory(str, Enum):
    HARDWARE = "hardware"
    SOFTWARE = "software"
    NETWORK = "network"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class RootCauseCategorization(BaseModel):
    root_cause_category: RootCauseCategory
    root_cause_reasoning: str


class TriageReport(BaseModel):
    alert: Alert
    under_maintenance: bool
    summary: str
    findings: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    root_cause_category: RootCauseCategory
    root_cause_reasoning: str
