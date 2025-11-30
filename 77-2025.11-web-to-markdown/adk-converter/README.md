# Web to Markdown Agent

A Python-based AI agent that extracts content from technical websites and converts it to clean Markdown. Built on [Google Cloud Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/docs/agent-engine/overview) using **Inline Source Deployment**.

## Features

- Extract main content from URLs (removes navigation, ads, boilerplate)
- Download and embed images locally
- Deploy to Vertex AI Agent Engine
- CI/CD via GitHub Actions with OIDC authentication

## Quick Start

```bash
# Install dependencies
uv sync

# Run tests
task test

# Deploy agent
task deploy

# Verify deployment
TEST_URL=https://example.com task verify

# Cleanup
task cleanup-agents --force
```

## Project Structure

```
web-to-md-agent/
├── web_to_md/core/      # Core agent logic and tools
├── deployment/          # Deployment scripts
├── tests/               # Unit tests
├── Taskfile.yml         # Automation tasks
└── docs:
    ├── AGENTS.md        # AI agent instructions
    ├── DEVELOPMENT.md   # Human developer guide
    └── what-good-looks-like.md  # Success criteria
```

## AI-Assisted Development

This project uses gemini-cli for iterative AI-assisted development:

```bash
./run-gemini.sh
```

The wrapper script:
1. Runs gemini with the iteration prompt
2. Captures session output to `gemini-sessions-outputs/`
3. Displays stats for including in commit messages

## Documentation

| Document | Purpose |
|----------|---------|
| [AGENTS.md](AGENTS.md) | Instructions for the AI agent |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Setup guide for human developers |
| [what-good-looks-like.md](what-good-looks-like.md) | Success criteria checklist |

## Tech Stack

- **Language**: Python
- **Framework**: Google ADK (Agent Development Kit)
- **Platform**: Vertex AI Agent Engine
- **Package Manager**: uv
- **Task Runner**: Taskfile
