# Copyright 2026 Google LLC
import datetime
import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request

from .config import config

def _get(url: str) -> tuple[int, str]:
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "AgentPass/1.0")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return 0, f"Error: {e}"


def get_live_streams() -> dict:
    """Returns the current live stream status for all rooms at the conference.

    Poll this first to discover which rooms are currently streaming. The response
    includes a `live_stream_ids` list (rooms active right now) and per-stream
    status (`live`, `connecting`, or `idle`), plus captions_url and screen_url
    for each live stream.
    """
    status, body = _get(f"{config.base_url}/streams.json")
    if status != 200:
        return {"error": body}
    try:
        return json.loads(body)
    except Exception:
        return {"raw": body}


def get_captions(stream_id: str, since: str = "") -> dict:
    """Returns recent captions (last ~200 lines) for a live stream room.

    Use `since` (ISO 8601 timestamp, e.g. '2026-06-03T09:31:00Z') to get only
    new lines since your last poll. Remember the `ts` of the last line you saw
    and pass it back each time. Polls every ~60s for follow-along; ~15s for
    real-time reactions.

    Args:
        stream_id: Room identifier
        since: Optional ISO 8601 timestamp to fetch only captions after this time
    """
    url = f"{config.base_url}/{stream_id}/captions.json"
    if since:
        url += f"?since={urllib.parse.quote(since)}"
    status, body = _get(url)
    if status == 404:
        return {"status": "no_captions", "message": "Session not yet started or already ended."}
    if status != 200:
        return {"error": body}
    try:
        return json.loads(body)
    except Exception:
        return {"raw": body}


def get_current_screen(stream_id: str) -> dict:
    """Returns a semantic-markdown description of what's currently on screen in a room.

    Includes slide content, bullet points, and code (verbatim); diagrams are
    described in [brackets]. Refreshes ~every 15s while live. Compare
    `captured_at` to your previous read to detect changes. Returns
    `[speaker camera — no slide content]` when camera is on the speaker.

    Args:
        stream_id: Room identifier
    """
    url = f"{config.base_url}/{stream_id}/screen.json"
    status, body = _get(url)
    if status == 404:
        return {"status": "no_screen", "message": "No active session or screen capture unavailable."}
    if status != 200:
        return {"error": body}
    try:
        return json.loads(body)
    except Exception:
        return {"raw": body}


def get_program() -> str:
    """Fetches the full conference program (schedule, talks, speakers).

    Use this to look up talk titles, speaker names, session times, and room assignments.
    Cross-reference with get_live_streams() to know which talks are happening right now.
    """
    status, body = _get(config.program_url)
    if status != 200:
        return f"Error fetching program: {body}"
    return body


def list_past_sessions(stream_id: str) -> dict:
    """Lists all completed (archived) sessions for a given room.

    Use this to find sessions you missed and their IDs for get_session_transcript().

    Args:
        stream_id: Room identifier
    """
    url = f"{config.base_url}/{stream_id}/sessions.json"
    status, body = _get(url)
    if status == 404:
        return {"sessions": [], "message": "No archived sessions yet."}
    if status != 200:
        return {"error": body}
    try:
        return json.loads(body)
    except Exception:
        return {"raw": body}


def get_session_transcript(stream_id: str, session_id: str) -> str:
    """Returns the full transcript and slide timeline for a completed session.

    Use list_past_sessions() first to get valid session IDs.

    Args:
        stream_id: Room identifier
        session_id: Session ID from list_past_sessions()
    """
    url = f"{config.base_url}/{stream_id}/sessions/{session_id}.md"
    status, body = _get(url)
    if status == 404:
        return f"Session {session_id} not found in {stream_id}."
    if status != 200:
        return f"Error fetching session: {body}"
    return body


def checkin(note: str = "") -> dict:
    """Checks in to the conference as an AI agent attendee.

    Optional but recommended at session start — lets the organisers know
    you're attending. Returns a welcome message with current live stream status.

    Args:
        note: Optional note about what you're here to do or who you're helping
    """
    import os
    agent_name = config.agent_name
    on_behalf_of = config.on_behalf_of

    payload = json.dumps({
        "agent": agent_name,
        "on_behalf_of": on_behalf_of,
        "note": note
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            config.checkin_url,
            data=payload,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "AgentPass/1.0")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def get_streams() -> dict:
    """Returns the current simulation status.

    Call this first each polling cycle to check whether the session is live.

    Status values:
    - "idle"     — simulation not yet started; check back in ~30 seconds
    - "live"     — session is streaming; call get_sim_transcript() for captions
    - "finished" — all content has been served; produce your final summary and stop polling
    """
    sim_url = config.simulation_base_url
    if not sim_url:
        return {"error": "SIMULATION_BASE_URL not configured. Set SIMULATION_BASE_URL in .setup-env."}

    status, body = _get(f"{sim_url}/streams")
    if status != 200:
        return {"error": body}
    try:
        return json.loads(body)
    except Exception:
        return {"raw": body}


def get_sim_transcript(since: str = "") -> dict:
    """Fetches new transcript entries from the simulator since your last poll.

    The simulator releases entries progressively — polling again will return
    entries that have arrived since your last call. Pass the `ts` of the last
    entry you received as `since` to get only new lines.

    Returns an empty list when no new entries have arrived yet (session may
    still be live — check get_streams() status).

    Args:
        since: ISO 8601 timestamp (e.g. '2026-06-03T09:00:10.000Z'); omit on first call
    """
    sim_url = config.simulation_base_url
    if not sim_url:
        return {"error": "SIMULATION_BASE_URL not configured. Set SIMULATION_BASE_URL in .setup-env."}

    url = f"{sim_url}/transcript"
    if since:
        url += f"?since={urllib.parse.quote(since)}"

    status, body = _get(url)
    if status != 200:
        return {"error": body}
    try:
        entries = json.loads(body)
        return {"entries": entries}
    except Exception:
        return {"raw": body}


def save_screenshot_to_bucket(stream_id: str) -> dict:
    """Downloads the current live screenshot for the given stream and uploads it to the configured Google Cloud Storage bucket.

    The screenshot is stored with a unique name based on the capture timestamp
    (e.g., stream_id/YYYY-MM-DDTHH-MM-SS.sssZ.jpg) to prevent overwriting.

    Args:
        stream_id: Room identifier
    """
    from google.cloud import storage
    # config is already imported at module level

    bucket_name = config.screenshots_bucket_name
    if not bucket_name:
        return {"error": "SCREENSHOTS_BUCKET_NAME environment variable is not configured."}

    # 1. Fetch current screen metadata to get capture timestamp and filename
    screen_meta = get_current_screen(stream_id)
    if "error" in screen_meta:
        return {"error": f"Failed to retrieve screen metadata: {screen_meta['error']}"}
    if screen_meta.get("status") == "no_screen":
        return {"error": f"No active screen to capture: {screen_meta.get('message')}"}

    captured_at = screen_meta.get("captured_at")
    frame_key = screen_meta.get("frame_key", "screen.jpg")
    if not captured_at:
        return {"error": "Screen metadata does not contain capture timestamp ('captured_at')."}

    # 2. Build the screenshot download URL
    image_url = f"{config.base_url}/{stream_id}/{frame_key}"

    # 3. Download the image bytes
    try:
        req = urllib.request.Request(image_url)
        req.add_header("User-Agent", "AgentPass/1.0")
        with urllib.request.urlopen(req, timeout=10) as resp:
            image_data = resp.read()
            content_type = resp.headers.get("Content-Type", "image/jpeg")
    except Exception as e:
        return {"error": f"Failed to download image from {image_url}: {e}"}

    # 4. Upload to Cloud Storage
    try:
        # Sanitize captured_at to make a safe filename
        safe_timestamp = captured_at.replace(":", "-").replace(" ", "_")
        gcs_filename = f"{stream_id}/{safe_timestamp}.jpg"

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(gcs_filename)
        blob.upload_from_string(image_data, content_type=content_type)

        gcs_uri = f"gs://{bucket_name}/{gcs_filename}"
        return {
            "status": "success",
            "message": f"Successfully uploaded screenshot to {gcs_uri}",
            "gcs_uri": gcs_uri,
            "captured_at": captured_at,
            "stream_id": stream_id
        }
    except Exception as e:
        return {"error": f"Failed to upload to GCS bucket {bucket_name}: {e}"}

