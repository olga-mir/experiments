# Copyright 2026 Google LLC
import datetime
import json
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from .config import config, get_model_wrapper
from .tools import (
    get_streams,
    get_sim_transcript,
)

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

1. **Check status** — call `get_streams()`.
   - `"idle"` and you have not yet received any entries → session hasn't started; note this and finish.
   - `"idle"` and you have already received entries → stream was killed early; summarize what you have then finish.
   - `"live"` → proceed to step 2.
   - `"finished"` → fetch remaining transcript (step 2), produce final summary, and finish.
2. **Fetch captions** — call `get_sim_transcript(since=<last_ts>)`. Omit `since` on the first call.
3. **Analyze and Alert** — If keywords like "GKE", "GPU", "RAG", "MCP" appear, note them clearly in your response with a brief explanation of why they are relevant to {config.on_behalf_of}.

## State Management

Since you run periodically, use your memory/session to keep track of the last timestamp
you processed to avoid duplicate alerts. Pass it as the `since` argument to `get_sim_transcript`.

Finish your execution once you have completed the sweep.
"""

ambient_agent_tools = [
    FunctionTool(parse_event),
    FunctionTool(get_streams),
    FunctionTool(get_sim_transcript),
]

ambient_ai_attendee = Agent(
    name="ambient_ai_attendee",
    model=get_model_wrapper(config.worker_model),
    description=f"Ambient conference attendee agent for {config.conference_name}. Periodically sweeps all rooms, alerts on key topics, and commits findings to GitHub.",
    instruction=f"{AMBIENT_SYSTEM_INSTRUCTIONS}\n\nCurrent date: {datetime.datetime.now().strftime('%Y-%m-%d')}",
    tools=ambient_agent_tools,
)

root_agent = ambient_ai_attendee
