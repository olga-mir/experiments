# Vertex AI Live Audio Conversation App

A Python CLI application that enables real-time voice conversations with Google's Gemini 2.5 Flash Native Audio model via Vertex AI.

## Features

- **Real-time voice conversations**: Speak naturally and get audio responses
- **Native audio processing**: Uses `gemini-live-2.5-flash-native-audio` model
- **Automatic turn detection**: Voice Activity Detection (VAD) handles conversation flow
- **Bi-directional audio**: Captures microphone input and plays model responses
- **Clean architecture**: Object-oriented design with AudioRecorder and LiveSession classes

## Quick Start

1. **Setup environment:**
   ```bash
   cp .env.example .env
   # Edit .env and set your GOOGLE_CLOUD_PROJECT
   ```

2. **Install and run:**
   ```bash
   task setup  # Installs dependencies
   task run    # Starts the application
   ```

3. **Use the app:**
   - Speak your question clearly
   - Wait for 2-3 seconds of silence after finishing
   - Listen to the model's audio response through your speakers

## Project Structure

```
74-2025.12-google-live-api/
├── .env.example          # Configuration template
├── Taskfile.yml          # Task automation (setup, run, lint, clean)
├── pyproject.toml        # Project metadata
├── src/
│   ├── __init__.py       # Package initialization
│   └── main.py           # Main application (AudioRecorder, LiveSession)
├── transcribe-snippet.md # Reference for text transcription mode
└── CLAUDE.md             # Project context for AI assistants
```

## Architecture

### Core Components

**Config**
- Environment-based configuration
- Loads GCP project, region, model settings
- Configures system instructions for the model

**AudioRecorder**
- Handles microphone capture via PyAudio
- 16kHz mono PCM audio input
- Queues audio chunks for streaming

**LiveSession**
- Manages Vertex AI connection
- Streams audio to and from the model
- Handles audio playback (24kHz output)

### Audio Flow

```
Microphone (16kHz) → AudioRecorder → Queue → send_audio() → Vertex AI
                                                                  ↓
Speaker (24kHz) ← play_audio() ← Queue ← receive_responses()
```

## Configuration

Environment variables (`.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_CLOUD_PROJECT` | Your GCP project ID | (required) |
| `GOOGLE_CLOUD_REGION` | Vertex AI region | `us-central1` |
| `MODEL_ID` | Model name | `gemini-live-2.5-flash-native-audio` |
| `CHUNK_SIZE` | Audio chunk size | `1024` |
| `SAMPLE_RATE` | Input sample rate (Hz) | `16000` |

## How It Works

1. **Connection**: Establishes WebSocket connection to Vertex AI Live API
2. **Voice Activity Detection**: Model automatically detects when you finish speaking
3. **Turn-based conversation**:
   - You speak → model listens
   - Silence detected → model responds
   - Model responds → you can speak again
4. **Audio playback**: Model's audio response plays through your default output device

## Development

### Available Tasks

```bash
task --list
```

### System Requirements

- macOS (uses Homebrew for portaudio)
- Python 3.14+
- Audio input device (microphone)
- Audio output device (speakers/headphones)

## Next Steps: Text Transcription Mode

The current implementation uses audio-to-audio conversation. For text transcription of conversations, see `transcribe-snippet.md` for configuration using:

```python
"audio_transcription_config": {
    "model_transcription_config": {
        "enable_user_transcription": True,  # Text of what you said
        "enable_model_transcription": True  # Text of what AI said
    }
}
```

This enables:
- Real-time text transcription of your speech
- Text transcription of model responses
- Simultaneous audio playback

## References

- [Gemini 2.5 Flash Live API](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-flash-live-api)
- [Vertex AI Live API Overview](https://cloud.google.com/vertex-ai/generative-ai/docs/live-api)
- [Original Gemini API Example](https://ai.google.dev/gemini-api/docs/live?example=mic-stream)
