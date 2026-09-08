import datetime
import os

import boto3
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from kubernetes import client as k8s_client
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

import eks_auth
import gcp_auth
import gcp_mcp

CLUSTER_NAME = os.environ.get("CLUSTER_NAME", "")
AWS_REGION = os.environ["AWS_REGION"]
ARTIFACT_BUCKET = os.environ["ARTIFACT_BUCKET"]
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
GKE_CLUSTER_NAME = os.environ.get("GKE_CLUSTER_NAME", "")
GKE_LOCATION = os.environ.get("GKE_LOCATION", "")
GKE_NAMESPACE = os.environ.get("GKE_NAMESPACE", "demo")

app = BedrockAgentCoreApp()


def _core_v1() -> k8s_client.CoreV1Api:
    return k8s_client.CoreV1Api(eks_auth.get_api_client(CLUSTER_NAME, AWS_REGION))


def _apps_v1() -> k8s_client.AppsV1Api:
    return k8s_client.AppsV1Api(eks_auth.get_api_client(CLUSTER_NAME, AWS_REGION))


def _s3():
    return boto3.client("s3", region_name=AWS_REGION)


# ── Read-only tools ───────────────────────────────────────────────────────


@tool
def list_pods(namespace: str = "default") -> str:
    """List pods in a namespace, with status and restart counts."""
    pods = _core_v1().list_namespaced_pod(namespace)
    if not pods.items:
        return f"No pods found in namespace '{namespace}'."
    lines = []
    for pod in pods.items:
        restarts = sum(cs.restart_count for cs in (pod.status.container_statuses or []))
        lines.append(f"{pod.metadata.name}  phase={pod.status.phase}  restarts={restarts}")
    return "\n".join(lines)


@tool
def describe_pod(name: str, namespace: str = "default") -> str:
    """Describe a pod: phase, container statuses, and reasons for any waiting/terminated state."""
    pod = _core_v1().read_namespaced_pod(name, namespace)
    lines = [f"name={pod.metadata.name}  namespace={namespace}  phase={pod.status.phase}"]
    for cs in pod.status.container_statuses or []:
        state = cs.state
        if state.waiting:
            detail = f"waiting reason={state.waiting.reason} message={state.waiting.message}"
        elif state.terminated:
            detail = (
                f"terminated reason={state.terminated.reason} "
                f"exit_code={state.terminated.exit_code} message={state.terminated.message}"
            )
        elif state.running:
            detail = f"running since={state.running.started_at}"
        else:
            detail = "unknown"
        lines.append(f"container={cs.name} restart_count={cs.restart_count} {detail}")
    return "\n".join(lines)


@tool
def get_pod_logs(name: str, namespace: str = "default", tail_lines: int = 100) -> str:
    """Get the recent log output of a pod. Automatically falls back to the previous container's logs if it's currently crash-looping."""
    core = _core_v1()
    try:
        return core.read_namespaced_pod_log(name, namespace, tail_lines=tail_lines)
    except k8s_client.ApiException:
        return core.read_namespaced_pod_log(name, namespace, tail_lines=tail_lines, previous=True)


@tool
def list_events(namespace: str = "default") -> str:
    """List recent Kubernetes events in a namespace (Warning/Normal), most useful for spotting crash loops, OOMs, and scheduling failures."""
    events = _core_v1().list_namespaced_event(namespace)
    if not events.items:
        return f"No events found in namespace '{namespace}'."
    lines = []
    for ev in sorted(events.items, key=lambda e: e.last_timestamp or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc), reverse=True):
        lines.append(
            f"[{ev.type}] {ev.involved_object.kind}/{ev.involved_object.name} "
            f"reason={ev.reason} count={ev.count} message={ev.message}"
        )
    return "\n".join(lines)


@tool
def list_deployments(namespace: str = "default") -> str:
    """List deployments in a namespace with desired vs available replica counts."""
    deployments = _apps_v1().list_namespaced_deployment(namespace)
    if not deployments.items:
        return f"No deployments found in namespace '{namespace}'."
    lines = []
    for d in deployments.items:
        lines.append(
            f"{d.metadata.name}  desired={d.spec.replicas}  "
            f"available={d.status.available_replicas or 0}  ready={d.status.ready_replicas or 0}"
        )
    return "\n".join(lines)


# ── S3 input/output tools ────────────────────────────────────────────────


@tool
def fetch_input_from_s3(key: str) -> str:
    """Download a text object (e.g. an incident ticket) from the shared artifact
    bucket under the given key, and return its contents."""
    obj = _s3().get_object(Bucket=ARTIFACT_BUCKET, Key=key)
    return obj["Body"].read().decode("utf-8")


@tool
def upload_report_to_s3(key: str, report: str) -> str:
    """Upload the final troubleshooting report as text to the shared artifact
    bucket under the given key (e.g. 'reports/2026-08-19-payments-worker.md')."""
    _s3().put_object(Bucket=ARTIFACT_BUCKET, Key=key, Body=report.encode("utf-8"))
    return f"Uploaded report to s3://{ARTIFACT_BUCKET}/{key}"


# ── Cloud Logging MCP (GKE app panics without talking to kube-apiserver) ─


def _since_rfc3339(hours: int = 1) -> str:
    start = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
    return start.strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_gke_filter(namespace: str | None = None, extra: str = "") -> str:
    clauses = [
        'resource.type="k8s_container"',
        f'timestamp>="{_since_rfc3339(1)}"',
    ]
    if GKE_CLUSTER_NAME:
        clauses.append(f'resource.labels.cluster_name="{GKE_CLUSTER_NAME}"')
    if GKE_LOCATION:
        clauses.append(f'resource.labels.location="{GKE_LOCATION}"')
    ns = namespace or GKE_NAMESPACE
    if ns:
        clauses.append(f'resource.labels.namespace_name="{ns}"')
    if extra:
        clauses.append(f"({extra})")
    return " AND ".join(clauses)


@tool
def list_gcp_log_names() -> str:
    """List Cloud Logging log names in the configured GCP project (Logging MCP). Useful to see whether k8s_container / k8s_cluster logs exist."""
    return gcp_mcp.list_log_names(project_id=gcp_auth.gcp_project_id())


@tool
def list_gcp_log_entries(filter: str = "", page_size: int = 20) -> str:
    """Search Cloud Logging via the Logging remote MCP server (https://logging.googleapis.com/mcp). Does not call the Kubernetes API, so GKE authorized networks do not apply.

    `filter` is Logging Query Language. If empty, searches k8s_container logs for the configured GKE cluster/namespace over the last hour. Examples:
    - resource.type="k8s_container" AND resource.labels.namespace_name="demo" AND severity>=ERROR
    - resource.type="k8s_cluster" AND jsonPayload.reason="BackOff"
    Always include a timestamp window with an RFC3339 lower bound so queries stay cheap.
    """
    log_filter = filter.strip() or _default_gke_filter()
    page_size = max(1, min(int(page_size), 50))
    return gcp_mcp.list_log_entries(
        project_id=gcp_auth.gcp_project_id(),
        filter=log_filter,
        page_size=page_size,
    )


# ── Limited-write tools ──────────────────────────────────────────────────


@tool
def restart_deployment(name: str, namespace: str = "default") -> str:
    """Trigger a rolling restart of a deployment (like `kubectl rollout restart`)."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    patch = {"spec": {"template": {"metadata": {"annotations": {"kubectl.kubernetes.io/restartedAt": now}}}}}
    _apps_v1().patch_namespaced_deployment(name, namespace, patch)
    return f"Triggered rolling restart of deployment '{name}' in namespace '{namespace}'."


@tool
def delete_pod(name: str, namespace: str = "default") -> str:
    """Delete a stuck pod so its controller (Deployment/ReplicaSet) recreates it."""
    _core_v1().delete_namespaced_pod(name, namespace)
    return f"Deleted pod '{name}' in namespace '{namespace}'."


EKS_TOOLS = [
    list_pods,
    describe_pod,
    get_pod_logs,
    list_events,
    list_deployments,
    restart_deployment,
    delete_pod,
]
GCP_LOGGING_TOOLS = [list_gcp_log_names, list_gcp_log_entries]
S3_TOOLS = [fetch_input_from_s3, upload_report_to_s3]

TOOLS = list(S3_TOOLS)
if GCP_PROJECT_ID:
    TOOLS = GCP_LOGGING_TOOLS + TOOLS
if CLUSTER_NAME:
    TOOLS = EKS_TOOLS + TOOLS


def _system_message() -> str:
    parts = [
        "You're an SRE assistant. If the user references an incident ticket or "
        "S3 key, fetch it first with fetch_input_from_s3. Quote actual log/event "
        "text as evidence. When done, upload a report with upload_report_to_s3 "
        "under reports/<workload>-<UTC timestamp>.md."
    ]
    if GCP_PROJECT_ID:
        parts.append(
            "GKE investigation is Cloud Logging MCP only (list_gcp_log_names, "
            "list_gcp_log_entries) — you cannot reach the Kubernetes API. "
            f"GCP project={GCP_PROJECT_ID}"
            + (f" cluster={GKE_CLUSTER_NAME}" if GKE_CLUSTER_NAME else "")
            + (f" location={GKE_LOCATION}" if GKE_LOCATION else "")
            + f" default_namespace={GKE_NAMESPACE}. "
            "Use Logging Query Language. Prefer resource.type=\"k8s_container\" "
            "for app panics and resource.type=\"k8s_cluster\" for cluster events. "
            "Always constrain timestamp with an RFC3339 lower bound "
            '(e.g. timestamp>="2026-01-01T00:00:00Z").'
        )
    if CLUSTER_NAME:
        parts.append(
            f"EKS cluster '{CLUSTER_NAME}' is available via Kubernetes API tools. "
            "Prefer read-only investigation before restart_deployment or delete_pod."
        )
    return " ".join(parts)


SYSTEM_MESSAGE = _system_message()


def create_agent():
    from langchain_aws import ChatBedrock

    llm = ChatBedrock(
        model_id="amazon.nova-lite-v1:0",
        model_kwargs={"temperature": 0.1},
    )
    llm_with_tools = llm.bind_tools(TOOLS)

    def chatbot(state: MessagesState):
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_MESSAGE)] + messages
        return {"messages": [llm_with_tools.invoke(messages)]}

    graph_builder = StateGraph(MessagesState)
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", ToolNode(TOOLS))
    graph_builder.add_conditional_edges("chatbot", tools_condition)
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.set_entry_point("chatbot")
    return graph_builder.compile()


agent = create_agent()


@app.entrypoint
def sre_agent(payload):
    user_input = payload.get("prompt")
    response = agent.invoke({"messages": [HumanMessage(content=user_input)]})
    return response["messages"][-1].content


if __name__ == "__main__":
    app.run()
