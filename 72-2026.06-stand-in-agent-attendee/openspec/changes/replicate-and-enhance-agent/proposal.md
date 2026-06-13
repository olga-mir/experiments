# Proposal: replicate-and-enhance-agent

## Summary
Replicate the ADK conference attendee agent from `~/dev/dummy-folder2` to the current workspace with enhancements for better genericity and a new simulation mode for troubleshooting. The project will follow strict guidelines: using `uv` for Python management and `Taskfile` for automation, including a `preflight` check for environment variables.

## Problem
The current agent is hardcoded for a specific conference (AI Engineer Melbourne 2026) and its data sources are fixed. To reuse the agent for other events or for development/troubleshooting, it needs to be more flexible and support mock/simulated data streams.

## Proposed Solution
1. **Replication**: Port `agent.py`, `config.py`, `tools.py`, and `requirements.txt` to the current folder.
2. **Genericity**: Refactor `tools.py` and `config.py` to use environment variables or configuration files for base URLs and conference-specific metadata.
3. **Simulation Mode**: Introduce a `SIMULATION_MODE` environment variable. When enabled, the agent will point to a simulation endpoint (to be defined or made configurable).
4. **Taskfile Integration**: Create a `Taskfile.yml` that handles environment setup, running the agent, and a `preflight` task to validate required variables like `GOOGLE_CLOUD_PROJECT`, `SCREENSHOTS_BUCKET_NAME`, and `CONFERENCE_BASE_URL`.
5. **Dependency Management**: Use `uv` to manage Python dependencies and run commands.

## Capabilities Affected
- **Core Agent Logic**: Instructions and tool initialization.
- **Data Fetching Tools**: URL construction and response handling.
- **Configuration Management**: Env var loading and validation.
- **Automation/CI/CD**: Introduction of `Taskfile`.

## Impact & Risks
- **Impact**: Increased reusability of the agent for future conferences and easier troubleshooting via simulation.
- **Risks**: Ensuring the simulation mode accurately reflects the live API structure to avoid misleading troubleshooting results.

## Out of Scope
- Actually deploying the simulation endpoint (this change only covers the agent-side configuration).
- Implementing new core capabilities beyond what the source agent already provides (except for genericity).
