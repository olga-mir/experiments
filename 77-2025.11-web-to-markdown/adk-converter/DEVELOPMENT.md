# Development Guide

This document covers environment setup, local development, and deployment for human developers.

## Environment Setup

### Local Repositories

Reference repositories are checked out at `${HOME}/repos/upstream/gcp-google/`:

| Repository | Purpose |
|------------|---------|
| `adk-python` | Core ADK SDK |
| `adk-docs` | ADK documentation |
| `adk-samples` | Usage examples |
| `python-aiplatform` | Vertex AI SDK for deployment |
| `agent-starter-pack` | Reference for GitHub Actions pipelines |

### Package Management

Use `uv` for all Python operations. Do not use `pip` or `python` directly.

```bash
# Install dependencies
uv sync

# Run commands
uv run pytest
uv run python script.py
```

### Environment Variables

**For agent deployment target:**
```bash
export PROJECT_ID=...
export PROJECT_NUMBER=...
```

## Development Workflow

### Available Tasks

```bash
task --list        # Show all available tasks
task test          # Run unit tests
task lint          # Run linters
task deploy        # Deploy agent to Vertex AI
task verify        # Verify deployed agent
task cleanup-agents --force  # Delete deployed agents
```

### Running the AI Development Loop

```bash
./run-gemini.sh
```

This wrapper script:
1. Runs gemini-cli with the prompt
2. Captures the session output
3. Includes the session timestamp and AI usage stats in commit messages

## Deployment

### Strategy: Inline Source Deployment

We deploy to **Vertex AI Agent Engine** using **Inline Source Deployment** (no GCS buckets required for code).

Reference: [Deploying Agents with Inline Source](https://discuss.google.dev/t/deploying-agents-with-inline-source-on-vertex-ai-agent-engine/288935)

### Local Deployment

```bash
task deploy
TEST_URL=<your-url> task verify
```

### CI/CD (GitHub Actions)

Uses **Workload Identity Federation (OIDC)** for authentication.

**OIDC Setup:** See [github.com/olga-mir/experiments/tree/main/82-2025.06-oidc-demo](https://github.com/olga-mir/experiments/tree/main/82-2025.06-oidc-demo)

**Required GitHub Secrets:**

| Secret | Description |
|--------|-------------|
| `GCP_PROJECT_ID` | Google Cloud Project ID |
| `WIF_PROVIDER` | Workload Identity Provider resource name |

**Required Permissions:** The principal needs `Vertex AI Express User` role at minimum.

## Troubleshooting

### Permission Issues

If you encounter permission errors:
1. Verify your GCP credentials: `gcloud auth list`
2. Check project: `gcloud config get-value project`
3. Ensure required roles are assigned to your identity
