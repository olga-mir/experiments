# Stand-In Agent Backend Simulator

FastAPI server that simulates a live conference transcript stream. Consumed by agents in `72-2026.06-stand-in-agent-attendee`. Deployed to Cloud Run.

## How it works

Loads `data/transcript.json` on startup and auto-starts the simulation. Entries are released progressively based on elapsed wall-clock time — each entry has `start_time`/`end_time` in seconds. A `SIM_SPEED` env var (default `1.0`) compresses time: `SIM_SPEED=10` plays a 12.5-minute podcast in ~75 seconds.

## Endpoints agents use

| Endpoint | Purpose |
|----------|---------|
| `GET /streams` | Returns session status: `idle` / `live` / `finished` |
| `GET /transcript?since=<ISO8601>` | Returns entries that have arrived so far; pass last `ts` to get only new ones |

## Control endpoints (test harness)

| Endpoint | Purpose |
|----------|---------|
| `POST /sim/start?speed=<float>` | Reset + restart simulation at given speed |
| `POST /sim/reset` | Reset to idle |
| `POST /sim/kill` | Flip status to `idle` mid-stream (tests the agent's killswitch handling) |
| `GET /health` | Returns status, entry count, current speed |

## Dev workflow

```bash
task run                  # real-time (12.5 min)
SIM_SPEED=60 task run     # 60x speed — full podcast in ~12 seconds

# Deploy to Cloud Run
GCP_PROJECT_ID=<proj> task deploy

# Accelerated deploy (useful for agent integration tests)
SIM_SPEED=10 GCP_PROJECT_ID=<proj> task deploy
```

## Transcript data

`data/transcript.json` — 63 entries from Google Cloud Security Podcast EP278, timed at ~150 WPM with 1.5s gaps (~12.5 min total).

## Key constraint

Single-track, single-client design. No auth. CORS open. Intended for local or private Cloud Run use only.
