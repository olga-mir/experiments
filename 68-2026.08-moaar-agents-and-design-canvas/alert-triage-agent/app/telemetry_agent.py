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
"""Telemetry analysis sub-agent — spec.md §4, §5.4.

Wraps gcp_node_metrics_check / gcp_heartbeat_check behind an LLM that
reasons over both series and returns a typed conclusion. Uses ADK 2.0 task
delegation (mode="task") rather than a plain AgentTool wrap, because it's
the one boundary in this system that needs BOTH tool calling and a typed
final result — output_schema alone disables tool calling, and a plain
AgentTool only returns free text.
"""

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from app.models import TelemetryAnalysisResult
from app.monitoring_tools import gcp_heartbeat_check, gcp_node_metrics_check

TELEMETRY_AGENT_INSTRUCTION = """\
You are a telemetry analysis specialist for GKE nodes. Given a project ID,
node name, and alert time, use the available tools to fetch CPU/memory
utilization and heartbeat data for a 30-minute window ending at the alert
time, then determine whether the data shows an anomaly relevant to the
alert.

Call gcp_node_metrics_check and gcp_heartbeat_check (you may call both in
parallel). Base your conclusion only on the data returned by the tools —
do not speculate beyond it. When you have enough information, call
finish_task with your structured conclusion.
"""


def create_telemetry_agent() -> Agent:
    return Agent(
        name="telemetry_metrics_analysis_agent",
        model=Gemini(
            model="gemini-flash-latest",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction=TELEMETRY_AGENT_INSTRUCTION,
        description=(
            "Analyzes GKE node CPU/memory utilization and heartbeat telemetry "
            "for a given node and alert time; returns a structured anomaly finding."
        ),
        mode="task",
        output_schema=TelemetryAnalysisResult,
        tools=[gcp_node_metrics_check, gcp_heartbeat_check],
    )
