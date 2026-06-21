# Stand-In Agent Attendee

AI agent that attends a conference on behalf of a user, monitors live captions, and surfaces relevant moments in real time.

## Sub-projects

### `ai-attendee-ambient/`
Periodically triggered agent deployed to Vertex AI Agent Engine. Cloud Scheduler POSTs a "tick" directly to the Reasoning Engine `:streamQuery` REST endpoint every 5 minutes; each tick does one sweep — checks stream status, fetches new captions since last poll, and emits alerts for relevant keywords (GKE, GPU, RAG, MCP, etc.). Uses a persistent Vertex AI session for state continuity across ticks.

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

# One-time infra setup (SA, IAM, APIs)
task setup:infra

# Create a persistent session (required before scheduling)
task session:create

# Wire up Cloud Scheduler
AGENT_URL=https://us-east1-aiplatform.googleapis.com/v1/projects/<PROJECT_NUM>/locations/us-east1/reasoningEngines/<ENGINE_ID> \
  task schedule

# View agent outputs
task logs

# Reset session between test runs (then re-run task schedule)
task session:reset
```

## How Cloud Scheduler triggers the agent

The scheduler job POSTs directly to the Reasoning Engine `:streamQuery` REST endpoint:

```
POST https://us-east1-aiplatform.googleapis.com/v1/projects/<NUM>/locations/us-east1/reasoningEngines/<ID>:streamQuery
Authorization: Bearer <oauth-token>   # OAuth required for *.googleapis.com URLs
Content-Type: application/json

{"input": {"message": "tick", "user_id": "scheduler", "session_id": "<session-id>"}}
```

Key details:
- **OAuth (not OIDC):** Cloud Scheduler's OAuth token auth requires the URL to end in `.googleapis.com`. The Taskfile auto-selects OIDC for Cloud Run URLs.
- **`input` envelope:** The Reasoning Engine API wraps all method arguments under `input`.
- **Persistent session:** The session must be created first via `task session:create`. The ID is saved to `.ambient_session_id` and picked up automatically by `task schedule`.
- **SA permissions:** `ambient-attendee-scheduler@<project>.iam.gserviceaccount.com` needs `roles/aiplatform.user`.

## Session Reset vs. Simulation Reset

Because you may want to demo both agents (`ambient` and `standard`) during a presentation without losing session history, the agent's Vertex AI ADK sessions are decoupled from the backend simulation timeline.
- **To reset the simulation clock (set stream back to 0.0)**: Run `task session:reset` in the `72-2026.06-stand-in-agent-backend-sim/` directory.
- **To create a new agent session**: Run `task session:create` in the agent folder (this will generate a fresh persistent session on Vertex AI without deleting past sessions).
- **Do not use `task session:reset` in the agent directory** if you wish to preserve the history of your previous test runs.
