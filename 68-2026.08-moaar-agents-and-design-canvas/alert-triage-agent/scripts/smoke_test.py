# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Runs the agent once against a synthetic alert and prints the final report.

Exercises the full pipeline wiring end to end. The maintenance gate is
deterministic-ish (coin flip, see app/maintenance.py) so about half of all
runs will short-circuit before ever calling the LLM/GKE/Cloud Monitoring —
that's expected, not a bug. A run that reaches the LLM agents requires a GCP
project with the Vertex AI API enabled and (for real tool results) a
reachable GKE cluster matching the alert's project_id/location/cluster_name.
"""

import asyncio
import json
import os

from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agent import root_agent

ALERT = {
    "host_id": os.environ.get("SMOKE_TEST_NODE_NAME", "gke-cluster1-pool1-abcd1234-xyz0"),
    "cluster_name": os.environ.get("GKE_CLUSTER_NAME", "cluster1"),
    "project_id": os.environ.get("GKE_PROJECT_ID", os.environ.get("PROJECT_ID", "unset-project")),
    "location": os.environ.get("GKE_LOCATION", "us-central1"),
    "alert_type": "high_cpu",
    "timestamp": "2026-08-23T10:00:00.000000",
}


async def main() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name="app")
    session = await runner.session_service.create_session(app_name="app", user_id="smoke-test")
    message = types.Content(role="user", parts=[types.Part(text=json.dumps(ALERT))])

    async for event in runner.run_async(
        user_id="smoke-test", session_id=session.id, new_message=message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            print(event.content.parts[0].text)


if __name__ == "__main__":
    asyncio.run(main())
