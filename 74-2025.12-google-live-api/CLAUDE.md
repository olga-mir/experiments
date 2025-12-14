# Project: Vertex AI Live Audio Transcriber

## Context & Standards
You are acting as a Senior Python Engineer. We are building a modular Python application to experiment with the **Google Vertex AI Multimodal Live API**.

### Tooling & Environment
* **Package Manager:** Always use `uv` for dependency management and script execution. Do not create a manual `venv`; allow `uv` to manage it.
* **Task Management:** specific tasks (setup, dev, run) must be defined in a `Taskfile.yml`.
* **Configuration:** All variable data (GCP Project ID, Region, Model Names) must be loaded from environment variables (`.env`).
* **SDK:** Use the new `google-genai` Python SDK which supports both Vertex AI and Gemini Developer APIs.

## The Objective
Build a CLI application that records audio from the microphone (up to 5 minutes) and streams it to the Vertex AI Live API.

**Core Functionality (MVP):**
1.  Connect to the Vertex AI Live API using a WebSocket.
2.  Stream audio from the local microphone in real-time.
3.  Receive text responses.
4.  **Smart Transcription:** The model must be configured (via System Instructions) to output coherent, clean text. It must aggressively filter out filler words ("um", "ah", "like") and fix stutters *before* returning the text.

## Source Context
The file `src/main.py` contains raw example code derived from: `https://ai.google.dev/gemini-api/docs/live?example=mic-stream`.

## Instructions

### 1. Project Initialization
* Initialize a standard python project structure using `uv init`.
* Add necessary dependencies: `google-genai`, `pyaudio` (for mic input), and `python-dotenv`.
* Ensure `src/` is a proper python package.

### 2. Configuration Setup
* Create a `.env.example` file.
* Required variables: `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_REGION` (default: `us-central1`), `MODEL_ID` (default: `gemini-2.0-flash-exp`).

### 3. Code Refactoring
Refactor the existing `src/main.py` into a clean, object-oriented structure:
* **`AudioRecorder` class:** Handles PyAudio stream (opening, reading chunks, closing).
* **`LiveSession` class:** Handles the `google-genai` client connection, WebSocket management, and sending/receiving messages.
* **Entrypoint:** Ensure the main loop handles graceful shutdowns (Ctrl+C).

### 4. Developer Experience (Taskfile)
Create a `Taskfile.yml` with the following tasks:
* `setup`: Install system dependencies (portaudio) if needed, and run `uv sync`.
* `run`: Run the application using `uv run python src/main.py`.
* `lint`: Basic linting check.

### 5. Prompting Strategy
In the `LiveSession` setup, inject a specific system prompt to the model: "You are a professional transcriber. Your output should be a clean, readable transcript of the audio. Remove all filler words, stutters, and verbal tics. output text only."

Proceed to scaffolding the project and refactoring the code.
