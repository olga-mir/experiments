# Text Transcription with Native Audio Model

## Overview

The `gemini-live-2.5-flash-native-audio` model supports simultaneous audio conversation AND text transcription. This document describes how to enable text transcription for the next iteration.

## Configuration

The key is using `audio_transcription_config` in the Live API configuration:

```python
config = {
    "generation_config": {
        # CRITICAL: This model only accepts "AUDIO" for output modality
        "response_modalities": ["AUDIO"],

        # Optional: Configure voice characteristics
        "speech_config": {
            "voice_config": {
                "prebuilt_voice_config": {
                    "voice_name": "Puck"  # or "Charon", "Kore", etc.
                }
            }
        }
    },

    # ENABLE TEXT TRANSCRIPTION: This enables text alongside audio
    "audio_transcription_config": {
        "model_transcription_config": {
            "enable_user_transcription": True,  # Transcribe what the user says
            "enable_model_transcription": True  # Transcribe what the model says
        }
    }
}
```

## Implementation Notes

### Response Structure Changes

When transcription is enabled, responses will include:

1. **Audio data** in `response.server_content.model_turn.parts[].inline_data.data`
2. **Transcription events** (need to investigate exact structure)

### Code Changes Required

**src/main.py modifications:**

1. Update `get_live_config()` to include `audio_transcription_config`
2. Modify `receive_responses()` to handle transcription events
3. Add text output alongside audio playback

Example:
```python
def get_live_config(self):
    return {
        "response_modalities": ["AUDIO"],
        "system_instruction": self.config.system_instruction,
        "speech_config": {
            "voice_config": {
                "prebuilt_voice_config": {"voice_name": "Puck"}
            }
        },
        "audio_transcription_config": {
            "model_transcription_config": {
                "enable_user_transcription": True,
                "enable_model_transcription": True
            }
        }
    }
```

### Expected Behavior

- User speaks → Live API transcribes user speech to text (realtime)
- Model responds → Audio plays AND text transcription is available
- Both transcriptions can be displayed in the terminal

## Research Needed

1. **Response format**: What fields contain the transcription text?
2. **Timing**: Are transcriptions streamed or sent at turn completion?
3. **Event types**: Are there specific message types for transcription?
4. **Error handling**: How to handle partial/failed transcriptions?

## Benefits

- Visual feedback of what the model heard
- Ability to log conversations as text
- Accessibility for users who need text output
- Debugging aid to verify VAD/turn detection

## References

- [Gemini 2.5 Flash Live API Docs](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-flash-live-api)
- Current implementation: `src/main.py`