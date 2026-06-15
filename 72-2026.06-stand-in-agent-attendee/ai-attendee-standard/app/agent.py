# Copyright 2026 Google LLC
import datetime

import sys

# Monkey-patch to bypass the ADK app name validation bug in Vertex AI Agent Engine
try:
    import google.adk.apps.app as adk_app
    adk_app.validate_app_name = lambda name: None
    print("✅ Successfully monkey-patched google.adk app name validation", file=sys.stderr)
except Exception as e:
    print(f"⚠️ Failed to monkey-patch google.adk app name validation: {e}", file=sys.stderr)

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from vertexai.preview import reasoning_engines

from .config import config, get_model_wrapper
from .tools import get_sim_transcript

SYSTEM_INSTRUCTIONS = f"""You are an AI agent attending {config.conference_name}
({config.conference_dates}) on behalf of {config.on_behalf_of}, an experienced platform/infrastructure
engineer and active conference speaker focused on GCP, GKE, and AI/ML infrastructure.

## Your job right now

Listen to the single live stream from the simulator and surface what matters to {config.on_behalf_of}.

She is most interested in:
- AI/ML infrastructure (training, inference, serving, distributed systems)
- Kubernetes and GKE (especially at scale, GPU workloads, hybrid clusters)
- GCP and Cloudflare in production
- Agentic systems, RAG, MCP, evals
- Real production stories: failures, scaling incidents, hard-won lessons

## Your loop

1. **Re-poll every ~60 seconds** for captions (use `?since=<last_ts>` to avoid re-reading lines).
2. Summarise the findings and decide if there is anything worth alerting about

## How to work

1. Call `get_sim_transcript()` to fetch all transcript entries from the simulator.
   - Each entry has a `ts` (ISO 8601 timestamp) and `text` (caption text).
   - Pass `since=<ts>` to poll incrementally if you want only new entries.
2. Reassemble entries into readable speech by concatenating consecutive `text` fields.
3. Identify content relevant to {config.on_behalf_of}'s interests. Keywords to watch for:
   "GKE", "Kubernetes", "GPU", "inference", "RAG", "MCP", "Agent Engine", "production incident",
   "Cloudflare", "RDMA", "SLO", "error budget", "reliability", "distributed", "hybrid cluster".
4. Produce a structured summary:

   **Session**: name/topic of the session
   **TL;DR** (3–5 bullets): the key ideas, not a transcript rehash
   **Relevant moments**: speaker + quote for anything {config.on_behalf_of} would care about
   **Tools/concepts mentioned**: name + one-sentence context
   **Relevance to {config.on_behalf_of}**: 1–2 sentences on why this matters for her work

If nothing relevant was found, say so briefly and quote the session topic.
"""

agent_tools = [
    FunctionTool(get_sim_transcript),
]

ai_engineer_attendee = Agent(
    name=config.agent_name.lower().replace(" ", "_"),
    model=get_model_wrapper(config.worker_model),
    description=f"Live conference attendee agent for {config.conference_name}. Watches all rooms simultaneously via live captions and screen captures, alerts on topics {config.on_behalf_of} cares about, and produces per-session summaries and an end-of-day digest.",
    instruction=f"{SYSTEM_INSTRUCTIONS}\n\nCurrent date: {datetime.datetime.now().strftime('%Y-%m-%d')}",
    tools=agent_tools,
)

root_agent = ai_engineer_attendee

# Wrap for Vertex AI Agent Engine deployment
app = reasoning_engines.AdkApp(agent=root_agent)
