# Spec: mock-streaming-backend

## Overview
Implements a lightweight FastAPI server that provides a Server‑Sent Events (SSE) endpoint streaming transcript chunks at configurable intervals.

### Requirement: Stream Transcript Chunks

**Context:** The client expects a continuous stream of JSON lines representing transcript snippets.

#### Scenario: Normal Streaming
- **Given** a list of transcript chunks is available
- **When** a client connects to `/stream`
- **Then** the server sends each chunk as a JSON object followed by a newline, waiting `delay_seconds` (default 30 s) between chunks.

#### Scenario: Client Disconnect
- **Given** a client is connected to `/stream`
- **When** the client disconnects before all chunks are sent
- **Then** the server stops streaming without raising an unhandled exception.

#### Scenario: Empty Transcript
- **Given** the transcript list is empty
- **When** a client connects to `/stream`
- **Then** the server immediately closes the stream.

## Non‑Functional Requirements
- **Performance:** Streaming must be non‑blocking; use asynchronous iteration.
- **Scalability:** Support multiple concurrent connections.
- **Reliability:** Handle abrupt client termination gracefully.
