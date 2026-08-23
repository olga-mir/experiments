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
"""Alert triage agent — see ../spec.md for the full design.

Pipeline: MaintenanceGate (before_agent_callback, deterministic) -> TriageAgent
(ReAct loop over k8s tools + telemetry sub-agent) -> CategorizerAgent
(structured root-cause classification) -> ReportAssembler (deterministic).
"""

import os
from collections.abc import AsyncGenerator

import google.auth
from google.adk.agents import Agent, BaseAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.apps import App
from google.adk.events import Event
from google.adk.models import Gemini
from google.genai import types

from app.k8s_tools import k8s_node_status_check, k8s_pod_status_check
from app.maintenance import maintenance_gate_callback
from app.models import RootCauseCategorization
from app.telemetry_agent import create_telemetry_agent

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


TRIAGE_AGENT_INSTRUCTION = """\
You are an alert triage agent for GKE-hosted infrastructure. You will
receive an alert as JSON in {alert} with fields: host_id, cluster_name,
project_id, location, alert_type, timestamp, raw_payload.

Investigate the alert using the available tools:
- k8s_node_status_check: node-level conditions (Ready, MemoryPressure,
  DiskPressure, PIDPressure, NetworkUnavailable), capacity, taints.
- k8s_pod_status_check: health and readiness of pods scheduled on the node
  (also your signal for workload connectivity — a pod failing readiness is
  failing to serve traffic).
- telemetry_metrics_analysis_agent (delegate task): CPU/memory utilization
  and heartbeat trends around the alert time.

Use host_id as node_name, and project_id/location/cluster_name from the
alert for every tool call. Investigate as many tools as are relevant to the
alert_type before concluding — do not stop after the first tool call.

When done, write a concise investigation summary covering: what you checked,
what you found, and your recommended next actions. This summary becomes the
"Investigation" section of the final triage report, so write it as a
complete, well-organized account of your findings — not just your final
sentence.
"""

CATEGORIZER_INSTRUCTION = """\
You are a root cause categorizer. Read the investigation findings below and
classify the root cause into one of: hardware, software, network, unknown.
(Do not use "maintenance" — that classification is handled upstream, before
you ever see this alert.)

Investigation findings:
{triage_findings}
"""


def create_root_agent() -> BaseAgent:
    triage_agent = Agent(
        name="triage_agent",
        model=Gemini(
            model="gemini-flash-latest",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction=TRIAGE_AGENT_INSTRUCTION,
        tools=[k8s_node_status_check, k8s_pod_status_check],
        sub_agents=[create_telemetry_agent()],
        output_key="triage_findings",
    )

    categorizer_agent = Agent(
        name="categorizer_agent",
        model=Gemini(
            model="gemini-flash-latest",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction=CATEGORIZER_INSTRUCTION,
        output_schema=RootCauseCategorization,
        output_key="root_cause",
    )

    report_assembler = ReportAssembler(name="report_assembler")

    return SequentialAgent(
        name="alert_triage_pipeline",
        sub_agents=[triage_agent, categorizer_agent, report_assembler],
        before_agent_callback=maintenance_gate_callback,
    )


class ReportAssembler(BaseAgent):
    """Deterministic final step — renders TriageReport contract fields to markdown.

    See spec.md §5.6: TriageReport is the data contract, markdown is a
    rendering concern kept at this one edge, not threaded through the graph.
    """

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        alert = ctx.session.state.get("alert") or {}
        findings = ctx.session.state.get("triage_findings", "")
        root_cause = ctx.session.state.get("root_cause") or {}
        category = root_cause.get("root_cause_category", "unknown")
        reasoning = root_cause.get("root_cause_reasoning", "")

        report = (
            f"# Alert Triage Report — {alert.get('host_id', 'unknown host')}\n\n"
            f"## Investigation\n{findings}\n\n"
            f"## Root Cause Category\n{category}\n\n{reasoning}\n"
        )
        yield Event(
            author=self.name,
            content=types.Content(role="model", parts=[types.Part(text=report)]),
        )


root_agent = create_root_agent()

app = App(
    root_agent=root_agent,
    name="app",
)
