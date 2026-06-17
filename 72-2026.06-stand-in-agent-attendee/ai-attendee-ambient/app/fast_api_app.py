# Copyright 2026 Google LLC
import json
import os
import re
import google.auth
from fastapi import FastAPI, Request
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import Runner
from google.cloud import logging as google_cloud_logging
from google.genai import types

from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback
from app.ambient_agent import root_agent as _agent

setup_telemetry()
_, project_id = google.auth.default()
logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")
AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_NAME = "ambient_ai_attendee"

artifact_service_uri = f"gs://{logs_bucket_name}" if logs_bucket_name else None

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=artifact_service_uri,
    allow_origins=allow_origins,
    otel_to_cloud=True,
)
app.title = "ai-attendee-ambient"
app.description = "API for the Ambient Conference Attendee Agent (Triggered via Webhook)"

# ---------------------------------------------------------------------------
# Persistent-session runner for the webhook trigger path.
#
# AGENT_ENGINE_RESOURCE (set in .setup-env after first deploy) should be the
# full resource name: projects/{proj}/locations/{loc}/reasoningEngines/{id}
#
# When set, sessions survive across Cloud Run restarts and back-to-back
# Cloud Scheduler ticks. Without it, falls back to in-memory (good enough
# for local testing within a single server run).
# ---------------------------------------------------------------------------
_RESOURCE_RE = re.compile(
    r"projects/(?P<project>[^/]+)/locations/(?P<location>[^/]+)"
    r"/reasoningEngines/(?P<engine_id>[^/]+)"
)
_resource = os.environ.get("AGENT_ENGINE_RESOURCE", "")
_match = _RESOURCE_RE.match(_resource)

if _match:
    from google.adk.sessions.vertex_ai_session_service import VertexAiSessionService
    _session_service = VertexAiSessionService(
        project=_match.group("project"),
        location=_match.group("location"),
        agent_engine_id=_match.group("engine_id"),
    )
    logger.log_text(f"Webhook trigger: using Agent Engine sessions ({_resource})", severity="INFO")
else:
    from google.adk.sessions.in_memory_session_service import InMemorySessionService
    _session_service = InMemorySessionService()
    logger.log_text("Webhook trigger: using in-memory sessions (set AGENT_ENGINE_RESOURCE for persistence)", severity="WARNING")

_runner = Runner(
    app_name=APP_NAME,
    agent=_agent,
    session_service=_session_service,
)


@app.post("/apps/{app_name}/trigger/webhook")
async def trigger_webhook(app_name: str, request: Request):
    """Webhook trigger for Cloud Scheduler (or manual curl).

    Resumes the named session so the agent accumulates context across sweeps.
    Each trigger continues the same conversation thread rather than starting fresh.
    Pass {"session_id": "..."} in the body to use a different session.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    # Extract session_id and user_id from 'input' block (if present) to match Taskfile.yml / Reasoning Engine schema
    input_data = body.get("input", {})
    session_id = input_data.get("session_id") or body.get("session_id", "ambient-sweep-main")
    user_id = input_data.get("user_id") or body.get("user_id", "scheduler")

    session = await _session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if not session:
        session = await _session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

    new_message = types.Content(
        role="user",
        parts=[types.Part(text=json.dumps(body) if body else "tick")],
    )

    async for _ in _runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=new_message,
    ):
        pass

    return {"status": "success", "session_id": session.id}


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
