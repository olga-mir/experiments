# Introduction

Build tiny smart transcribe app with Google Live API

https://ai.google.dev/gemini-api/docs/live?example=mic-stream

# Usage

1. Configure your environment: `cp .env.example .env` and edit with your values

2. Run the setup:
```
$ task setup
```

3. Run the transcriber:
```
$ task run
```

  The app will:
  - Connect to the Vertex AI Live API
  - Stream audio from your microphone
  - Display clean transcriptions in real-time (with filler words removed)
  - Stop gracefully with Ctrl+C

# Project Structure

```
  74-2025.12-google-live-api/
  ├── .env.example          # Configuration template
  ├── Taskfile.yml          # Task automation (setup, run, lint, clean)
  ├── pyproject.toml        # Project metadata (created by uv)
  ├── src/
  │   ├── __init__.py       # Package initialization
  │   └── main.py           # Refactored OOP implementation
  └── CLAUDE.md             # Updated with monorepo structure
```

# Key Features

**AudioRecorder class**:
  - Manages PyAudio stream lifecycle
  - Captures microphone input and queues it for streaming
  - Handles graceful cleanup

**LiveSession class**:
  - Connects to Vertex AI using google-genai SDK
  - Configured for TEXT responses (not audio)
  - Includes smart transcription system prompt that filters filler words

**Config class**:
  - Loads all settings from environment variables
  - Provides sensible defaults

