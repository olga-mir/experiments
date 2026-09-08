"""One-shot Cloud Logging MCP probe (no Bedrock, no AgentCore).

Uses WIF env if set, otherwise Application Default Credentials.

Usage:
    GCP_PROJECT_ID=... uv run --with-requirements requirements.txt python probe_logging_mcp.py
    GCP_PROJECT_ID=... uv run ... python probe_logging_mcp.py 'resource.type="k8s_container"'
"""

import os
import sys

import gcp_auth
import gcp_mcp


def main() -> None:
    project = gcp_auth.gcp_project_id()
    cluster = os.environ.get("GKE_CLUSTER_NAME", "")
    namespace = os.environ.get("GKE_NAMESPACE", "demo")
    location = os.environ.get("GKE_LOCATION", "")

    if len(sys.argv) > 1:
        log_filter = " ".join(sys.argv[1:])
    else:
        from datetime import datetime, timedelta, timezone

        since = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        clauses = ['resource.type="k8s_container"', f'timestamp>="{since}"']
        if cluster:
            clauses.append(f'resource.labels.cluster_name="{cluster}"')
        if location:
            clauses.append(f'resource.labels.location="{location}"')
        if namespace:
            clauses.append(f'resource.labels.namespace_name="{namespace}"')
        log_filter = " AND ".join(clauses)

    auth = "AWS WIF" if gcp_auth.wif_configured() else "Application Default Credentials"
    print(f"Project:  {project}")
    print(f"Auth:     {auth}")
    print(f"Filter:   {log_filter}\n")

    print("── list_log_names (first page) ──")
    print(gcp_mcp.list_log_names(project_id=project, page_size=50))
    print("\n── list_log_entries ──")
    print(gcp_mcp.list_log_entries(project_id=project, filter=log_filter, page_size=10))


if __name__ == "__main__":
    main()
