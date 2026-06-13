# Coding Agent Guide

## Prerequisites

Install the CLI (one-time):
```bash
uv tool install google-agents-cli
```

---

## Development Phases

### Phase 1: Understand Requirements
Before writing any code, understand the project's requirements, constraints, and success criteria.

### Phase 2: Build and Implement
Implement agent logic in `app/`. Use `agents-cli playground` for interactive testing. Iterate based on user feedback.

### Phase 3: The Evaluation Loop (Main Iteration Phase)
Start with 1-2 eval cases, run `agents-cli eval run`, iterate. Expect 5-10+ iterations. See the **Evaluation Guide** for metrics, evalset schema, LLM-as-judge config, and common gotchas.

### Phase 4: Pre-Deployment Tests
Run `uv run pytest tests/unit tests/integration`. Fix issues until all tests pass.

### Phase 5: Deploy to Dev
**Requires explicit human approval.** Run `agents-cli deploy` only after user confirms. See the **Deployment Guide** for details.

### Phase 6: Production Deployment
Ask the user: Option A (simple single-project) or Option B (full CI/CD pipeline with `agents-cli infra cicd`).

## Development Commands

| Command | Purpose |
|---------|---------|
| `task preflight` | Check required environment variables |
| `task run -- "prompt"` | Run agent with a single prompt |
| `task playground` | Interactive local testing |
| `task eval` | Run evaluation against evalsets |

## Environment Variables

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `GOOGLE_CLOUD_PROJECT` | Yes | (gcloud config) | Google Cloud Project ID |
| `GOOGLE_CLOUD_LOCATION`| No | `us-central1` | Region for Vertex AI |
| `SCREENSHOTS_BUCKET_NAME`| No | | GCS bucket for screen captures |
| `SIMULATION_MODE` | No | `false` | Enable simulation stream |
| `CONFERENCE_BASE_URL` | No | (AI Engineer) | Live API base URL |
| `SIMULATION_BASE_URL` | No | | Simulation API base URL |
| `CONFERENCE_NAME` | No | `AI Engineer Melbourne 2026` | Display name for system instructions |
| `CONFERENCE_DATES` | No | `2026-06-03–2026-06-04` | Dates for system instructions |

## Simulation Mode

To troubleshoot the agent using a simulation stream, set the following variables:
```bash
export SIMULATION_MODE=true
export SIMULATION_BASE_URL=https://your-simulation-endpoint.com/live
```
The agent will automatically route all data-fetching tool calls to the simulation endpoint.

---

## Operational Guidelines for Coding Agents

- **Code preservation**: Only modify code directly targeted by the user's request. Preserve all surrounding code, config values (e.g., `model`), comments, and formatting.
- **NEVER change the model** unless explicitly asked.
- **Model 404 errors**: Fix `GOOGLE_CLOUD_LOCATION` (e.g., `global` instead of `us-east1`), not the model name.
- **ADK tool imports**: Import the tool instance, not the module: `from google.adk.tools.load_web_page import load_web_page`
- **Run Python with `uv`**: `uv run python script.py`. Run `agents-cli install` first.
- **Stop on repeated errors**: If the same error appears 3+ times, fix the root cause instead of retrying.
- **Terraform conflicts** (Error 409): Use `terraform import` instead of retrying creation.
