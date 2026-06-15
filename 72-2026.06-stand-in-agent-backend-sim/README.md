# Mock Transcript Streaming Server

A lightweight FastAPI server that simulates a live conference transcript stream. It serves one room's worth of captions progressively, releasing entries in real time (or accelerated time) anchored to when the server started. Designed to test stand-in AI attendee agents without needing a real conference stream.

This server is deployed to Cloud Run and consumed by agents in the same repo under `72-2026.06-stand-in-agent-attendee`.

## How it works

The simulation starts automatically when the server boots. It loads `data/transcript.json` and releases entries based on elapsed wall-clock time. A `speed` multiplier (env var `SIM_SPEED`, default `1.0`) lets you compress time for testing — `SIM_SPEED=10` plays a 12-minute podcast in ~75 seconds.

Timestamps on returned entries are anchored to the real wall-clock time the server started, so polling clients can use `since=<ts>` to fetch only new entries across successive calls.

## Requirements

- Python >= 3.11
- `uv` package manager
- `task` (Taskfile runner)

## Running locally

```bash
task run                    # real-time speed
SIM_SPEED=60 task run       # 60x — full podcast in ~12 seconds
```

## Endpoints

### `GET /streams`

Returns current session status. Poll this first each cycle.

```json
{
  "status": "live",
  "stream_id": "main",
  "session_name": "Cloud Security Podcast Ep 278: ...",
  "captions_url": "/transcript",
  "started_at": "2026-06-16T10:00:00.000Z",
  "speed": 1.0
}
```

Status values:
- `"live"` — entries are being released; poll `/transcript` for captions
- `"finished"` — all entries served; produce final summary and stop polling

### `GET /transcript?since=<ISO8601>`

Returns transcript entries that have arrived so far. Each entry includes a real wall-clock `ts` timestamp, so you can pass the last `ts` you saw as `since` to get only new lines.

```json
[
  {
    "ts": "2026-06-16T10:00:00.000Z",
    "speaker": "Tim",
    "text": "Welcome to the Cloud Security Podcast by Google..."
  }
]
```

Returns an empty list when no new entries have arrived yet (session may still be live).

### `POST /sim/start?speed=<float>`

Resets and restarts the simulation with the given speed multiplier. Useful for replaying mid-session.

### `POST /sim/reset`

Resets the simulation to idle.

### `GET /health`

Returns sim status, entry count, and current speed.

## Deployment

```bash
# Real-time playback (12.5 min podcast plays in 12.5 min)
GCP_PROJECT_ID=my-project task deploy

# Accelerated playback (10x — useful for agent testing)
SIM_SPEED=10 GCP_PROJECT_ID=my-project task deploy
```

## Data

`data/transcript.json` — 63 speaker-attributed entries generated from the podcast debrief below, timed at ~150 WPM with a 1.5s gap between speakers (~12.5 minutes total).

`data/google-security-podcast-ep278-raw.txt` — source debrief copied from [Google Cloud Security Podcast EP278: The Agentic SOC: Are We Measuring Time Saved or Risk Reduced?](https://cloud.withgoogle.com/cloudsecurity/podcast/ep278-the-agentic-soc-are-we-measuring-time-saved-or-risk-reduced/)
