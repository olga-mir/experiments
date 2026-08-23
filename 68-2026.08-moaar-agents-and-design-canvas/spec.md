# Alert Triage Agent — ADK / GKE port — Spec

Source of truth for architecture: [`NVIDIA/NeMo-Agent-Toolkit`](https://github.com/NVIDIA/NeMo-Agent-Toolkit), `examples/advanced_agents/alert_triage_agent`
ADK reference: [`google/adk-python`](https://github.com/google/adk-python), [`google/adk-docs`](https://github.com/google/adk-docs)

If you have local clones of these repos, tell the assistant the paths so it can verify claims in this spec against the actual source.

## 1. Decisions (from mission scoping)

1. No SSH/Ansible/IPMI to bare hosts. The target infra is **GKE clusters** — `cluster_name` and `project_id` are provided as input. Diagnostic tools call the **Kubernetes API** (via `google-cloud-container` for cluster metadata + the `kubernetes` python client for the API server, authenticated via Workload Identity Federation — see §5.2) instead of Ansible playbooks or raw sockets.
2. Monitoring source is **GCP Cloud Monitoring** (Cloud Monitoring API / `google-cloud-monitoring`), replacing the NeMo example's CSV-backed offline telemetry and Ansible-collected `top`/`ps` output.
3. **Tool count reduced initially**; the rest stubbed (return a fixed "not implemented" / synthetic response) but present in the graph so the orchestration shape is faithful. See §3 for which.
4. Deployment target is **Agent Engine only** (Agent Platform), via `agents-cli` (needs upgrading — flagged as a pre-req, not part of this spec). No Gemini Enterprise publish step.
5. Root-cause categorization evaluator (NeMo's `classification_evaluator.py`) is **deferred**, not ported.
6. Primary design focus of this spec: **data and API contracts** between the orchestrator agent, sub-agent, and tool nodes — not prompt content or infra provisioning details.

## 2. Source → target mapping

| NeMo component | Mechanism | ADK target | Mechanism |
|---|---|---|---|
| `alert_triage_agent_workflow` (`register.py`) | LangGraph `StateGraph` + `ToolNode`, manual ReAct loop | `TriageAgent` | `LlmAgent` with `tools=[...]`, ADK's built-in function-calling loop |
| `maintenance_check` | Pre-graph gate, short-circuits before agent runs | `MaintenanceGate` | Deterministic `FunctionNode` (`maintenance_gate`), the workflow's entry node — routes on `investigate` / `under_maintenance` / `parse_error`, no LLM call. Minimal build backs the decision with a **coin flip** placeholder (see §5.5) rather than a real maintenance-window lookup, to be replaced once a real maintenance data source is chosen |
| `telemetry_metrics_analysis_agent` | Nested LangGraph `StateGraph` exposed as a callable tool | `TelemetryAgent` | ADK sub-agent wrapped via `AgentTool` — matches the "agent as tool" pattern natively |
| `host_performance_check_tool`, `hardware_check_tool`, `monitoring_process_check_tool`, `network_connectivity_check_tool`, `telemetry_metrics_host_performance_check_tool`, `telemetry_metrics_host_heartbeat_check_tool` | `FunctionInfo.from_fn`, each: fetch raw data → LLM-summarize → return `str` | ADK `FunctionTool`s | See §3/§5 — reduced set backed by k8s API / Cloud Monitoring, typed return, no per-tool LLM summarization pass (LLM reasoning happens once, at the orchestrator) |
| `categorizer_tool` | LLM classification appended as a markdown section | `categorize_root_cause` | `FunctionTool` or final `output_schema`-typed field on `TriageAgent`'s last turn |
| Final `_process_alert` return (markdown string) | string concatenation | `TriageReport` | typed Pydantic model, rendered to markdown at the edge (see §5.5) |

**Key architectural shift:** the NeMo tools each do their own LLM call to "interpret" raw output before returning to the orchestrator (so the orchestrator LLM never sees raw `top`/`ping` text). This spec drops that per-tool LLM pass for the reduced build — tools return **typed structured data**, and the one orchestrator LLM turn does the reasoning. This is both simpler and gives the "data contracts between agent and nodes" the sharp edges the mission asked to focus on. Re-adding a per-tool summarization LLM call later is additive, not a rework, if raw payloads turn out too large for the orchestrator's context.

## 3. Tool scope for the minimal build

Reduce to tools that map cleanly onto GKE/k8s API + Cloud Monitoring with no invented data:

**Implemented (minimal set):**
- `k8s_node_status_check` — replaces `hardware_check_tool` (IPMI) + part of `host_performance_check_tool`. Reads `Node` object: conditions (Ready/MemoryPressure/DiskPressure/PIDPressure/NetworkUnavailable), allocatable vs capacity, taints.
- `k8s_pod_status_check` — replaces `monitoring_process_check_tool` (was: is the monitoring agent process running) **and** `network_connectivity_check_tool` for v1. Reads Pod phase/restarts/container statuses and `Ready`/`ContainersReady` conditions on the affected node — pod health (including readiness, which is itself a workload-level connectivity signal: a pod that fails its readiness probe is by definition failing to serve traffic) is the starting point rather than a synthetic ping/telnet or Service/Endpoints reachability probe. Optionally filtered to a monitoring DaemonSet (e.g. `gke-metadata-server`, `node-exporter`, or user-specified).
- `gcp_node_metrics_check` — replaces `telemetry_metrics_host_performance_check_tool`. Queries Cloud Monitoring for `kubernetes.io/node/cpu/allocatable_utilization`, memory utilization, over a time window around the alert timestamp.
- `gcp_heartbeat_check` — replaces `telemetry_metrics_host_heartbeat_check_tool`. Queries Cloud Monitoring for node up/down or last-sample-age on core node metrics as a liveness proxy.
- `maintenance_check` — kept as a gate in the graph, but its decision logic is a **coin flip placeholder** for the minimal build (see §5.5), not a real maintenance-window lookup.

**Deferred (not in the graph at all for v1 — no stub node):**
- **Workload-to-workload connectivity** (Service/Endpoints reachability, cross-namespace network policy checks, actual ping/telnet-equivalent probes) — `k8s_pod_status_check`'s readiness signal is the v1 proxy; a dedicated connectivity tool is future work once it's clear pod health alone under- or over-reports real connectivity issues.
- Anything IPMI-specific beyond what `k8s_node_status_check` covers (out-of-band hardware sensors — not exposed via k8s API at all; permanently out of scope unless a specific need shows up).

**Deferred:** the `telemetry_metrics_analysis_agent` sub-agent is **kept** (not stubbed) since it's the one component that exercises ADK's sub-agent-as-tool / task-delegation pattern — it wraps `gcp_node_metrics_check` + `gcp_heartbeat_check`. (Note: "design canvas," the second half of this experiment's folder name, is a separate feature to be built alongside this agent in a later step — not part of this agent's design.)

## 4. Orchestration graph

Built on ADK's graph-based `Workflow` API (`google.adk.workflow`), not `SequentialAgent`. `SequentialAgent` was the first pass and is deprecated in this ADK version in favor of `Workflow` — moving to the real graph engine (explicit nodes, edges, and routed conditionals) is itself part of the exercise, since the NeMo source is an explicit `LangGraph` `StateGraph` and `Workflow` is ADK's idiomatic equivalent, unlike `SequentialAgent`'s implicit linear chaining.

```
START ──▶ maintenance_gate ──[investigate]──▶ triage_agent ──▶ categorizer_agent ──▶ report_assembler
               │        │                          │  tools:
               │        │                          │   - k8s_node_status_check
               │        │                          │   - k8s_pod_status_check (also v1 connectivity/health proxy)
               │        │                          │   - telemetry_metrics_analysis_agent (task delegation) ──▶ LlmAgent
               │        │                                                                       tools:
               │        │                                                                        - gcp_node_metrics_check
               │        │                                                                        - gcp_heartbeat_check
               │        └──[under_maintenance]──▶ maintenance_report
               └──[parse_error]──▶ parse_error_report
```

`maintenance_gate` is a deterministic `FunctionNode` (app/maintenance.py) — no LLM call, no reasoning needed — that parses the incoming alert and routes on three explicit conditions: `investigate` (continue into the LLM pipeline), `under_maintenance` (short-circuit to a maintenance report — decision is the coin-flip placeholder, §5.5), and `parse_error` (malformed alert, short-circuit to an error report). `triage_agent` and `categorizer_agent` are `LlmAgent`s used directly as workflow nodes (auto-wrapped). `report_assembler` is a deterministic `FunctionNode` that renders `TriageReport`'s fields to markdown (§5.6) — the ADK 2.0 workflow docs' "node_input type by predecessor" table governs each edge here: `categorizer_agent` sets `output_schema`, so `report_assembler` receives a `dict`, not `types.Content`.

Root cause categorization runs as a separate node after the triage ReAct loop ends, mirroring NeMo's `_process_alert` (agent loop, then `categorizer_tool.arun(result)`) — just expressed as a graph edge instead of a second function call in Python.

## 5. Data & API contracts

All models are Pydantic `BaseModel`s (ADK-native — `LlmAgent.output_schema` and `FunctionTool` both consume Pydantic).

### 5.1 Alert input (workflow entrypoint)

```python
class Alert(BaseModel):
    host_id: str            # GKE node name, e.g. "gke-cluster1-pool1-abcd1234-xyz0"
    cluster_name: str
    project_id: str
    location: str            # zone or region, needed for GKE/Monitoring API calls
    alert_type: str          # e.g. "high_cpu", "node_not_ready", "disk_pressure"
    timestamp: str            # ISO-8601, UTC
    raw_payload: dict | None = None   # passthrough for whatever the source monitoring system sent
```

Replaces NeMo's loosely-parsed `input_message: str` containing embedded JSON (`_parse_alert_data` regex-extracts `{...}` from a free-text string) — that's a legacy of the CLI-invocation demo, not worth preserving. ADK entrypoint takes `Alert` directly (or a `state["alert"]` set once at session start).

### 5.2 GKE/k8s context shared by all k8s-backed tools

```python
class GkeTarget(BaseModel):
    project_id: str
    location: str
    cluster_name: str
    node_name: str
```

Every k8s tool takes a `GkeTarget`, not a bare `host_id` string (NeMo's tools take `host_id: str` alone because Ansible connection details were hardcoded placeholders in the source — that shortcut doesn't survive contact with real multi-cluster GKE).

**Auth model:** the phrase "GKE-fetched credentials" from the mission discussion is directionally right but worth being precise about, since GEAP handles this differently from a local kubeconfig. There's no kubeconfig file and no per-tool credential fetch step. The Agent Engine runtime executes as a **GCP service account identity** (the agent's runtime SA). Two authorization layers apply, both keyed off that one identity:
- **IAM** grants the runtime SA the GKE-level permissions to reach the cluster at all (e.g. `container.clusters.get` to resolve the cluster endpoint/CA cert, typically via `roles/container.viewer` or narrower).
- **Kubernetes RBAC**, bound to that same SA (via GKE Workload Identity Federation mapping the GSA to a `Role`/`ClusterRole` inside the cluster), governs what the SA can actually read once it's talking to the API server — e.g. `get`/`list` on `nodes` and `pods`, nothing else.
The `kubernetes` python client obtains a short-lived bearer token for the runtime SA via `google.auth` and presents it to the cluster's API server; it does not need a separately "fetched" credential file. Net effect for this spec: **no credential-plumbing code is a tool-contract concern** — `GkeTarget` only carries addressing info (project/location/cluster/node), not secrets. The actual IAM role grants and RBAC bindings are a deployment-time prerequisite, out of scope for this doc (§7), but the *shape* of the auth (one identity, two authorization layers) is worth keeping in mind when writing the tool implementations so they don't assume a kubeconfig-style credential object exists.

### 5.3 Tool contracts (minimal set)

```python
class NodeCondition(BaseModel):
    type: str            # "Ready" | "MemoryPressure" | "DiskPressure" | "PIDPressure" | "NetworkUnavailable"
    status: str           # "True" | "False" | "Unknown"
    reason: str | None
    message: str | None
    last_transition_time: str

class NodeStatusResult(BaseModel):
    node_name: str
    conditions: list[NodeCondition]
    capacity: dict[str, str]
    allocatable: dict[str, str]
    unschedulable: bool
    taints: list[dict]

class PodSummary(BaseModel):
    name: str
    namespace: str
    phase: str                     # "Running" | "Pending" | "Failed" | "Succeeded" | "Unknown"
    ready: bool                    # from the Pod's "Ready" condition — v1 connectivity/health proxy
    restart_count: int
    container_statuses: list[dict]  # name, ready, restart_count, last_termination_reason

class PodStatusResult(BaseModel):
    node_name: str
    pods: list[PodSummary]

class NodeMetricsResult(BaseModel):
    node_name: str
    window_start: str
    window_end: str
    cpu_utilization_series: list[MetricPoint]     # MetricPoint: timestamp, value
    memory_utilization_series: list[MetricPoint]

class HeartbeatResult(BaseModel):
    node_name: str
    last_sample_time: str | None
    seconds_since_last_sample: float | None
    is_reporting: bool

```

Each tool function signature: `async def <tool>(target: GkeTarget, alert_time: str) -> <Result model>`. ADK serializes Pydantic returns to the LLM as JSON automatically — no manual `json.dumps` needed (unlike NeMo's raw-string returns).

### 5.4 Sub-agent contract (`TelemetryAgent` via `AgentTool`)

Input (matches NeMo's `_arun(host_id: str, alert_type: str)` signature, extended for multi-cluster):
```python
class TelemetryAnalysisRequest(BaseModel):
    target: GkeTarget
    alert_type: str
    alert_time: str
```
Output — the sub-agent's final turn, typed via `output_schema` rather than NeMo's free-text `conclusion`:
```python
class TelemetryAnalysisResult(BaseModel):
    summary: str                    # natural-language conclusion, still needed for the report
    anomaly_detected: bool
    contributing_metrics: list[str]  # which series (cpu/memory/heartbeat) drove the conclusion
```
`AgentTool` wraps `TelemetryAgent`; the parent `TriageAgent` calls it like any other tool and receives `TelemetryAnalysisResult` as structured JSON — this is the one contract boundary in the whole system that crosses an LLM-to-LLM (agent-to-agent) call rather than agent-to-deterministic-tool, worth flagging explicitly as the highest-value place for schema discipline since a bad contract here means the parent has to *guess* what the child's prose means.

### 5.5 Maintenance check contract

```python
class MaintenanceWindow(BaseModel):
    host_id: str
    maintenance_start: str
    maintenance_end: str | None    # None == ongoing, open-ended

class MaintenanceCheckResult(BaseModel):
    under_maintenance: bool
    window: MaintenanceWindow | None
```
Deterministic (no LLM), matching NeMo's `_get_active_maintenance` in spirit, but for the minimal build the lookup itself is a **coin flip placeholder**:

```python
def check_maintenance(alert: Alert) -> MaintenanceCheckResult:
    under_maintenance = random.random() < 0.5   # placeholder — replace with real lookup later
    window = (MaintenanceWindow(host_id=alert.host_id,
                                 maintenance_start=alert.timestamp,
                                 maintenance_end=None)
              if under_maintenance else None)
    return MaintenanceCheckResult(under_maintenance=under_maintenance, window=window)
```

The `MaintenanceCheckResult`/`MaintenanceWindow` contract itself is unaffected by this — swapping the coin flip for a real maintenance-window data source (CSV, DB, ticketing API) later is a one-function change behind the same typed return, not a graph or contract change.

### 5.6 Final output contract

```python
class RootCauseCategory(str, Enum):
    HARDWARE = "hardware"
    SOFTWARE = "software"
    NETWORK = "network"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"

class TriageReport(BaseModel):
    alert: Alert
    under_maintenance: bool
    summary: str
    findings: list[str]              # one entry per tool/sub-agent invoked, human-readable
    recommended_actions: list[str]
    root_cause_category: RootCauseCategory
    root_cause_reasoning: str
```
NeMo returns a hand-assembled markdown string (agent's last message + categorizer's appended section, matched by regex-detected heading level). This spec keeps `TriageReport` as the structured contract and treats markdown as a rendering concern at the API/UI edge, not the data contract — cleaner boundary, and markdown rendering is a one-line `template.render(report)` away if a chat-style output is still wanted for GEAP's UI.

## 6. Open questions (not blocking, but unresolved)

- Where `alert_type` taxonomy comes from for the minimal build (NeMo's is implicit in prompt engineering + offline CSV columns) — needs a small fixed enum before tool routing can be alert-type-aware.
- Whether a prose maintenance report (matching NeMo's LLM-summarized version) is needed for GEAP's chat surface, or `MaintenanceCheckResult` as structured JSON is enough for v1. Leaning toward structured-only for now, consistent with dropping per-tool LLM summarization elsewhere.
- Whether `k8s_pod_status_check`'s readiness signal turns out to be a good-enough connectivity proxy in practice, or a dedicated workload-to-workload connectivity tool becomes necessary once real alerts are tested against it (see §3, deferred).

## 7. Explicitly out of scope for this spec

- `agents-cli` upgrade steps (separate pre-req, tracked outside this doc)
- Actual GKE/Cloud Monitoring credential and IAM setup
- Prompt content for `TriageAgent` / `TelemetryAgent` system instructions
- Eval harness / `classification_evaluator` port
- Gemini Enterprise publish step
