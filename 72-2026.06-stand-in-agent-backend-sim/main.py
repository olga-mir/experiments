import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock-transcript-server")

DATA_PATH = Path(__file__).parent / "data" / "transcript.json"


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def load_transcript() -> dict:
    """Load transcript from JSON; supports both old flat-array format and new object format."""
    if not DATA_PATH.exists():
        logger.error(f"Transcript file not found at {DATA_PATH}")
        return {"entries": []}
    try:
        raw = json.loads(DATA_PATH.read_text())
        if isinstance(raw, list):
            return {"session_name": "Live Session", "track_id": "main", "entries": raw}
        return raw
    except Exception as e:
        logger.error(f"Error reading transcript JSON: {e}")
        return {"entries": []}


# ---------------------------------------------------------------------------
# Simulation state — single client, no scale-to-zero between calls
# ---------------------------------------------------------------------------

class _SimState:
    def __init__(self):
        self._started_at: datetime | None = None
        self.speed: float = 1.0
        self._data: dict = {"entries": []}

    def start(self, speed: float = 1.0):
        self._started_at = datetime.now(timezone.utc)
        self.speed = speed
        self._data = load_transcript()
        logger.info(
            f"Simulation started at {self._started_at.isoformat()} "
            f"speed={speed}x  entries={len(self._data['entries'])}"
        )

    def reset(self):
        self._started_at = None
        self.speed = 1.0
        self._data = {"entries": []}
        logger.info("Simulation reset")

    @property
    def started_at(self) -> datetime | None:
        return self._started_at

    @property
    def entries(self) -> list:
        return self._data.get("entries", [])

    @property
    def session_name(self) -> str:
        return self._data.get("session_name", "Live Session")

    @property
    def track_id(self) -> str:
        return self._data.get("track_id", "main")

    def _elapsed_seconds(self) -> float:
        if self._started_at is None:
            return 0.0
        return (datetime.now(timezone.utc) - self._started_at).total_seconds() * self.speed

    def status(self) -> str:
        if self._started_at is None:
            return "idle"
        entries = self.entries
        if not entries:
            return "finished"
        total = entries[-1]["end_time"] - entries[0]["start_time"]
        return "finished" if self._elapsed_seconds() >= total else "live"

    def _ts_for_entry(self, entry: dict) -> str:
        """Return wall-clock ISO timestamp for when this entry is 'spoken'."""
        offset = entry["start_time"] - self.entries[0]["start_time"]
        real_offset = offset / self.speed
        wall_ts = self._started_at + timedelta(seconds=real_offset)
        return wall_ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{wall_ts.microsecond // 1000:03d}Z"

    def available_since(self, since: str = "") -> list[dict]:
        """Return entries that have arrived in wall-clock time, optionally filtered by since."""
        if self._started_at is None:
            return []
        elapsed = self._elapsed_seconds()
        entries = self.entries
        if not entries:
            return []
        first_start = entries[0]["start_time"]
        visible = []
        for e in entries:
            offset = e["start_time"] - first_start
            if offset <= elapsed:
                item = {
                    "ts": self._ts_for_entry(e),
                    "speaker": e.get("speaker", ""),
                    "text": e["text"],
                }
                visible.append(item)
        if since:
            visible = [item for item in visible if item["ts"] > since]
        return visible


_sim = _SimState()


# ---------------------------------------------------------------------------
# Auto-start on server startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    speed = float(os.environ.get("SIM_SPEED", "1.0"))
    _sim.start(speed=speed)
    yield


app = FastAPI(
    title="Mock Transcript Server",
    description="Serves a conference transcript progressively, simulating a live stream.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/streams")
def get_streams():
    """
    Returns the current simulation status.

    Status values:
    - "idle"     — simulation not yet started
    - "live"     — transcript is streaming, more entries will appear on future polls
    - "finished" — all entries have been served; produce your final summary
    """
    status = _sim.status()
    response = {
        "status": status,
        "stream_id": _sim.track_id,
        "session_name": _sim.session_name,
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

    Timestamps in each entry reflect real wall-clock time anchored to when the
    simulation started, so you can use `since` to poll incrementally.
    Pass the `ts` of the last entry you received; you will only get new ones.
    Returns an empty list when there are no new entries yet (session may still be live).
    """
    return _sim.available_since(since)


@app.post("/sim/start")
def sim_start(speed: float = Query(default=1.0, description="Playback speed multiplier")):
    """Start (or restart) the simulation clock. Resets any prior state."""
    _sim.reset()
    _sim.start(speed=speed)
    entries = _sim.entries
    total = entries[-1]["end_time"] - entries[0]["start_time"] if len(entries) >= 2 else 0.0
    return {
        "status": "started",
        "speed": speed,
        "total_sim_seconds": total,
        "expected_wall_seconds": round(total / speed, 1),
        "entries": len(entries),
    }


@app.post("/sim/reset")
def sim_reset():
    """Reset the simulation back to idle."""
    _sim.reset()
    return {"status": "reset"}


@app.get("/health")
def health_check():
    entries = _sim.entries
    return {
        "status": "ok",
        "sim_status": _sim.status(),
        "total_entries": len(entries),
        "session_name": _sim.session_name,
        "speed": _sim.speed,
    }
