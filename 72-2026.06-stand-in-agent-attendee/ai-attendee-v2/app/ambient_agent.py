# Copyright 2026 Google LLC
import datetime
import json
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from .config import config, get_model_wrapper
from .tools import (
    get_live_streams,
    get_captions,
    get_current_screen,
    get_program,
    list_past_sessions,
    get_session_transcript,
    checkin,
    save_screenshot_to_bucket,
)

# Import the reusable GitHub MCP toolset helper
try:
    from shared_tools import get_github_mcp_toolset
    github_toolset = get_github_mcp_toolset()
except Exception as e:
    print(f"⚠️ Warning: Could not initialize GitHub MCP toolset: {e}")
    github_toolset = None

def parse_event(raw_event: str) -> dict:
    """Parses the incoming trigger event payload."""
    try:
        event = json.loads(raw_event)
        return {
            "data": event.get("data"),
            "attributes": event.get("attributes", {}),
        }
    except Exception:
        return {"raw": raw_event}

AMBIENT_SYSTEM_INSTRUCTIONS = f"""You are an Ambient AI agent attending {config.conference_name}
({config.conference_dates}) on behalf of {config.on_behalf_of}.

You are triggered periodically (e.g., via Pub/Sub or a timer). Each time you are triggered,
your goal is to perform a single "sweep" of the conference status, alert on anything
important, and then finish.

## Your primary job

Be {config.on_behalf_of}'s eyes and ears across all rooms simultaneously.
- AI/ML infrastructure
- Kubernetes and GKE
- GCP and Cloudflare
- Agentic systems, RAG, MCP
- Production stories

## Your Ambient Sweep (Perform this once per trigger)

1. **Check what's live** — call `get_live_streams()`.
2. **Review live rooms** — for each live stream, call `get_captions()` and `get_current_screen()`.
3. **Analyze and Alert** — If keywords like "GKE", "GPU", "RAG", "MCP" appear, or if a demo is on screen, alert {config.on_behalf_of}.
4. **Screenshot** — If you see something worth preserving, call `save_screenshot_to_bucket(stream_id)`.
5. **Summarize** — Produce summaries for any recently completed sessions.
6. **Commit** — Commit any findings, alerts, or summaries to the conference GitHub repository.

## State Management

Since you run periodically, use your memory/session to keep track of the last timestamp
you processed for each room to avoid duplicate alerts. Use the `?since=` parameter in `get_captions`.

## GitHub Commits

The repository is `{config.conference_repo}`.
Path: `{config.conference_name.lower().replace(" ", "-")}/ambient/<ISO-timestamp>.md`.

Finish your execution once you have completed the sweep for all active rooms.
"""

ambient_agent_tools = [
    FunctionTool(parse_event),
    FunctionTool(get_live_streams),
    FunctionTool(get_captions),
    FunctionTool(get_current_screen),
    FunctionTool(get_program),
    FunctionTool(list_past_sessions),
    FunctionTool(get_session_transcript),
    FunctionTool(checkin),
    FunctionTool(save_screenshot_to_bucket),
]

if github_toolset:
    ambient_agent_tools.append(github_toolset)

ambient_ai_attendee = Agent(
    name="ambient_ai_attendee",
    model=get_model_wrapper(config.worker_model),
    description=f"Ambient conference attendee agent for {config.conference_name}. Periodically sweeps all rooms, alerts on key topics, and commits findings to GitHub.",
    instruction=f"{AMBIENT_SYSTEM_INSTRUCTIONS}\n\nCurrent date: {datetime.datetime.now().strftime('%Y-%m-%d')}",
    tools=ambient_agent_tools,
)

root_agent = ambient_ai_attendee
