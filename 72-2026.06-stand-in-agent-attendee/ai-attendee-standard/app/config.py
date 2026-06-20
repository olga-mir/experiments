# Copyright 2026 Google LLC
import os
from dataclasses import dataclass
from dotenv import load_dotenv

import google.auth

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
setup_env_path = os.path.join(project_root, ".setup-env")

import sys

if os.path.exists(setup_env_path):
    load_dotenv(dotenv_path=setup_env_path, override=True)
    print(f"Loaded configuration from {setup_env_path}", file=sys.stderr)
else:
    print(f"Warning: {setup_env_path} not found. Using system environment variables.", file=sys.stderr)

try:
    _, project_id = google.auth.default()
except Exception:
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "placeholder-project")

os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

def _strip_quotes(value: str) -> str:
    return value.strip().strip('"').strip("'")

@dataclass
class AgentConfiguration:
    @property
    def demo_mode(self) -> str:
        return os.getenv("DEMO_MODE", "vertex")

    @property
    def worker_model(self) -> str:
        return _strip_quotes(os.environ.get("WORKER_MODEL", "gemini-2.5-flash"))

    @property
    def agent_name(self) -> str:
        return os.environ.get("AI_ENGINEER_AGENT_NAME", "AI Engineer Attendee")

    @property
    def on_behalf_of(self) -> str:
        return os.environ.get("AI_ENGINEER_ON_BEHALF_OF", "Olga Mirensky")

    @property
    def conference_name(self) -> str:
        return os.environ.get("CONFERENCE_NAME", "Demo for GDG June 2026")

    @property
    def conference_dates(self) -> str:
        return os.environ.get("CONFERENCE_DATES", "2026-06-03–2026-06-04")

    @property
    def screenshots_bucket_name(self) -> str:
        return os.environ.get("SCREENSHOTS_BUCKET_NAME", "")

    @property
    def conference_repo(self) -> str:
        return os.environ.get("CONFERENCE_REPO", "olga-mir/conferences")

    @property
    def simulation_mode(self) -> bool:
        return os.environ.get("SIMULATION_MODE", "true").lower() == "true"

    @property
    def conference_base_url(self) -> str:
        return os.environ.get("CONFERENCE_BASE_URL", "")

    @property
    def simulation_base_url(self) -> str:
        return os.environ.get("SIMULATION_BASE_URL", "")

    @property
    def base_url(self) -> str:
        if self.simulation_mode and self.simulation_base_url:
            return self.simulation_base_url
        return self.conference_base_url

    @property
    def program_url(self) -> str:
        return os.environ.get("PROGRAM_URL", "NOT_SET")


config = AgentConfiguration()


def get_model_wrapper(model_name: str):
    if config.demo_mode == "local":
        from google.adk.models.lite_llm import LiteLlm
        return LiteLlm(model_name)
    else:
        return model_name
