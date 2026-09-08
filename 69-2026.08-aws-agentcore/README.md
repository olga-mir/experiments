# AgentCore SRE agent (EKS API and/or GKE via Cloud Logging MCP)

A LangGraph agent, deployed to [Amazon Bedrock AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html)
via **direct code deployment**. Inference stays on Bedrock. There is no Gemini
Enterprise / Agent Platform agent in this POC.

Two investigation backends (enabled independently via env):

1. **EKS** — `kubernetes` client + IAM authenticator (`agent/eks_auth.py`).
2. **GKE Step 0** — Cloud Logging **remote MCP** (`https://logging.googleapis.com/mcp`)
   using AWS→GCP [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation-with-other-clouds).
   No kube-apiserver, so GKE authorized networks do not apply.

GCP setup (APIs, WIF, GKE logging, SA) is in **[GCP_SETUP.md](GCP_SETUP.md)**.

Base pattern adapted from the AgentCore samples repo:
`01-features/02-host-your-agent/01-runtime/01-hosting-agents/01-http-protocol/02-langgraph-bedrock`.

## Architecture (GKE / Logging MCP)

```
you ──invoke_agent_runtime()──▶ AgentCore Runtime (PUBLIC network mode)
                                   └─ LangGraph agent (Bedrock)
                                        ├─ Logging MCP ──▶ logging.googleapis.com
                                        │                    (k8s_container / k8s_cluster)
                                        └─ S3 tools ──▶ agentcore-artifacts-<account>-<region>
```

- **Auth to Bedrock**: runtime IAM role (`bedrock:InvokeModel`).
- **Auth to GCP**: the same IAM role is trusted by a GCP WIF pool; Google STS
  mints a token for `agentcore-sre-logging@…`, which has `roles/logging.viewer`
  + `roles/mcp.toolUser`. No service-account JSON keys.
- **Network**: AgentCore reaches public Google APIs over the internet. It never
  talks to the GKE control-plane CIDR.

EKS mode is unchanged: `eks_auth.py` + RBAC + optional public Fargate cluster
(`cluster.yaml`). That path still needs a reachable EKS API endpoint.

## Layout

- `GCP_SETUP.md` — GCP/GKE checklist for Step 0
- `cluster.yaml` / `rbac/` / `broken-app/` — EKS demo (optional)
- `agent/` — LangGraph agent, WIF + MCP client, deploy/invoke/probe/cleanup

## GKE Step 0 usage

Complete [GCP_SETUP.md](GCP_SETUP.md), then:

```bash
export GCP_PROJECT_ID=...
export GCP_PROJECT_NUMBER=...
export GCP_WIF_POOL_ID=aws-agentcore
export GCP_WIF_PROVIDER_ID=aws
export GCP_WIF_SA_EMAIL=agentcore-sre-logging@${GCP_PROJECT_ID}.iam.gserviceaccount.com
export GKE_CLUSTER_NAME=...
export GKE_LOCATION=...
export GKE_NAMESPACE=demo

# From a machine that can reach GKE (VPN), optional demo workload:
task seed-broken-app

# MCP + logs with your Google user (does not prove WIF):
gcloud auth application-default login
task probe-gcp-logs

task deploy-agent
task invoke -- "Find CrashLoopBackOff evidence in Cloud Logging for the demo namespace"
```

Do **not** set `CLUSTER_NAME` unless you also want the EKS Kubernetes tools.

## EKS usage (original)

```bash
export CLUSTER_NAME=agentcore-sre-demo   # AWS_REGION defaults from `aws configure get region`

task cluster-up          # ~15 min — creates the Fargate EKS cluster
task seed-broken-app      # deploys the crash-looping demo workload

task deploy-agent
task grant-access AGENT_ROLE_ARN=<the arn printed at deploy>

task invoke -- "Investigate the demo namespace, something looks broken"
task seed-input
task invoke -- "Fetch input/ticket.txt from S3 and investigate the reported issue, then upload your report"
```

## Teardown

```bash
task cleanup-agent   # AgentCore runtime, IAM role, S3 artifacts
task cluster-down    # EKS cluster only if you created one
```

## Screenshots

### AWS SRE Agent Panel
<img src="screenshots/aws-sre-agent-panel.png" alt="AWS SRE Agent Panel" style="max-width: 650px;" />

### AWS Harness with Coding Interpreter
<img src="screenshots/aws-harness-with-coding-interpreter.png" alt="AWS Harness with Coding Interpreter" style="max-width: 650px;" />

### AWS Coding Harness Trace Tree
<img src="screenshots/aws-coding-harness-trace-tree.png" alt="AWS Coding Harness Trace Tree" style="max-width: 650px;" />
