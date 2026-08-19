"""Pure-Python EKS authentication - no `aws` CLI binary required.

AgentCore Runtime's direct-code-deployment Python runtime only runs the
zipped Python package; there's no `aws-iam-authenticator` or `aws eks
get-token` binary available. This reproduces what that command does: presign
an `sts:GetCallerIdentity` request (scoped to the cluster via the
`x-k8s-aws-id` header) and hand the presigned URL to the EKS API as a bearer
token, exactly as documented at
https://docs.aws.amazon.com/eks/latest/userguide/cluster-auth.html#api-server-auth
"""

import base64
import os
import time

import boto3
from botocore.signers import RequestSigner
from kubernetes import client as k8s_client

# EKS accepts the resulting token for 15 minutes from when it was presigned,
# regardless of the expiry requested here - this just matches the aws-cli's
# convention.
STS_TOKEN_EXPIRES_IN = 60
TOKEN_PREFIX = "k8s-aws-v1."

# Refresh a bit before STS_TOKEN_EXPIRES_IN to keep a safety margin.
_CLIENT_CACHE_TTL = 45
_client_cache: dict[tuple[str, str], tuple[float, str, k8s_client.ApiClient]] = {}


def _get_bearer_token(cluster_name: str, region: str) -> str:
    session = boto3.session.Session()
    sts = session.client("sts", region_name=region)
    service_id = sts.meta.service_model.service_id

    signer = RequestSigner(
        service_id,
        region,
        "sts",
        "v4",
        session.get_credentials(),
        session.events,
    )

    params = {
        "method": "GET",
        "url": f"https://sts.{region}.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15",
        "body": {},
        "headers": {"x-k8s-aws-id": cluster_name},
        "context": {},
    }

    signed_url = signer.generate_presigned_url(
        params,
        region_name=region,
        expires_in=STS_TOKEN_EXPIRES_IN,
        operation_name="GetCallerIdentity",
    )

    encoded = base64.urlsafe_b64encode(signed_url.encode("utf-8")).decode("utf-8")
    return TOKEN_PREFIX + encoded.rstrip("=")


def get_api_client(cluster_name: str, region: str) -> k8s_client.ApiClient:
    """Get a kubernetes ApiClient authenticated against the given EKS cluster.

    Cached per (cluster_name, region) for _CLIENT_CACHE_TTL seconds - well
    under the bearer token's validity window - so a burst of tool calls
    within one agent turn doesn't re-run describe_cluster/STS-presign and
    re-write the CA cert file for every single call.
    """
    key = (cluster_name, region)
    cached = _client_cache.get(key)
    if cached is not None:
        expires_at, _ca_path, client = cached
        if time.monotonic() < expires_at:
            return client
        _evict(key)

    eks = boto3.client("eks", region_name=region)
    cluster = eks.describe_cluster(name=cluster_name)["cluster"]

    ca_path = _write_ca_cert(cluster["certificateAuthority"]["data"])
    configuration = k8s_client.Configuration()
    configuration.host = cluster["endpoint"]
    configuration.verify_ssl = True
    configuration.ssl_ca_cert = ca_path
    token = _get_bearer_token(cluster_name, region)
    configuration.api_key = {
        "authorization": token,
        "BearerToken": token,
    }
    configuration.api_key_prefix = {
        "authorization": "Bearer",
        "BearerToken": "Bearer",
    }

    client = k8s_client.ApiClient(configuration)
    _client_cache[key] = (time.monotonic() + _CLIENT_CACHE_TTL, ca_path, client)
    return client


def _evict(key: tuple[str, str]) -> None:
    _expires_at, ca_path, client = _client_cache.pop(key)
    client.close()
    try:
        os.remove(ca_path)
    except OSError:
        pass


def _write_ca_cert(ca_data_b64: str) -> str:
    import tempfile

    ca_bytes = base64.b64decode(ca_data_b64)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".crt")
    tmp.write(ca_bytes)
    tmp.close()
    return tmp.name
