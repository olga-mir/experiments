# ai-attendee-ambient

Ambient AI conference attendee agent. Triggered periodically by Cloud Scheduler; each trigger performs one sweep — checks stream status, fetches new captions, emits keyword alerts. Deployed to Vertex AI Agent Engine (agent_runtime).

## Project structure

```
ai-attendee-ambient/
├── app/
│   ├── ambient_agent.py   # Agent definition, tools, system instructions
│   ├── agent.py           # ADK App wrapper
│   ├── agent_runtime_app.py  # Agent Engine deployment entry point
│   ├── fast_api_app.py    # FastAPI webhook server (local dev + trigger endpoint)
│   ├── config.py          # Config from .setup-env
│   └── tools.py           # get_streams(), get_sim_transcript()
├── .setup-env             # Local secrets/config (not committed)
├── agents-cli-manifest.yaml
└── Taskfile.yml
```

## Requirements

- `uv` — `brew install uv`
- `agents-cli` — `uv tool install google-agents-cli`
- `task` — `brew install go-task`
- `gcloud` — authenticated, project set to `gdg-june-playground`

## Configuration (`.setup-env`)

```bash
export GCP_PROJECT_ID=gdg-june-playground
export SIMULATION_BASE_URL=https://mock-transcript-server-471108326825.us-central1.run.app
export SIMULATION_MODE=true
export AGENT_ENGINE_RESOURCE=projects/471108326825/locations/us-east1/reasoningEngines/<engine-id>
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
task deploy           # deploys to Vertex AI Agent Engine (us-east1)
```

After the first deploy, copy the resource name from `deployment_metadata.json`:
```bash
export AGENT_ENGINE_RESOURCE=projects/471108326825/locations/us-east1/reasoningEngines/<new-id>
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

This enables `cloudscheduler.googleapis.com`, `run.googleapis.com`, `aiplatform.googleapis.com`,
creates the `ambient-attendee-scheduler` service account, and grants it `roles/aiplatform.user`.

### 2. Wire up the cron job

The `AGENT_URL` is the Vertex AI Agent Engine base URL for your reasoning engine:

```bash
AGENT_URL=https://us-east1-aiplatform.googleapis.com/v1/projects/471108326825/locations/us-east1/reasoningEngines/<engine-id> \
  task schedule
```

This creates a Cloud Scheduler job (`ambient-cron`) that POSTs to
`<AGENT_URL>/apps/ambient_ai_attendee/trigger/webhook` every 5 minutes using OIDC auth.

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
