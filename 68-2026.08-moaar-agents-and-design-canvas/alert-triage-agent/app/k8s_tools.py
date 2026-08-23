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
"""Diagnostic tools backed by the Kubernetes API (spec.md §3, §5.3)."""

from app import gke_client
from app.models import (
    ContainerStatus,
    NodeCondition,
    NodeStatusResult,
    PodStatusResult,
    PodSummary,
)


def k8s_node_status_check(
    project_id: str, location: str, cluster_name: str, node_name: str
) -> dict:
    """Checks a GKE node's Ready/MemoryPressure/DiskPressure conditions and capacity.

    Replaces the hardware/IPMI check and the node-level part of the host
    performance check from the original design — GKE nodes are managed VMs
    with no IPMI access, but node conditions surface the same class of
    hardware/resource-pressure signals via the Kubernetes API instead.

    Args:
        project_id: GCP project ID that owns the GKE cluster.
        location: GKE cluster zone or region.
        cluster_name: GKE cluster name.
        node_name: Name of the node to check.

    Returns:
        dict with node conditions, capacity, allocatable resources, and taints.
    """
    try:
        core_v1 = gke_client.get_core_v1_api(project_id, location, cluster_name)
        node = core_v1.read_node(node_name)
    except Exception as e:
        return NodeStatusResult(node_name=node_name, found=False, error=str(e)).model_dump()

    conditions = [
        NodeCondition(
            type=c.type,
            status=c.status,
            reason=c.reason,
            message=c.message,
            last_transition_time=(
                c.last_transition_time.isoformat() if c.last_transition_time else None
            ),
        )
        for c in (node.status.conditions or [])
    ]

    result = NodeStatusResult(
        node_name=node_name,
        found=True,
        conditions=conditions,
        capacity=dict(node.status.capacity or {}),
        allocatable=dict(node.status.allocatable or {}),
        unschedulable=bool(node.spec.unschedulable),
        taints=[t.to_dict() for t in (node.spec.taints or [])],
    )
    return result.model_dump()


def k8s_pod_status_check(
    project_id: str, location: str, cluster_name: str, node_name: str
) -> dict:
    """Checks the health of pods scheduled on a GKE node.

    Replaces the SSH-based monitoring-process check and, for v1, also stands
    in for workload-to-workload connectivity checks: a pod that is not
    reporting Ready is by definition failing to serve traffic, which is the
    same signal a ping/telnet-style connectivity probe would be used for.
    See spec.md §3 for why a dedicated connectivity tool was deferred instead
    of stubbed.

    Args:
        project_id: GCP project ID that owns the GKE cluster.
        location: GKE cluster zone or region.
        cluster_name: GKE cluster name.
        node_name: Name of the node to check pods on.

    Returns:
        dict with per-pod phase, readiness, restart counts, and container statuses.
    """
    try:
        core_v1 = gke_client.get_core_v1_api(project_id, location, cluster_name)
        pods = core_v1.list_pod_for_all_namespaces(
            field_selector=f"spec.nodeName={node_name}"
        )
    except Exception as e:
        return PodStatusResult(node_name=node_name, error=str(e)).model_dump()

    summaries = []
    for pod in pods.items:
        ready = any(
            c.type == "Ready" and c.status == "True"
            for c in (pod.status.conditions or [])
        )
        container_statuses = [
            ContainerStatus(
                name=cs.name,
                ready=cs.ready,
                restart_count=cs.restart_count,
                last_termination_reason=(
                    cs.last_state.terminated.reason
                    if cs.last_state and cs.last_state.terminated
                    else None
                ),
            )
            for cs in (pod.status.container_statuses or [])
        ]
        summaries.append(
            PodSummary(
                name=pod.metadata.name,
                namespace=pod.metadata.namespace,
                phase=pod.status.phase or "Unknown",
                ready=ready,
                restart_count=sum(cs.restart_count for cs in container_statuses),
                container_statuses=container_statuses,
            )
        )

    return PodStatusResult(node_name=node_name, pods=summaries).model_dump()
