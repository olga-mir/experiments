# Proposal: mock-transcript-streaming-server

## Summary
Implement a lightweight, asynchronous Python FastAPI server that simulates a streaming agent backend. It will expose an SSE endpoint to stream podcast transcript chunks sequentially at fixed intervals.

## Problem
Testing real-time data ingestion for stand-in conference agents requires a stable and predictable source of streaming transcript data.

## Proposed Solution
Use FastAPI's `StreamingResponse` to implement a Server-Sent Events (SSE) stream. The server will iterate through a static dataset of transcript chunks from the Google SRE Prodcast and send them with a configurable delay (defaulting to 30 seconds).

## Capabilities Affected
- mock-streaming-backend: The core streaming logic and SSE endpoint.

## Impact & Risks
- **Improvements:** Provides a reliable mock for frontend and ingestion testing.
- **Edge Cases:** Client disconnects must be handled gracefully.
- **Risks:** Delay logic must be non-blocking to support concurrent connections.
- **Estimated Effort:** Low (single-file FastAPI implementation).

## Out of Scope
- Permanent data storage (uses static JSON/array).
- Authentication or authorization.
- Complex multi-room or multi-speaker tracking beyond the simple sequential stream.
