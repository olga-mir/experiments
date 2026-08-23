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
"""Deterministic maintenance gate — spec.md §4, §5.5.

The workflow's entry node (see app/agent.py): parses the incoming alert,
decides (coin flip placeholder for now) whether the host is under
maintenance, and routes accordingly — "under_maintenance" short-circuits to
a maintenance report, "investigate" continues into the LLM pipeline,
"parse_error" handles a malformed alert. No LLM call here.
"""

import random

from google.adk.events.event import Event
from google.genai import types

from app.models import Alert, MaintenanceCheckResult, MaintenanceWindow


def parse_alert_from_content(content: types.Content | None) -> Alert | None:
    if not content or not content.parts:
        return None
    text = "".join(part.text or "" for part in content.parts)
    try:
        return Alert.model_validate_json(text)
    except Exception:  # malformed input routes to parse_error instead
        return None


def check_maintenance(alert: Alert) -> MaintenanceCheckResult:
    """Coin flip placeholder — replace with a real maintenance-window lookup later.

    The contract (MaintenanceCheckResult / MaintenanceWindow) is what matters
    here; swapping this out for a real data source is a one-function change.
    """
    under_maintenance = random.random() < 0.5  # placeholder, not security-sensitive
    window = (
        MaintenanceWindow(
            host_id=alert.host_id,
            maintenance_start=alert.timestamp,
            maintenance_end=None,
        )
        if under_maintenance
        else None
    )
    return MaintenanceCheckResult(under_maintenance=under_maintenance, window=window)


def maintenance_gate(node_input: types.Content) -> Event:
    """Workflow entry node — see app/agent.py edges for the routing table."""
    alert = parse_alert_from_content(node_input)
    if alert is None:
        return Event(output=None, route="parse_error")

    result = check_maintenance(alert)
    state = {"alert": alert.model_dump(), "maintenance_check": result.model_dump()}
    route = "under_maintenance" if result.under_maintenance else "investigate"
    return Event(output=alert.model_dump(), route=route, state=state)
