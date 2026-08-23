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
"""Unit tests for the k8s-backed tool contracts (app/k8s_tools.py).

Exercises the error path only — no live cluster available in this
environment. Confirms tool failures surface as a typed result with `error`
set (visible to the LLM as a tool result) rather than raising, matching the
contract in spec.md §5.3.
"""

from app import k8s_tools


def test_k8s_node_status_check_returns_error_dict_on_failure(monkeypatch) -> None:
    def _raise(*args, **kwargs):
        raise RuntimeError("cluster unreachable")

    monkeypatch.setattr(k8s_tools.gke_client, "get_core_v1_api", _raise)

    result = k8s_tools.k8s_node_status_check(
        project_id="p", location="us-central1", cluster_name="c", node_name="n"
    )

    assert result["found"] is False
    assert "cluster unreachable" in result["error"]


def test_k8s_pod_status_check_returns_error_dict_on_failure(monkeypatch) -> None:
    def _raise(*args, **kwargs):
        raise RuntimeError("cluster unreachable")

    monkeypatch.setattr(k8s_tools.gke_client, "get_core_v1_api", _raise)

    result = k8s_tools.k8s_pod_status_check(
        project_id="p", location="us-central1", cluster_name="c", node_name="n"
    )

    assert result["pods"] == []
    assert "cluster unreachable" in result["error"]
