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

Built on ADK's graph-based Workflow API (google.adk.workflow), not the
deprecated SequentialAgent — this migration is itself part of the exercise
(the original NeMo/LangGraph source is an explicit state graph; ADK's
Workflow is the idiomatic equivalent, vs. SequentialAgent's implicit linear
chaining).

Graph:

    START -> maintenance_gate --[under_maintenance]--> maintenance_report
                    |          --[parse_error]-------> parse_error_report
                    |
                    +--[investigate]--> triage_agent -> categorizer_agent -> report_assembler

maintenance_gate is a deterministic FunctionNode (see app/maintenance.py).
triage_agent is an LlmAgent (ReAct loop over k8s tools + the telemetry
sub-agent). categorizer_agent is an LlmAgent with output_schema for
structured root-cause classification. report_assembler is a deterministic
FunctionNode that renders the final markdown report.
"""

import os

import google.auth
from google.adk.agents import Agent
from google.adk.agents.context import Context
from google.adk.apps import App
from google.adk.events.event import Event
from google.adk.models import Gemini
from google.adk.workflow import Workflow
from google.genai import types

from app.k8s_tools import k8s_node_status_check, k8s_pod_status_check
from app.maintenance import maintenance_gate
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


def create_triage_agent() -> Agent:
    return Agent(
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


def create_categorizer_agent() -> Agent:
    return Agent(
        name="categorizer_agent",
        model=Gemini(
            model="gemini-flash-latest",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction=CATEGORIZER_INSTRUCTION,
        output_schema=RootCauseCategorization,
        output_key="root_cause",
    )


def maintenance_report(ctx: Context, node_input: dict) -> Event:
    """Renders the short-circuit report when maintenance_gate routes here."""
    alert = node_input or {}
    maintenance_check = ctx.state.get("maintenance_check") or {}
    window = maintenance_check.get("window") or {}
    maintenance_end = window.get("maintenance_end")
    window_status = "ongoing" if not maintenance_end else f"ends {maintenance_end}"

    report = (
        f"# Alert Triage Report — {alert.get('host_id', 'unknown host')}\n\n"
        f"## Maintenance Status\n"
        f"Host `{alert.get('host_id', 'unknown host')}` is under maintenance "
        f"(window started {window.get('maintenance_start', 'unknown')}, {window_status}). "
        f"No further investigation was performed.\n\n"
        f"## Root Cause Category\nmaintenance\n"
    )
    return Event(
        output=report,
        content=types.Content(role="model", parts=[types.Part(text=report)]),
    )


def parse_error_report(node_input: None) -> Event:
    """Renders the short-circuit report when maintenance_gate can't parse the alert."""
    report = (
        "# Alert Triage Report\n\n"
        "Could not parse the incoming message as a valid alert (expected JSON "
        "matching the Alert schema — see app/models.py). No investigation was "
        "performed.\n"
    )
    return Event(
        output=report,
        content=types.Content(role="model", parts=[types.Part(text=report)]),
    )


def report_assembler(ctx: Context, node_input: dict) -> Event:
    """Deterministic final step — renders TriageReport contract fields to markdown.

    See spec.md §5.6: TriageReport is the data contract, markdown is a
    rendering concern kept at this one edge, not threaded through the graph.
    node_input is categorizer_agent's structured output_schema dict
    (RootCauseCategorization), per the Workflow node_input-type rule for an
    LlmAgent predecessor that sets output_schema.
    """
    alert = ctx.state.get("alert") or {}
    findings = ctx.state.get("triage_findings", "")
    category = node_input.get("root_cause_category", "unknown")
    reasoning = node_input.get("root_cause_reasoning", "")

    report = (
        f"# Alert Triage Report — {alert.get('host_id', 'unknown host')}\n\n"
        f"## Investigation\n{findings}\n\n"
        f"## Root Cause Category\n{category}\n\n{reasoning}\n"
    )
    return Event(
        output=report,
        content=types.Content(role="model", parts=[types.Part(text=report)]),
    )


def create_root_agent() -> Workflow:
    triage_agent = create_triage_agent()
    categorizer_agent = create_categorizer_agent()

    return Workflow(
        name="alert_triage_pipeline",
        edges=[
            ("START", maintenance_gate),
            (
                maintenance_gate,
                {
                    "investigate": triage_agent,
                    "under_maintenance": maintenance_report,
                    "parse_error": parse_error_report,
                },
            ),
            (triage_agent, categorizer_agent),
            (categorizer_agent, report_assembler),
        ],
    )


root_agent = create_root_agent()

app = App(
    root_agent=root_agent,
    name="app",
)
