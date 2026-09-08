"""Google credentials for AgentCore: AWS WIF first, then ADC.

AgentCore Runtime injects AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY /
AWS_SESSION_TOKEN / AWS_REGION. There is no IMDS. google-auth's AWS
credential source reads those env vars before IMDS, so the WIF config
omits 169.254.169.254 URLs on purpose.

Locally (probe script), if WIF env is incomplete, fall back to Application
Default Credentials — typically `gcloud auth application-default login`.
That path cannot impersonate the AgentCore IAM role (its trust policy is
bedrock-agentcore.amazonaws.com only).
"""

from __future__ import annotations

import json
import os
import tempfile
import time

import google.auth
from google.auth.transport.requests import Request

SCOPES = (
    "https://www.googleapis.com/auth/logging.read",
    "https://www.googleapis.com/auth/cloud-platform.read-only",
)

_TOKEN_SKEW_SECONDS = 60
_cached: tuple[object, float] | None = None
_wif_file: str | None = None


def wif_configured() -> bool:
    return all(
        os.environ.get(k)
        for k in (
            "GCP_PROJECT_NUMBER",
            "GCP_WIF_POOL_ID",
            "GCP_WIF_PROVIDER_ID",
            "GCP_WIF_SA_EMAIL",
        )
    )


def gcp_project_id() -> str:
    project = os.environ.get("GCP_PROJECT_ID", "")
    if not project:
        raise RuntimeError("GCP_PROJECT_ID is not set")
    return project


def _wif_info() -> dict:
    number = os.environ["GCP_PROJECT_NUMBER"]
    pool = os.environ["GCP_WIF_POOL_ID"]
    provider = os.environ["GCP_WIF_PROVIDER_ID"]
    sa = os.environ["GCP_WIF_SA_EMAIL"]
    audience = (
        f"//iam.googleapis.com/projects/{number}/locations/global/"
        f"workloadIdentityPools/{pool}/providers/{provider}"
    )
    return {
        "type": "external_account",
        "audience": audience,
        "subject_token_type": "urn:ietf:params:aws:token-type:aws4_request",
        "token_url": "https://sts.googleapis.com/v1/token",
        "service_account_impersonation_url": (
            f"https://iamcredentials.googleapis.com/v1/projects/-/"
            f"serviceAccounts/{sa}:generateAccessToken"
        ),
        "credential_source": {
            "environment_id": "aws1",
            "regional_cred_verification_url": (
                "https://sts.{region}.amazonaws.com"
                "?Action=GetCallerIdentity&Version=2011-06-15"
            ),
        },
    }


def _ensure_wif_adc_file() -> None:
    global _wif_file
    if _wif_file:
        return
    fd, path = tempfile.mkstemp(prefix="gcp-wif-", suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump(_wif_info(), fh)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
    _wif_file = path


def get_access_token() -> str:
    """Return a Google OAuth access token, refreshing if needed."""
    global _cached
    now = time.monotonic()
    if _cached is not None:
        creds, expires_at = _cached
        if now < expires_at and getattr(creds, "token", None):
            return creds.token

    if wif_configured():
        _ensure_wif_adc_file()

    creds, _ = google.auth.default(scopes=list(SCOPES))
    creds.refresh(Request())
    expiry = getattr(creds, "expiry", None)
    if expiry is not None:
        ttl = max(expiry.timestamp() - time.time() - _TOKEN_SKEW_SECONDS, 30)
    else:
        ttl = 300
    _cached = (creds, time.monotonic() + ttl)
    return creds.token
