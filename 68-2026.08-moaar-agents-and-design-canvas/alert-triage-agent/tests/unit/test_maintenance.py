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
"""Unit tests for the deterministic maintenance gate (app/maintenance.py).

No LLM calls here — the gate is plain Python, so it's tested as such
rather than through an eval loop.
"""

import json

from google.genai import types

from app.maintenance import check_maintenance, maintenance_gate
from app.models import Alert

ALERT = Alert(
    host_id="gke-cluster1-pool1-abcd1234-xyz0",
    cluster_name="cluster1",
    project_id="test-project",
    location="us-central1",
    alert_type="high_cpu",
    timestamp="2026-08-23T10:00:00.000000",
)


def _content(text: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part(text=text)])


def test_check_maintenance_under_maintenance(monkeypatch) -> None:
    monkeypatch.setattr("app.maintenance.random.random", lambda: 0.0)

    result = check_maintenance(ALERT)

    assert result.under_maintenance is True
    assert result.window is not None
    assert result.window.host_id == ALERT.host_id
    assert result.window.maintenance_start == ALERT.timestamp
    assert result.window.maintenance_end is None


def test_check_maintenance_not_under_maintenance(monkeypatch) -> None:
    monkeypatch.setattr("app.maintenance.random.random", lambda: 0.99)

    result = check_maintenance(ALERT)

    assert result.under_maintenance is False
    assert result.window is None


def test_maintenance_gate_routes_to_under_maintenance(monkeypatch) -> None:
    monkeypatch.setattr("app.maintenance.random.random", lambda: 0.0)

    event = maintenance_gate(_content(ALERT.model_dump_json()))

    assert event.actions.route == "under_maintenance"
    assert event.output["host_id"] == ALERT.host_id
    assert event.actions.state_delta["maintenance_check"]["under_maintenance"] is True


def test_maintenance_gate_routes_to_investigate(monkeypatch) -> None:
    monkeypatch.setattr("app.maintenance.random.random", lambda: 0.99)

    event = maintenance_gate(_content(ALERT.model_dump_json()))

    assert event.actions.route == "investigate"
    assert event.actions.state_delta["alert"]["host_id"] == ALERT.host_id


def test_maintenance_gate_routes_to_parse_error_on_malformed_input() -> None:
    event = maintenance_gate(_content("not valid json"))

    assert event.actions.route == "parse_error"
    assert event.output is None


def test_maintenance_gate_routes_to_parse_error_on_missing_fields() -> None:
    event = maintenance_gate(_content(json.dumps({"host_id": "n1"})))

    assert event.actions.route == "parse_error"
