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
"""GKE cluster access for diagnostic tools.

Auth model (see spec.md §5.2): no kubeconfig, no per-tool credential fetch.
The process runs as a single GCP service account identity. That identity is
used both to resolve the cluster endpoint/CA cert via the GKE control-plane
API (IAM: roles/container.viewer or narrower) and, via Workload Identity
Federation, as the bearer token presented to the cluster's Kubernetes API
server (authorized there by RBAC bindings on the same identity). Callers only
ever need to pass addressing info (project/location/cluster/node), never a
credential object.
"""

import functools

import google.auth
import google.auth.transport.requests
from google.cloud import container_v1
from kubernetes import client as k8s_client


@functools.lru_cache(maxsize=8)
def _cluster_endpoint(project_id: str, location: str, cluster_name: str) -> tuple[str, str]:
    """Resolve a GKE cluster's API server endpoint and CA cert (cached per cluster)."""
    gke_client = container_v1.ClusterManagerClient()
    name = f"projects/{project_id}/locations/{location}/clusters/{cluster_name}"
    cluster = gke_client.get_cluster(name=name)
    return cluster.endpoint, cluster.master_auth.cluster_ca_certificate


def get_core_v1_api(project_id: str, location: str, cluster_name: str) -> k8s_client.CoreV1Api:
    """Build a Kubernetes CoreV1Api client for the given GKE cluster.

    Uses the process's default GCP credentials (see module docstring) as the
    bearer token for the cluster's API server — no separate kubeconfig.
    """
    endpoint, ca_cert_b64 = _cluster_endpoint(project_id, location, cluster_name)

    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(google.auth.transport.requests.Request())

    configuration = k8s_client.Configuration()
    configuration.host = f"https://{endpoint}"
    configuration.verify_ssl = True
    configuration.ssl_ca_cert = _write_ca_cert(ca_cert_b64)
    configuration.api_key = {"authorization": f"Bearer {credentials.token}"}

    return k8s_client.CoreV1Api(k8s_client.ApiClient(configuration))


def _write_ca_cert(ca_cert_b64: str) -> str:
    import base64
    import tempfile

    ca_cert = base64.b64decode(ca_cert_b64)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pem") as f:
        f.write(ca_cert)
        return f.name
