"""Main entrypoint for the Vertex AI Live Audio Transcriber."""

import asyncio
import os
import signal
import sys
from typing import Optional

import pyaudio
from dotenv import load_dotenv
from google import genai

load_dotenv()

# https://ai.google.dev/gemini-api/docs/live?example=mic-stream
class Config:
    """Configuration loaded from environment variables."""

    def __init__(self):
        # Vertex AI Configuration
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        self.region = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")

        self.model_id = os.getenv("MODEL_ID", "gemini-live-2.5-flash-native-audio")
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1024"))
        self.sample_rate = int(os.getenv("SAMPLE_RATE", "16000"))

        # Transcription prompt
        self.system_instruction = (
            "You are a professional transcriber. Your output should be a clean, "
            "readable transcript of the audio. Remove all filler words, stutters, "
            "and verbal tics. Output text only."
        )


class AudioRecorder:
    """Handles microphone audio capture using PyAudio."""

    def __init__(self, config: Config):
        self.config = config
        self.pya = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.audio_queue = asyncio.Queue(maxsize=5)

    async def start(self):
        """Open the audio stream and start capturing."""
        mic_info = self.pya.get_default_input_device_info()
        self.stream = await asyncio.to_thread(
            self.pya.open,
            format=pyaudio.paInt16,
            channels=1,
            rate=self.config.sample_rate,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=self.config.chunk_size,
        )
        print(f"🎤 Recording from: {mic_info['name']}")

    async def capture_audio(self):
        """Continuously capture audio and put it into the queue."""
        if not self.stream:
            raise RuntimeError("Audio stream not started. Call start() first.")

        kwargs = {"exception_on_overflow": False}
        while True:
            try:
                data = await asyncio.to_thread(
                    self.stream.read, self.config.chunk_size, **kwargs
                )
                await self.audio_queue.put({"data": data, "mime_type": "audio/pcm"})
            except Exception as e:
                print(f"Error capturing audio: {e}")
                break

    def close(self):
        """Close the audio stream and terminate PyAudio."""
        if self.stream:
            self.stream.close()
        self.pya.terminate()


class LiveSession:
    """Manages the connection to the Vertex AI Live API."""

    def __init__(self, config: Config):
        self.config = config

        # Initialize Vertex AI client
        self.client = genai.Client(
            vertexai=True,
            project=config.project_id,
            location=config.region,
        )

        self.session = None

    def get_live_config(self):
        """Return the configuration for the Live API session."""
        return {
            "response_modalities": ["TEXT"],
            "system_instruction": self.config.system_instruction,
        }

    async def send_audio(self, audio_queue: asyncio.Queue):
        """Send audio from the queue to the Live API."""
        while True:
            msg = await audio_queue.get()
            await self.session.send_realtime_input(audio=msg)

    async def receive_text(self):
        """Receive text responses from the Live API and print them."""
        while True:
            turn = self.session.receive()
            async for response in turn:
                if response.server_content and response.server_content.model_turn:
                    for part in response.server_content.model_turn.parts:
                        if part.text:
                            print(f"\n📝 Transcript: {part.text}")

    async def connect_and_run(self, audio_recorder: AudioRecorder):
        """Connect to the Live API and run the transcription loop."""
        async with self.client.aio.live.connect(
            model=self.config.model_id,
            config=self.get_live_config(),
        ) as session:
            self.session = session
            print(f"✅ Connected to {self.config.model_id} via Vertex AI")
            print("🎙️  Start speaking... (Ctrl+C to stop)\n")

            async with asyncio.TaskGroup() as tg:
                tg.create_task(audio_recorder.capture_audio())
                tg.create_task(self.send_audio(audio_recorder.audio_queue))
                tg.create_task(self.receive_text())


async def main():
    """Main entrypoint for the transcriber."""
    config = Config()

    # Validate configuration
    if not config.project_id:
        print("❌ Error: GOOGLE_CLOUD_PROJECT environment variable not set.")
        print("   Please copy .env.example to .env and configure it.")
        sys.exit(1)

    print(f"🔧 Using Vertex AI (Project: {config.project_id}, Region: {config.region})")

    audio_recorder = AudioRecorder(config)
    live_session = LiveSession(config)

    try:
        await audio_recorder.start()
        await live_session.connect_and_run(audio_recorder)
    except asyncio.CancelledError:
        print("\n\n⏹️  Stopping...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        audio_recorder.close()
        print("👋 Closed.")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n⏹️  Interrupted by user.")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
