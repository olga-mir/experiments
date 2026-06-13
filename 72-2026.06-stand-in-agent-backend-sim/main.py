import asyncio
import json
import logging
from pathlib import Path
from typing import AsyncGenerator
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock-streaming-server")

app = FastAPI(
    title="Mock Transcript Streaming Server",
    description="Simulates a streaming podcast transcript backend via SSE"
)

# Enable CORS for ingestion clients
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


async def event_generator(delay: float) -> AsyncGenerator[str, None]:
    chunks = load_transcript()
    if not chunks:
        logger.warning("No transcript chunks to stream. Closing connection immediately.")
        return

    logger.info(f"Started streaming transcript ({len(chunks)} chunks, delay={delay}s).")
    try:
        for idx, chunk in enumerate(chunks):
            # Send SSE event format
            yield f"data: {json.dumps(chunk)}\n\n"
            # Wait for next chunk (unless it's the last one)
            if idx < len(chunks) - 1:
                await asyncio.sleep(delay)
    except asyncio.CancelledError:
        logger.info("Client connection closed/cancelled midway.")
        raise
    except Exception as e:
        logger.error(f"Error during streaming: {e}")
    finally:
        logger.info("Finished streaming transcript.")


@app.get("/stream")
async def stream_transcript(
    delay: float = Query(default=30.0, description="Delay between chunks in seconds", ge=0.0)
):
    """
    Exposes a Server-Sent Events (SSE) endpoint to stream podcast transcript chunks sequentially.
    """
    return StreamingResponse(
        event_generator(delay),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in Nginx reverse proxies
        }
    )


@app.get("/health")
def health_check():
    return {"status": "ok", "chunks_loaded": len(load_transcript())}
