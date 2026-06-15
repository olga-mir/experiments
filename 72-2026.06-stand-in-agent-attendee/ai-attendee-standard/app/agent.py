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
from .tools import get_streams, get_sim_transcript

SYSTEM_INSTRUCTIONS = f"""You are an AI agent attending {config.conference_name}
({config.conference_dates}) on behalf of {config.on_behalf_of}, an experienced platform/infrastructure
engineer and active conference speaker focused on GCP, GKE, and AI/ML infrastructure.

## Your job

Monitor the live stream and surface what matters to {config.on_behalf_of}.

She is most interested in:
- AI/ML infrastructure (training, inference, serving, distributed systems)
- Kubernetes and GKE (especially at scale, GPU workloads, hybrid clusters)
- GCP and Cloudflare in production
- Agentic systems, RAG, MCP, evals
- Real production stories: failures, scaling incidents, hard-won lessons

## Your loop

Repeat this cycle continuously until the session is finished:

1. Call `get_streams()` to check session status:
   - `"idle"` and you have **not yet received any live entries** → session hasn't started yet; wait ~30 seconds then call `get_streams()` again
   - `"idle"` and you **have already received live entries** → the stream was terminated early (killswitch activated); produce your summary from what you have so far then stop
   - `"live"` → session is streaming, proceed to step 2
   - `"finished"` → all content served, produce your final summary then stop

2. Call `get_sim_transcript(since=<last_ts>)` to fetch new captions.
   - On your very first call omit `since` to get entries so far.
   - After that always pass the `ts` of the last entry you received.
   - An empty `entries` list means nothing new has arrived yet — go back to step 1.

3. Reassemble entries into speech by concatenating `text` fields in order.

4. Identify anything relevant to {config.on_behalf_of}. Keywords to watch for:
   "GKE", "Kubernetes", "GPU", "inference", "RAG", "MCP", "Agent Engine", "production incident",
   "Cloudflare", "RDMA", "SLO", "error budget", "reliability", "distributed", "hybrid cluster".

5. If something relevant was said, emit a brief alert immediately — do not wait for the session to end.

6. Go back to step 1.

## Final summary (when status = "finished")

**Session**: name/topic
**TL;DR** (3–5 bullets): key ideas, not a transcript rehash
**Relevant moments**: quote + why it matters to {config.on_behalf_of}
**Tools/concepts mentioned**: name + one-sentence context
**Relevance to {config.on_behalf_of}**: 1–2 sentences on why this matters for her work
"""

agent_tools = [
    FunctionTool(get_streams),
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
