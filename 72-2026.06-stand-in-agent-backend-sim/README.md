# Mock Transcript Streaming Server

A lightweight FastAPI-based mock server that simulates an asynchronous transcript stream. Useful for testing ingestion clients and frontend interfaces that expect real-time transcription feeds via Server-Sent Events (SSE).

## Requirements

- Python >= 3.14
- `uv` package manager

## Quick Start

1. Install dependencies:
   ```bash
   task init
   ```
   *or manually:*
   ```bash
   uv sync
   ```

2. Start the local server:
   ```bash
   task run
   ```
   *or manually:*
   ```bash
   uv run uvicorn main:app --reload --port 8000
   ```

## Endpoints

### `GET /stream`

Streams transcript chunks sequentially as Server-Sent Events (`text/event-stream`).

- **Query Parameters:**
  - `delay` (float, optional): Time delay between streaming each transcript chunk in seconds. Defaults to `30.0`.

- **Example Usage:**
  ```bash
  curl -N "http://localhost:8000/stream?delay=2"
  ```

### `GET /health`

Returns a basic health check showing application status and the count of preloaded transcript chunks.
