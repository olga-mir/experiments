# Stand-In Agent Attendee

Demo for the talk [AI Agent Conference — Lessons](https://olga-mir.github.io/Public-Speaking/2026.06.24__GDG-Melbourne__AI-Agent-Conference-Lessons/) at GDG Melbourne (June 2026).

An AI agent that attends a conference on your behalf: it monitors a live caption stream and surfaces relevant moments in real time. This folder contains the agents. The companion backend simulator lives in `../72-2026.06-stand-in-agent-backend-sim/`.

---

## Overall architecture

```
┌─────────────────────────────────────────────────────────────┐
│            72-2026.06-stand-in-agent-backend-sim            │
│                                                             │
│  FastAPI server (Cloud Run)                                 │
│  · loads data/transcript.json on startup                    │
│  · releases entries at real wall-clock pace (SIM_SPEED)     │
│                                                             │
│  GET /streams          ← session status (idle/live/finished)│
│  GET /transcript?since ← new caption entries since last ts  │
│  POST /sim/start       ← reset & restart stream             │
│  POST /sim/reset       ← reset to idle                      │
└────────────────────┬────────────────────────────────────────┘
                     │  HTTP (SIMULATION_BASE_URL)
          ┌──────────┴──────────┐
          │                     │
┌─────────▼──────────┐ ┌────────▼───────────────┐
│  ai-attendee-      │ │  ai-attendee-ambient/   │
│  standard/         │ │                         │
│                    │ │  Vertex AI Agent Engine  │
│  Long-running loop │ │  triggered every 5 min  │
│  runs until stream │ │  by Cloud Scheduler      │
│  finishes. Best    │ │  via :streamQuery.       │
│  for playground /  │ │  Persistent session for  │
│  interactive demo. │ │  state across ticks.     │
└────────────────────┘ └─────────────────────────┘
```

Both agents are wired for **simulation mode only** — they call the backend simulator instead of a real ASR service. Set `SIMULATION_MODE=true` and `SIMULATION_BASE_URL` in `.setup-env`.

---

## Repository layout

```
72-2026.06-stand-in-agent-attendee/     ← you are here
├── ai-attendee-standard/               ← reactive long-running agent
│   ├── app/
│   │   ├── agent.py                   # ADK App wrapper
│   │   ├── agent_runtime_app.py       # Agent Engine entry point
│   │   ├── config.py                  # reads .setup-env
│   │   ├── fast_api_app.py            # local webhook server
│   │   └── tools.py                   # get_streams(), get_sim_transcript()
│   ├── Taskfile.yml
│   └── .setup-env                     # local config (not committed)
│
└── ai-attendee-ambient/                ← scheduler-triggered agent
    ├── app/
    │   ├── ambient_agent.py           # agent + system prompt + tools
    │   ├── agent.py
    │   ├── agent_runtime_app.py
    │   ├── config.py
    │   ├── fast_api_app.py
    │   └── tools.py
    ├── Taskfile.yml
    └── .setup-env                     # local config (not committed)

../72-2026.06-stand-in-agent-backend-sim/   ← companion repo
├── main.py                            # FastAPI sim server
├── data/transcript.json               # timed transcript (~12.5 min)
└── Taskfile.yml
```

---

## Agent variants

### `ai-attendee-standard/`

Reactive agent deployed to Vertex AI Agent Engine. Each session runs a continuous loop:

1. Call `get_streams()` — check if the caption stream is live / finished
2. Call `get_sim_transcript(since=<last_ts>)` — fetch new caption entries
3. Analyse for relevant keywords (GKE, GPU, RAG, MCP, agentic SOC, …)
4. Emit alerts to the user; advance `last_ts`
5. Repeat until `status == finished`

Best used via the **Agent Engine playground** for an interactive demo — you send one message and the agent drives itself to completion.

### `ai-attendee-ambient/`

Scheduler-triggered agent deployed to Vertex AI Agent Engine. Cloud Scheduler POSTs a `"tick"` message directly to the Reasoning Engine `:streamQuery` REST endpoint every 5 minutes. Each tick does one sweep, then the agent exits. A **persistent Vertex AI session** carries state (last timestamp seen) across ticks so the agent never re-reads old captions.

Key design details:
- **OAuth (not OIDC):** the `:streamQuery` URL ends in `.googleapis.com`, so Cloud Scheduler must use OAuth. The Taskfile auto-selects this.
- **`input` envelope:** the Reasoning Engine API wraps all method arguments under `"input"`.
- **SA permissions:** the scheduler service account needs `roles/aiplatform.user`.

---

## Quick start

### 1. Start the backend simulator

```bash
cd ../72-2026.06-stand-in-agent-backend-sim
task run              # real-time (12.5 min)
SIM_SPEED=10 task run # 10x — done in ~75 seconds
```

Or deploy to Cloud Run (see the backend sim README).

### 2. Configure an agent

Create `.setup-env` in the agent folder (not committed):

```bash
export GCP_PROJECT_ID=<your-project-id>
export SIMULATION_BASE_URL=<backend-sim-url>   # http://localhost:8000 for local
export SIMULATION_MODE=true
export AGENT_ENGINE_RESOURCE=projects/<project-number>/locations/us-east1/reasoningEngines/<engine-id>
```

### 3. Run locally (standard agent — no deploy needed)

```bash
cd ai-attendee-standard
task install
task run              # one sweep locally
```

### 4. Deploy and use via playground

```bash
task deploy
# Then open Agent Engine → playground → send "Attend the conference and alert me on relevant topics"
```

### 5. Set up ambient agent with Cloud Scheduler

```bash
cd ai-attendee-ambient
task setup:infra      # enable APIs, create service account
task session:create   # create persistent session
AGENT_URL=https://us-east1-aiplatform.googleapis.com/v1/projects/<project-number>/locations/us-east1/reasoningEngines/<engine-id> \
  task schedule       # create cron job (every 5 min)
task logs             # watch agent output
```

---

## Demo flow (presentation)

1. Deploy the backend sim to Cloud Run (or run locally with `SIM_SPEED=10`)
2. Start the standard agent in the playground — it will loop through the full session
3. Optionally run the ambient agent with `SIM_SPEED=1` so ticks arrive naturally every 5 min

**To replay the demo from the beginning:**

```bash
# Reset the simulation clock (in backend-sim dir)
curl -X POST $SIMULATION_BASE_URL/sim/start

# Create a fresh agent session (optional — preserves history of previous runs)
task session:create     # in the agent dir
AGENT_URL=... task schedule  # re-wire scheduler to new session
```

See `AGENTS.md` in this folder for a deeper explanation of the session/simulation reset distinction.

---

## Environment variables reference

| Var | Required | Purpose |
|-----|----------|---------|
| `GCP_PROJECT_ID` | yes | GCP project for deployment |
| `SIMULATION_BASE_URL` | yes | URL of the backend sim (Cloud Run or localhost) |
| `SIMULATION_MODE` | yes | Set to `true` to use sim tools |
| `AGENT_ENGINE_RESOURCE` | ambient only | Reasoning Engine resource name (for persistent sessions) |
| `SIM_SPEED` | backend sim | Time compression multiplier (default `1.0`) |
