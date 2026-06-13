# Spec: configuration-management

## Overview
This capability handles environment variable loading, validation, and providing a unified configuration object to the rest of the agent. It is being enhanced to support `SIMULATION_MODE` and parameterized URLs.

### Requirement: Environment Validation

**Context:** The agent requires several environment variables to function correctly (e.g., `GOOGLE_CLOUD_PROJECT`, `SCREENSHOTS_BUCKET_NAME`).

#### Scenario: Missing required variable
- **Given** the `GOOGLE_CLOUD_PROJECT` environment variable is not set
- **When** the `preflight` task is run via `Taskfile`
- **Then** the process should exit with a non-zero code and a clear error message.

#### Scenario: Optional variable defaults
- **Given** the `WORKER_MODEL` environment variable is not set
- **When** the configuration is loaded
- **Then** it should default to `gemini-2.5-flash`.

### Requirement: Simulation Mode Toggle

**Context:** The agent needs to switch between live conference data and a simulation stream for troubleshooting.

#### Scenario: Live mode (default)
- **Given** `SIMULATION_MODE` is not set or is set to `false`
- **When** the `CONFERENCE_BASE_URL` is requested
- **Then** it should return the live API base URL (`https://agents.conffab.com/ai-engineer/live`).

#### Scenario: Simulation mode enabled
- **Given** `SIMULATION_MODE` is set to `true`
- **When** the `CONFERENCE_BASE_URL` is requested
- **Then** it should return the URL specified in `SIMULATION_BASE_URL`.
