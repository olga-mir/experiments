# Stand-In Agent Attendee

AI agent that attends a conference on behalf of a user, monitors live captions, and surfaces relevant moments in real time.

## Sub-projects

### `ai-attendee-ambient/`
Periodically triggered agent deployed to Vertex AI Agent Engine (agent_runtime). Cloud Scheduler POSTs a "tick" to the webhook endpoint every 5 minutes; each tick does one sweep — checks stream status, fetches new captions since last poll, and emits alerts for relevant keywords (GKE, GPU, RAG, MCP, etc.). Uses Vertex AI sessions for state continuity across ticks.

### `ai-attendee-standard/`
Long-running reactive agent deployed to Vertex AI Agent Engine. Loops continuously: checks stream status → fetches captions → analyzes → alerts → repeat, until the session finishes. Suited for running interactively during a session via the Agent Engine playground.

## Simulation mode (default)

Both agents are wired for simulation only. They call two endpoints on the backend sim:
- `GET /streams` — check if the session is idle / live / finished
- `GET /transcript?since=<ts>` — fetch new transcript entries since last poll

`SIMULATION_BASE_URL` in `.setup-env` points to the deployed sim backend (Cloud Run). `SIMULATION_MODE=true` must also be set.

## Key env vars (`.setup-env`)

| Var | Purpose |
|-----|---------|
| `SIMULATION_BASE_URL` | URL of the sim backend Cloud Run service |
| `SIMULATION_MODE` | Set to `true` to use sim tools |
| `AGENT_ENGINE_RESOURCE` | Reasoning engine resource name (set after first deploy, used for persistent sessions) |
| `GCP_PROJECT_ID` | GCP project |

## Dev workflow

```bash
# Install deps
task install

# Run one sweep locally (no deploy needed)
task run

# Local webhook server (for manual trigger testing)
task server
task trigger   # in another terminal — simulates a Cron tick

# Deploy to Vertex AI Agent Engine
task deploy

# Wire up Cloud Scheduler (requires AGENT_URL env var)
AGENT_URL=https://... task schedule
```

## Infra setup (one-time)

```bash
task setup:infra   # enables APIs, creates SA, grants IAM roles
```

Then after first `task deploy`, copy `remote_agent_runtime_id` from `deployment_metadata.json`
into `.setup-env` as `AGENT_ENGINE_RESOURCE`, then `task deploy` again to pick it up.
