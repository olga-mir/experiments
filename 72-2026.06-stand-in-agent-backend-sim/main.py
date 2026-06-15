import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock-transcript-server")

app = FastAPI(
    title="Mock Transcript Server",
    description="Serves a conference transcript progressively, simulating a live stream."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = Path(__file__).parent / "data" / "transcript.json"


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def load_transcript() -> list:
    if not DATA_PATH.exists():
        logger.error(f"Transcript file not found at {DATA_PATH}")
        return []
    try:
        with open(DATA_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading transcript JSON: {e}")
        return []


# ---------------------------------------------------------------------------
# Simulation state — single client, no scale-to-zero between calls
# ---------------------------------------------------------------------------

class _SimState:
    def __init__(self):
        self._started_at: datetime | None = None
        self.speed: float = 1.0

    def start(self, speed: float = 1.0):
        self._started_at = datetime.now(timezone.utc)
        self.speed = speed
        logger.info(f"Simulation started at {self._started_at.isoformat()} speed={speed}x")

    def reset(self):
        self._started_at = None
        self.speed = 1.0
        logger.info("Simulation reset")

    @property
    def started_at(self) -> datetime | None:
        return self._started_at

    def _elapsed_sim_seconds(self) -> float:
        if self._started_at is None:
            return 0.0
        wall = (datetime.now(timezone.utc) - self._started_at).total_seconds()
        return wall * self.speed

    def status(self, entries: list) -> str:
        if self._started_at is None:
            return "idle"
        if not entries:
            return "finished"
        first_ts = _parse_ts(entries[0]["ts"])
        last_ts = _parse_ts(entries[-1]["ts"])
        total = (last_ts - first_ts).total_seconds()
        return "finished" if self._elapsed_sim_seconds() >= total else "live"

    def available(self, entries: list) -> list:
        """Return entries whose simulated timestamp has arrived."""
        if self._started_at is None or not entries:
            return []
        elapsed = self._elapsed_sim_seconds()
        first_ts = _parse_ts(entries[0]["ts"])
        return [
            e for e in entries
            if (_parse_ts(e["ts"]) - first_ts).total_seconds() <= elapsed
        ]


_sim = _SimState()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/streams")
def get_streams():
    """
    Returns the current simulation status.

    Status values:
    - "idle"     — simulation not yet started (call POST /sim/start first)
    - "live"     — transcript is streaming, more entries will appear on future polls
    - "finished" — all entries have been served; produce your final summary
    """
    entries = load_transcript()
    status = _sim.status(entries)
    response = {
        "status": status,
        "stream_id": "main",
        "captions_url": "/transcript",
    }
    if _sim.started_at:
        response["started_at"] = _sim.started_at.isoformat()
        response["speed"] = _sim.speed
    return response


@app.get("/transcript")
def get_transcript(
    since: str = Query(default="", description="ISO 8601 timestamp; return only entries after this time")
):
    """
    Returns transcript entries that have arrived so far in simulation time.

    Use ?since=<ISO8601> to poll incrementally — pass the `ts` of the last
    entry you received and you will only get new ones. Returns an empty list
    when there are no new entries yet (the session may still be live).
    """
    entries = load_transcript()
    visible = _sim.available(entries)
    if since:
        visible = [e for e in visible if e.get("ts", "") > since]
    return visible


@app.post("/sim/start")
def sim_start(speed: float = Query(default=1.0, description="Playback speed multiplier (e.g. 60 = 1 min of content per real second)")):
    """Start the simulation clock. Use speed>1 to accelerate playback for testing."""
    if _sim.started_at is not None:
        return {"status": "already_running", "message": "Call POST /sim/reset first to restart."}
    _sim.start(speed=speed)
    entries = load_transcript()
    total = 0.0
    if len(entries) >= 2:
        total = (_parse_ts(entries[-1]["ts"]) - _parse_ts(entries[0]["ts"])).total_seconds()
    return {
        "status": "started",
        "speed": speed,
        "total_sim_seconds": total,
        "expected_wall_seconds": round(total / speed, 1),
    }


@app.post("/sim/reset")
def sim_reset():
    """Reset the simulation back to idle so it can be restarted."""
    _sim.reset()
    return {"status": "idle"}


@app.get("/health")
def health_check():
    entries = load_transcript()
    return {
        "status": "ok",
        "total_entries": len(entries),
        "sim_status": _sim.status(entries),
    }
