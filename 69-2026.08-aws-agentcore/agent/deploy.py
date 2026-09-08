"""
Deploy the SRE LangGraph agent to AgentCore Runtime using direct code
deployment (no Docker/ECR needed).

Set CLUSTER_NAME for EKS Kubernetes tools, GCP_PROJECT_ID + WIF env for
Cloud Logging MCP (GKE app panics without hitting kube-apiserver). At least
one of the two is required. See GCP_SETUP.md.
"""

import json
import os
import shutil
import subprocess
import sys
import time

import boto3
from boto3.session import Session

# ── Configuration ────────────────────────────────────────────────────────────

AGENT_NAME = "sre_agent"
PROTOCOL = "HTTP"
PYTHON_RUNTIME = "PYTHON_3_13"
ENTRY_POINT = "agent.py"

AGENT_FILES = ["agent.py", "eks_auth.py", "gcp_auth.py", "gcp_mcp.py"]

CLUSTER_NAME = os.environ.get("CLUSTER_NAME", "")
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
GCP_PROJECT_NUMBER = os.environ.get("GCP_PROJECT_NUMBER", "")
GCP_WIF_POOL_ID = os.environ.get("GCP_WIF_POOL_ID", "")
GCP_WIF_PROVIDER_ID = os.environ.get("GCP_WIF_PROVIDER_ID", "")
GCP_WIF_SA_EMAIL = os.environ.get("GCP_WIF_SA_EMAIL", "")
GKE_CLUSTER_NAME = os.environ.get("GKE_CLUSTER_NAME", "")
GKE_LOCATION = os.environ.get("GKE_LOCATION", "")
GKE_NAMESPACE = os.environ.get("GKE_NAMESPACE", "demo")

if not CLUSTER_NAME and not GCP_PROJECT_ID:
    sys.exit("Set CLUSTER_NAME (EKS tools) and/or GCP_PROJECT_ID (Cloud Logging MCP)")

if GCP_PROJECT_ID and not all(
    (GCP_PROJECT_NUMBER, GCP_WIF_POOL_ID, GCP_WIF_PROVIDER_ID, GCP_WIF_SA_EMAIL)
):
    sys.exit(
        "GCP_PROJECT_ID is set; also set GCP_PROJECT_NUMBER, GCP_WIF_POOL_ID, "
        "GCP_WIF_PROVIDER_ID, GCP_WIF_SA_EMAIL (see GCP_SETUP.md)"
    )

# ── AWS Setup ────────────────────────────────────────────────────────────────

session = Session()
REGION = session.region_name
ACCOUNT_ID = session.client("sts").get_caller_identity()["Account"]
S3_BUCKET = f"agentcore-code-{ACCOUNT_ID}-{REGION}"
S3_PREFIX = f"{AGENT_NAME}/code.zip"
ARTIFACT_BUCKET = f"agentcore-artifacts-{ACCOUNT_ID}-{REGION}"
CLUSTER_ARN = (
    f"arn:aws:eks:{REGION}:{ACCOUNT_ID}:cluster/{CLUSTER_NAME}" if CLUSTER_NAME else ""
)

print(f"Region:     {REGION}")
print(f"Account:    {ACCOUNT_ID}")
print(f"Agent:      {AGENT_NAME}")
print(f"EKS:        {CLUSTER_ARN or '(disabled)'}")
if GCP_PROJECT_ID:
    print(f"GCP:        {GCP_PROJECT_ID}  SA={GCP_WIF_SA_EMAIL}")
    if GKE_CLUSTER_NAME:
        print(f"GKE:        {GKE_CLUSTER_NAME} loc={GKE_LOCATION} ns={GKE_NAMESPACE}")
else:
    print("GCP:        (Logging MCP disabled)")


# ── Step 1: Create IAM Execution Role ────────────────────────────────────────


def create_execution_role() -> str:
    """Create the IAM execution role with the permissions AgentCore + our EKS tools need."""
    iam = boto3.client("iam", region_name=REGION)
    role_name = f"agentcore-{AGENT_NAME}-role"

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
                "Action": "sts:AssumeRole",
                "Condition": {"StringEquals": {"aws:SourceAccount": ACCOUNT_ID}},
            }
        ],
    }

    # Base AgentCore direct-deploy permissions (logs, X-Ray, metrics, Bedrock)
    # plus eks:DescribeCluster - needed by agent/eks_auth.py to fetch the
    # cluster's API endpoint and CA cert before authenticating. Kubernetes
    # RBAC (not IAM) governs what the role can actually do once it has a
    # token - see rbac/agent-rbac.yaml.
    inline_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["logs:DescribeLogStreams", "logs:CreateLogGroup"],
                "Resource": [f"arn:aws:logs:{REGION}:{ACCOUNT_ID}:log-group:/aws/bedrock-agentcore/runtimes/*"],
            },
            {
                "Effect": "Allow",
                "Action": ["logs:DescribeLogGroups"],
                "Resource": [f"arn:aws:logs:{REGION}:{ACCOUNT_ID}:log-group:*"],
            },
            {
                "Effect": "Allow",
                "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
                "Resource": [
                    f"arn:aws:logs:{REGION}:{ACCOUNT_ID}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
                ],
            },
            {
                "Effect": "Allow",
                "Action": [
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets",
                ],
                "Resource": ["*"],
            },
            {
                "Effect": "Allow",
                "Action": "cloudwatch:PutMetricData",
                "Resource": "*",
                "Condition": {"StringEquals": {"cloudwatch:namespace": "bedrock-agentcore"}},
            },
            {
                "Sid": "BedrockModelInvocation",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                "Resource": [
                    "arn:aws:bedrock:*::foundation-model/*",
                    f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:*",
                ],
            },
            {
                "Sid": "ArtifactBucketReadWrite",
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:PutObject"],
                "Resource": f"arn:aws:s3:::{ARTIFACT_BUCKET}/*",
            },
        ],
    }
    if CLUSTER_ARN:
        inline_policy["Statement"].append(
            {
                "Sid": "EksDescribeCluster",
                "Effect": "Allow",
                "Action": "eks:DescribeCluster",
                "Resource": CLUSTER_ARN,
            }
        )

    try:
        resp = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=f"Execution role for {AGENT_NAME}",
        )
        role_arn = resp["Role"]["Arn"]
        print(f"\n✓ Created IAM role: {role_arn}")
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{role_name}"
        print(f"\n✓ IAM role exists: {role_arn}")

    iam.put_role_policy(
        RoleName=role_name,
        PolicyName=f"{AGENT_NAME}-policy",
        PolicyDocument=json.dumps(inline_policy),
    )

    print("  Waiting 10s for IAM propagation...")
    time.sleep(10)
    return role_arn


# ── Step 2: Build arm64 deployment package and upload to S3 ──────────────────


def build_and_upload_package():
    """Build a deployment zip with pre-compiled arm64 dependencies.

    AgentCore Runtime runs on arm64 (Graviton) microVMs. The zip must include
    all Python dependencies pre-compiled for arm64 - the runtime does not run
    `pip install` at startup.
    """
    s3 = boto3.client("s3", region_name=REGION)
    pkg_dir = "deployment_package"
    zip_file = "deployment_package.zip"

    try:
        if REGION == "us-east-1":
            s3.create_bucket(Bucket=S3_BUCKET)
        else:
            s3.create_bucket(
                Bucket=S3_BUCKET,
                CreateBucketConfiguration={"LocationConstraint": REGION},
            )
        print(f"\n✓ Created S3 bucket: {S3_BUCKET}")
    except (s3.exceptions.BucketAlreadyOwnedByYou, s3.exceptions.BucketAlreadyExists):
        print(f"\n✓ S3 bucket exists: {S3_BUCKET}")

    if os.path.isdir(pkg_dir):
        shutil.rmtree(pkg_dir)
    if os.path.exists(zip_file):
        os.remove(zip_file)

    print("\n  Installing arm64 dependencies with uv...")
    subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--python-platform",
            "aarch64-manylinux2014",
            "--python-version",
            "3.13",
            "--target",
            pkg_dir,
            "--only-binary",
            ":all:",
            "-r",
            "requirements.txt",
        ],
        check=True,
    )

    print("  Creating deployment zip...")
    subprocess.run(
        ["zip", "-r", f"../{zip_file}", "."],
        cwd=pkg_dir,
        check=True,
        capture_output=True,
    )
    for src_file in AGENT_FILES:
        subprocess.run(["zip", zip_file, src_file], check=True, capture_output=True)

    zip_size = os.path.getsize(zip_file) / (1024 * 1024)
    print(f"  ✓ Package: {zip_file} ({zip_size:.1f} MB)")

    print(f"  Uploading to s3://{S3_BUCKET}/{S3_PREFIX}...")
    s3.upload_file(zip_file, S3_BUCKET, S3_PREFIX)
    print("  ✓ Uploaded")

    shutil.rmtree(pkg_dir)
    os.remove(zip_file)


def create_artifact_bucket():
    """Create the S3 bucket the agent uses at runtime for input/report artifacts."""
    s3 = boto3.client("s3", region_name=REGION)
    try:
        if REGION == "us-east-1":
            s3.create_bucket(Bucket=ARTIFACT_BUCKET)
        else:
            s3.create_bucket(
                Bucket=ARTIFACT_BUCKET,
                CreateBucketConfiguration={"LocationConstraint": REGION},
            )
        print(f"\n✓ Created S3 artifact bucket: {ARTIFACT_BUCKET}")
    except (s3.exceptions.BucketAlreadyOwnedByYou, s3.exceptions.BucketAlreadyExists):
        print(f"\n✓ S3 artifact bucket exists: {ARTIFACT_BUCKET}")


def runtime_environment_variables() -> dict[str, str]:
    env = {
        "AWS_REGION": REGION,
        "ARTIFACT_BUCKET": ARTIFACT_BUCKET,
    }
    if CLUSTER_NAME:
        env["CLUSTER_NAME"] = CLUSTER_NAME
    if GCP_PROJECT_ID:
        env.update(
            {
                "GCP_PROJECT_ID": GCP_PROJECT_ID,
                "GCP_PROJECT_NUMBER": GCP_PROJECT_NUMBER,
                "GCP_WIF_POOL_ID": GCP_WIF_POOL_ID,
                "GCP_WIF_PROVIDER_ID": GCP_WIF_PROVIDER_ID,
                "GCP_WIF_SA_EMAIL": GCP_WIF_SA_EMAIL,
            }
        )
        if GKE_CLUSTER_NAME:
            env["GKE_CLUSTER_NAME"] = GKE_CLUSTER_NAME
        if GKE_LOCATION:
            env["GKE_LOCATION"] = GKE_LOCATION
        if GKE_NAMESPACE:
            env["GKE_NAMESPACE"] = GKE_NAMESPACE
    return env


def runtime_description() -> str:
    bits = []
    if GCP_PROJECT_ID:
        bits.append("GKE via Cloud Logging MCP")
    if CLUSTER_NAME:
        bits.append("EKS Kubernetes API")
    return "LangGraph SRE agent: " + " + ".join(bits) if bits else "LangGraph SRE agent"


# ── Step 3: Create AgentCore Runtime ─────────────────────────────────────────


def create_runtime(role_arn: str) -> dict:
    control = boto3.client("bedrock-agentcore-control", region_name=REGION)

    existing_runtime_id = None
    try:
        runtimes = control.list_agent_runtimes().get("agentRuntimes", [])
        for rt in runtimes:
            if rt["agentRuntimeName"] == AGENT_NAME:
                existing_runtime_id = rt["agentRuntimeId"]
                break
    except Exception as e:
        print(f"Error checking existing runtimes: {e}")

    if existing_runtime_id:
        print(f"\n  Updating existing AgentCore Runtime '{AGENT_NAME}' ({existing_runtime_id})...")
        response = control.update_agent_runtime(
            agentRuntimeId=existing_runtime_id,
            agentRuntimeArtifact={
                "codeConfiguration": {
                    "code": {"s3": {"bucket": S3_BUCKET, "prefix": S3_PREFIX}},
                    "runtime": PYTHON_RUNTIME,
                    "entryPoint": [ENTRY_POINT],
                }
            },
            roleArn=role_arn,
            networkConfiguration={"networkMode": "PUBLIC"},
            protocolConfiguration={"serverProtocol": PROTOCOL},
            environmentVariables=runtime_environment_variables(),
            description=runtime_description(),
        )
        runtime_id = existing_runtime_id
        runtime_arn = response.get("agentRuntimeArn") or f"arn:aws:bedrock-agentcore:{REGION}:{ACCOUNT_ID}:runtime/{runtime_id}"
    else:
        print(f"\n  Creating new AgentCore Runtime '{AGENT_NAME}'...")
        response = control.create_agent_runtime(
            agentRuntimeName=AGENT_NAME,
            agentRuntimeArtifact={
                "codeConfiguration": {
                    "code": {"s3": {"bucket": S3_BUCKET, "prefix": S3_PREFIX}},
                    "runtime": PYTHON_RUNTIME,
                    "entryPoint": [ENTRY_POINT],
                }
            },
            roleArn=role_arn,
            networkConfiguration={"networkMode": "PUBLIC"},
            protocolConfiguration={"serverProtocol": PROTOCOL},
            environmentVariables=runtime_environment_variables(),
            description=runtime_description(),
        )
        runtime_id = response["agentRuntimeId"]
        runtime_arn = response["agentRuntimeArn"]

    print(f"  ✓ Runtime registered: {runtime_id}")

    print("  Waiting for runtime to be ready...")
    while True:
        status_resp = control.get_agent_runtime(agentRuntimeId=runtime_id)
        status = status_resp["status"]
        print(f"    Status: {status}")
        if status == "READY":
            break
        if status in ("CREATE_FAILED", "UPDATE_FAILED"):
            print(f"  ✗ Failed: {status_resp.get('failureReason', 'Unknown')}")
            sys.exit(1)
        time.sleep(15)

    return {"runtime_id": runtime_id, "runtime_arn": runtime_arn}


# ── Step 4: Create Endpoint ──────────────────────────────────────────────────


def create_endpoint(runtime_id: str) -> dict:
    control = boto3.client("bedrock-agentcore-control", region_name=REGION)

    try:
        eps = control.list_agent_runtime_endpoints(agentRuntimeId=runtime_id)
        for ep in eps.get("runtimeEndpoints", []):
            if ep["name"] == "default":
                print("  ✓ Endpoint 'default' already exists")
                status = ep["status"]
                print(f"    Status: {status}")
                if status == "READY":
                    return ep
                print("  Waiting for endpoint to be ready...")
                while True:
                    eps_status = control.list_agent_runtime_endpoints(agentRuntimeId=runtime_id)
                    for ep_status in eps_status.get("runtimeEndpoints", []):
                        if ep_status["name"] == "default":
                            status = ep_status["status"]
                            print(f"    Status: {status}")
                            if status == "READY":
                                return ep_status
                            if status in ("CREATE_FAILED", "UPDATE_FAILED"):
                                print("  ✗ Endpoint check failed")
                                sys.exit(1)
                    time.sleep(15)
    except Exception as e:
        print(f"  Warning checking endpoints: {e}")

    print("\n  Creating endpoint 'default'...")
    response = control.create_agent_runtime_endpoint(
        agentRuntimeId=runtime_id,
        name="default",
    )
    print(f"  ✓ Endpoint created: {response['agentRuntimeEndpointArn']}")

    print("  Waiting for endpoint to be ready...")
    while True:
        eps = control.list_agent_runtime_endpoints(agentRuntimeId=runtime_id)
        for ep in eps.get("runtimeEndpoints", []):
            if ep["name"] == "default":
                status = ep["status"]
                print(f"    Status: {status}")
                if status == "READY":
                    return ep
                if status in ("CREATE_FAILED", "UPDATE_FAILED"):
                    print("  ✗ Endpoint creation failed")
                    sys.exit(1)
        time.sleep(15)


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("=" * 60)
    print(f"Deploying {AGENT_NAME} to AgentCore Runtime")
    print("  (direct code deployment — no Docker required)")
    print("=" * 60)

    role_arn = create_execution_role()
    create_artifact_bucket()
    build_and_upload_package()
    runtime = create_runtime(role_arn)
    create_endpoint(runtime["runtime_id"])

    config = {
        "agent_name": AGENT_NAME,
        "runtime_id": runtime["runtime_id"],
        "runtime_arn": runtime["runtime_arn"],
        "region": REGION,
        "role_arn": role_arn,
        "cluster_name": CLUSTER_NAME,
        "gcp_project_id": GCP_PROJECT_ID,
        "gke_cluster_name": GKE_CLUSTER_NAME,
        "gke_namespace": GKE_NAMESPACE,
        "artifact_bucket": ARTIFACT_BUCKET,
    }
    with open("runtime_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("\n" + "=" * 60)
    print("✓ Deployment complete!")
    print(f"  Runtime ARN: {runtime['runtime_arn']}")
    print(f"  Role ARN:    {role_arn}")
    print("  Config saved to: runtime_config.json")
    if CLUSTER_NAME:
        print("\n  EKS: grant this role RBAC before invoking:")
        print(f"    task grant-access AGENT_ROLE_ARN={role_arn}")
    if GCP_PROJECT_ID:
        print("\n  GCP: WIF must trust this role (GCP_SETUP.md). Probe:")
        print("    task probe-gcp-logs")
        print('    task invoke -- "Find CrashLoopBackOff evidence in Cloud Logging for the demo namespace"')
    print("=" * 60)


if __name__ == "__main__":
    main()
