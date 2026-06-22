# ai-attendee-ambient

Ambient AI conference attendee agent. Triggered periodically by Cloud Scheduler; each trigger performs one sweep — checks stream status, fetches new captions, emits keyword alerts. Deployed to Vertex AI Agent Engine (agent_runtime).

## Project structure

```
ai-attendee-ambient/
├── app/
│   ├── ambient_agent.py      # Agent definition, tools, system instructions
│   ├── agent.py              # ADK App wrapper
│   ├── agent_runtime_app.py  # Agent Engine deployment entry point
│   ├── fast_api_app.py       # FastAPI webhook server (local dev + trigger endpoint)
│   ├── config.py             # Config from .setup-env
│   └── tools.py              # get_streams(), get_sim_transcript()
├── .setup-env                # Local secrets/config (not committed)
├── .ambient_session_id       # Persistent session ID (git-ignored, created by task session:create)
├── agents-cli-manifest.yaml
└── Taskfile.yml
```

## Requirements

- `uv` — `brew install uv`
- `agents-cli` — `uv tool install google-agents-cli`
- `task` — `brew install go-task`
- `gcloud` — authenticated, project set to your GCP project

## Configuration (`.setup-env`)

```bash
export GCP_PROJECT_ID=<your-project-id>
export SIMULATION_BASE_URL=<cloud-run-url-from-backend-sim-deploy>
export SIMULATION_MODE=true
export AGENT_ENGINE_RESOURCE=projects/<project-number>/locations/us-east1/reasoningEngines/<engine-id>
```

`AGENT_ENGINE_RESOURCE` enables persistent sessions across Scheduler ticks (VertexAiSessionService).
Without it the agent falls back to in-memory sessions — fine for local testing.

## Local development

```bash
task install          # install deps

# Option 1: one-shot run (no server needed)
task run              # agents-cli run "Perform a sweep of the conference"

# Option 2: webhook server + manual trigger
task server           # starts FastAPI on localhost:8000
task trigger          # in another terminal — POSTs a tick to the local webhook
```

## Deployment

```bash
task deploy
```

After the first deploy, copy the resource name from `deployment_metadata.json`:
```bash
export AGENT_ENGINE_RESOURCE=projects/<project-number>/locations/us-east1/reasoningEngines/<new-id>
```
Add it to `.setup-env`, then redeploy so the agent picks up persistent sessions:
```bash
task deploy
```

### Testing the deployed agent

Open the Agent Engine playground in the GCP console and send:
> `Perform a sweep of the conference`

The agent should call `get_streams()` then `get_sim_transcript()`. Make sure the sim backend
is running first (see below).

## Cloud Scheduler setup (one-time)

### 1. Enable APIs and create the service account

```bash
task setup:infra
```

Enables `cloudscheduler.googleapis.com`, `run.googleapis.com`, `aiplatform.googleapis.com`,
creates the `ambient-attendee-scheduler` service account, and grants it `roles/aiplatform.user`
(required to call `:streamQuery` on the Reasoning Engine).

### 2. Create a persistent session

The agent needs a session to exist before the scheduler can reuse it for continuity across ticks.

```bash
task session:create
```

This calls the Agent Engine sessions API, creates a session for `user_id=scheduler`, and saves
the session ID to `.ambient_session_id`. The `schedule` task reads this file automatically.

### 3. Wire up the cron job

`AGENT_URL` is the Vertex AI Agent Engine base resource URL (v1, not v1beta1):

```bash
export AGENT_URL=https://us-east1-aiplatform.googleapis.com/v1/projects/<project-number>/locations/us-east1/reasoningEngines/<engine-id>
task schedule
```

This creates (or updates) a Cloud Scheduler job (`ambient-cron`) that POSTs to
`<AGENT_URL>:streamQuery` every 5 minutes with OAuth auth. The request body includes
the session ID from `.ambient_session_id` so each tick continues the same session.

**Why OAuth (not OIDC):** Cloud Scheduler's OAuth token auth requires the target URL to end
in `.googleapis.com`. OIDC is used automatically by the Taskfile when targeting Cloud Run URLs.

**Request body format** (set by the Taskfile):
```json
{"input": {"message": "tick", "user_id": "scheduler", "session_id": "<session-id>"}}
```

The `input` envelope is required by the Reasoning Engine REST API — method arguments are
not passed at the top level.

### Viewing agent output

```bash
task logs             # last 50 log lines from the Reasoning Engine
task logs -- 100      # more lines
```

Logs appear in `aiplatform.googleapis.com/reasoning_engine_stderr` in Cloud Logging.

## Session management

| Command | Purpose |
|---------|---------|
| `task session:create` | Create a new session, save ID to `.ambient_session_id` |
| `task session:list` | List all sessions for `user_id=scheduler` |
| `task session:reset` | Delete current session and create a fresh one (use between test runs), then re-run `task schedule` |

After `session:reset`, re-run `task schedule` to update the scheduler with the new session ID:
```bash
task session:reset
AGENT_URL=... task schedule
```

## Sim backend

The sim backend is deployed separately at `SIMULATION_BASE_URL`. Check its status:

```bash
curl $SIMULATION_BASE_URL/streams
```

If it shows `"idle"` (scale-to-zero after inactivity), restart it:

```bash
curl -X POST $SIMULATION_BASE_URL/sim/start
```

Source: `72-2026.06-stand-in-agent-backend-sim/`
