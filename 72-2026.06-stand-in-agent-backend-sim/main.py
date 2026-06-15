import json
import logging
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock-transcript-server")

app = FastAPI(
    title="Mock Transcript Server",
    description="Serves a conference transcript as a JSON array of {ts, text} entries"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = Path(__file__).parent / "data" / "transcript.json"


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


@app.get("/transcript")
def get_transcript(
    since: str = Query(default="", description="ISO 8601 timestamp; return only entries after this time")
):
    """
    Returns transcript entries as a JSON array of {ts, text} objects.
    Use ?since=<ISO8601> to get only entries after a given timestamp (for incremental polling).
    Timestamps compare lexicographically so plain string comparison works for UTC/Z-suffixed values.
    """
    entries = load_transcript()
    if since:
        entries = [e for e in entries if e.get("ts", "") > since]
    return entries


@app.get("/health")
def health_check():
    return {"status": "ok", "total_entries": len(load_transcript())}
