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

from app.maintenance import check_maintenance
from app.models import Alert

ALERT = Alert(
    host_id="gke-cluster1-pool1-abcd1234-xyz0",
    cluster_name="cluster1",
    project_id="test-project",
    location="us-central1",
    alert_type="high_cpu",
    timestamp="2026-08-23T10:00:00.000000",
)


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
