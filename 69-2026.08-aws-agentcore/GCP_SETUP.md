# GCP / GKE setup for Step 0 (Cloud Logging MCP)

This is the **GCP-side checklist** for the AgentCore SRE POC. Inference and the
agent stay on AWS. GCP is used only as a **data plane**: Cloud Logging (already
exported from GKE) behind Google's hosted MCP at
`https://logging.googleapis.com/mcp`.

No Gemini Enterprise agent. No Vertex / Agent Platform AI. No AgentCore CIDRs
on GKE authorized networks. The Kubernetes API is **not** in scope for Step 0.

```
you ──invoke──▶ AgentCore Runtime (AWS, PUBLIC)
                  ├─ Bedrock (AWS)
                  └─ HTTPS + WIF token ──▶ logging.googleapis.com/mcp
                                              └─ Cloud Logging (k8s_container / k8s_cluster)
```

The AgentCore execution role name is **predictable** (created by `agent/deploy.py`):

```
arn:aws:iam::<AWS_ACCOUNT_ID>:role/agentcore-sre_agent-role
```

Create WIF against that ARN **before** deploy, or after the first deploy — the
name does not change.

---

## 0. Values to fill in

| Name | Example | Notes |
|---|---|---|
| `GCP_PROJECT_ID` | `my-gke-proj` | Project that **owns the GKE cluster** (or the sink if logs are aggregated) |
| `GCP_PROJECT_NUMBER` | `123456789012` | `gcloud projects describe $GCP_PROJECT_ID --format='value(projectNumber)'` |
| `AWS_ACCOUNT_ID` | `111122223333` | Account that will host AgentCore |
| `GKE_CLUSTER_NAME` | `prod-gke` | Used only to default log filters |
| `GKE_LOCATION` | `us-central1` | Region or zone of the cluster |
| `GKE_NAMESPACE` | `demo` | Where the crash-loop demo will run |
| WIF pool / provider | `aws-agentcore` / `aws` | IDs you choose; must match env vars below |

Export on the AWS laptop after this spec is done:

```bash
export GCP_PROJECT_ID=...
export GCP_PROJECT_NUMBER=...
export GCP_WIF_POOL_ID=aws-agentcore
export GCP_WIF_PROVIDER_ID=aws
export GCP_WIF_SA_EMAIL=agentcore-sre-logging@${GCP_PROJECT_ID}.iam.gserviceaccount.com
export GKE_CLUSTER_NAME=...
export GKE_LOCATION=...
export GKE_NAMESPACE=demo
```

---

## 1. APIs (no AI products)

```bash
gcloud config set project "$GCP_PROJECT_ID"

gcloud services enable \
  logging.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  sts.googleapis.com \
  cloudresourcemanager.googleapis.com
```

`container.googleapis.com` is **not** required for Step 0 unless you still use
it to administer the cluster yourself.

Do **not** enable Vertex AI / Agent Platform / Gemini Enterprise for this POC.

---

## 2. GKE: make sure workload logs exist

Authorized networks / firewalls do **not** need to change. Cloud Logging is
pulled from Google's logging backend, not from kube-apiserver.

Golden path: `SYSTEM` + `WORKLOAD` logging (Autopilot usually already has this).

```bash
gcloud container clusters describe "$GKE_CLUSTER_NAME" \
  --location="$GKE_LOCATION" \
  --format='yaml(loggingConfig,loggingService)'
```

If `WORKLOADS` / `SYSTEM_COMPONENTS` are missing:

```bash
# The flag replaces the set. Always include SYSTEM.
gcloud container clusters update "$GKE_CLUSTER_NAME" \
  --location="$GKE_LOCATION" \
  --logging=SYSTEM,WORKLOAD
```

Optional: apply the same crash-loop Deployment this repo uses (from a machine
that **is** on authorized networks — your laptop/VPN, not AgentCore):

```bash
kubectl apply -f broken-app/crashloop-app.yaml
# wait ~1 min
gcloud logging read \
  'resource.type="k8s_container"
   AND resource.labels.cluster_name="'"$GKE_CLUSTER_NAME"'"
   AND resource.labels.namespace_name="'"$GKE_NAMESPACE"'"
   AND timestamp>="-1h"' \
  --project="$GCP_PROJECT_ID" \
  --limit=5 \
  --format='table(timestamp,severity,textPayload,jsonPayload.message)'
```

You should see `FATAL: could not connect to database...`. If this query is
empty, the agent will have nothing to diagnose — fix logging/workload first.

If you cannot apply manifests, pick a namespace that already crash-loops and
set `GKE_NAMESPACE` to that.

---

## 3. GCP service account (viewer, not admin)

Google's Logging MCP docs mention `roles/logging.admin`. For this POC use
**viewer** plus MCP tool user.

```bash
gcloud iam service-accounts create agentcore-sre-logging \
  --display-name="AgentCore SRE (Cloud Logging MCP, read-only)"

gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
  --member="serviceAccount:agentcore-sre-logging@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/logging.viewer"

gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
  --member="serviceAccount:agentcore-sre-logging@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/mcp.toolUser"
```

If `roles/mcp.toolUser` is missing in your org (MCP IAM still rolling out),
grant `mcp.tools.call` via a custom role, or temporarily use the role your
platform team has documented for Google remote MCP.

Do **not** download a JSON key.

---

## 4. Workload Identity Federation (AWS IAM role → GCP SA)

```bash
gcloud iam workload-identity-pools create aws-agentcore \
  --location=global \
  --display-name="AWS AgentCore SRE"

gcloud iam workload-identity-pools providers create-aws aws \
  --location=global \
  --workload-identity-pool=aws-agentcore \
  --account-id="$AWS_ACCOUNT_ID" \
  --attribute-mapping="google.subject=assertion.arn,attribute.aws_role=assertion.arn.extract('assumed-role/{role}/')" \
  --attribute-condition="assertion.arn.extract('assumed-role/{role}/') == 'agentcore-sre_agent-role'"
```

Allow that pool principal to impersonate the SA:

```bash
PROJECT_NUMBER=$(gcloud projects describe "$GCP_PROJECT_ID" --format='value(projectNumber)')

gcloud iam service-accounts add-iam-policy-binding \
  "agentcore-sre-logging@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/aws-agentcore/attribute.aws_role/agentcore-sre_agent-role"
```

AgentCore assumed-role ARNs look like:

```
arn:aws:sts::<AWS_ACCOUNT_ID>:assumed-role/agentcore-sre_agent-role/<session>
```

The extract mapping yields `agentcore-sre_agent-role`.

---

## 5. Local MCP probe (your Google user, not WIF)

The AgentCore role trust policy is `bedrock-agentcore.amazonaws.com` only —
you **cannot** `aws sts assume-role` into it from a laptop. Prove Logging MCP
and GKE log volume with **your** ADC first:

```bash
gcloud auth application-default login
# needs logging.viewer (or equivalent) on the project

export GCP_PROJECT_ID=...
export GKE_CLUSTER_NAME=...
export GKE_LOCATION=...
export GKE_NAMESPACE=demo

task probe-gcp-logs
```

This hits `list_log_names` then `list_log_entries`. Success here means MCP +
GKE workload logs work. It does **not** prove WIF.

---

## 6. VPC Service Controls (if the project is in a perimeter)

AgentCore calls `logging.googleapis.com`, `sts.googleapis.com`, and
`iamcredentials.googleapis.com` from **public AWS IPs**. That is perimeter
**ingress**.

You need an ingress rule that allows the WIF SA (or the pool principal) to
those APIs. IP-based access levels will not work (same reason as GKE
authorized networks).

If the POC project is **not** in a perimeter, skip this. If it is, this is
the most likely production blocker — get a platform exception or use a
scratch project outside the perimeter for the demo.

---

## 7. Optional: Model Armor / org MCP policy

If the org enables Model Armor on `GOOGLE_MCP_SERVER`, tool responses (pod
logs) may be inspected or **logged in full**. For a POC, prefer a project
where floor settings do not block `list_log_entries`.

IAM deny policies on MCP mutate tools are irrelevant here (Logging MCP is
read-only for the tools we call).

---

## 8. What you send back to the AWS side

After steps 1–4:

```text
GCP_PROJECT_ID=
GCP_PROJECT_NUMBER=
GCP_WIF_POOL_ID=aws-agentcore
GCP_WIF_PROVIDER_ID=aws
GCP_WIF_SA_EMAIL=agentcore-sre-logging@<project>.iam.gserviceaccount.com
GKE_CLUSTER_NAME=
GKE_LOCATION=
GKE_NAMESPACE=demo
```

Then on AWS:

```bash
# do not set CLUSTER_NAME unless you also want the EKS tools
task deploy-agent
task invoke -- "Find CrashLoopBackOff evidence in Cloud Logging for the demo namespace"
```

---

## Out of scope (later steps)

- GKE remote MCP (`https://container.googleapis.com/mcp`) — live kubectl
- Monitoring / Error Reporting MCP
- Mutating cluster or workloads
- Putting any LLM or agent runtime on GCP
