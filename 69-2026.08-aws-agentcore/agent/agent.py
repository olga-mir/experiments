import datetime
import os

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from kubernetes import client as k8s_client
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

import eks_auth

CLUSTER_NAME = os.environ["CLUSTER_NAME"]
AWS_REGION = os.environ["AWS_REGION"]

app = BedrockAgentCoreApp()


def _core_v1() -> k8s_client.CoreV1Api:
    return k8s_client.CoreV1Api(eks_auth.get_api_client(CLUSTER_NAME, AWS_REGION))


def _apps_v1() -> k8s_client.AppsV1Api:
    return k8s_client.AppsV1Api(eks_auth.get_api_client(CLUSTER_NAME, AWS_REGION))


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
    for ev in sorted(events.items, key=lambda e: e.last_timestamp or datetime.datetime.min.replace(tzinfo=None), reverse=True):
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


TOOLS = [
    list_pods,
    describe_pod,
    get_pod_logs,
    list_events,
    list_deployments,
    restart_deployment,
    delete_pod,
]

SYSTEM_MESSAGE = (
    "You're an SRE assistant investigating issues on a real EKS cluster "
    f"('{CLUSTER_NAME}') via Kubernetes API tools. Prefer read-only "
    "investigation (list_pods, describe_pod, get_pod_logs, list_events, "
    "list_deployments) to find the root cause before taking any write "
    "action (restart_deployment, delete_pod). Quote the actual log/event "
    "messages you found as evidence for your diagnosis."
)


def create_agent():
    from langchain_aws import ChatBedrock

    llm = ChatBedrock(
        model_id="global.anthropic.claude-sonnet-5",
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
