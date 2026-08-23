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

Runs as a before_agent_callback on the root pipeline: parses the incoming
alert, decides (coin flip placeholder for now) whether the host is under
maintenance, and if so short-circuits the whole pipeline by returning
Content directly instead of letting the LLM agents run at all.
"""

import random

from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from app.models import Alert, MaintenanceCheckResult, MaintenanceWindow


def _parse_alert(callback_context: CallbackContext) -> Alert | None:
    content = callback_context.user_content
    if not content or not content.parts:
        return None
    text = "".join(part.text or "" for part in content.parts)
    try:
        return Alert.model_validate_json(text)
    except Exception:
        return None


def check_maintenance(alert: Alert) -> MaintenanceCheckResult:
    """Coin flip placeholder — replace with a real maintenance-window lookup later.

    The contract (MaintenanceCheckResult / MaintenanceWindow) is what matters
    here; swapping this out for a real data source is a one-function change.
    """
    under_maintenance = random.random() < 0.5
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


async def maintenance_gate_callback(callback_context: CallbackContext) -> types.Content | None:
    alert = _parse_alert(callback_context)
    if alert is None:
        # No parseable alert — let the pipeline run and the agent surface the error.
        return None

    callback_context.state["alert"] = alert.model_dump()

    result = check_maintenance(alert)
    callback_context.state["maintenance_check"] = result.model_dump()

    if not result.under_maintenance:
        return None

    report = (
        f"# Alert Triage Report — {alert.host_id}\n\n"
        f"## Maintenance Status\n"
        f"Host `{alert.host_id}` is under maintenance "
        f"(window started {result.window.maintenance_start}, "
        f"{'ongoing' if not result.window.maintenance_end else f'ends {result.window.maintenance_end}'}). "
        f"No further investigation was performed.\n\n"
        f"## Root Cause Category\nmaintenance\n"
    )
    return types.Content(role="model", parts=[types.Part(text=report)])
