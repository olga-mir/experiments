# Tasks: replicate-and-enhance-agent

## Progress
12 / 12 complete

## Implementation Tasks

### Phase: Setup & Replication
- [x] Initialize `agents-cli` project structure: `agents-cli scaffold create ai-attendee-v2`
- [x] Copy source files from `~/dev/dummy-folder2/` to the new project directory.
- [x] Verify `uv` environment setup and install dependencies from `requirements.txt`.

### Phase: Core Implementation (Genericity & Simulation)
- [x] Refactor `config.py`: Add `SIMULATION_MODE`, `CONFERENCE_BASE_URL`, and `SIMULATION_BASE_URL` support.
- [x] Refactor `tools.py`: Replace hardcoded `BASE_URL` with dynamic lookup from `config.py`.
- [x] Refactor `agent.py`: Update system instructions to be conference-agnostic (using placeholders from config).
- [x] Create `Taskfile.yml` with `preflight` and `run` tasks.

### Phase: Testing & Validation
- [x] Verify `preflight` task correctly catches missing required environment variables.
- [x] Verify `SIMULATION_MODE=true` correctly routes tool calls to the simulation endpoint.
- [x] Perform a smoke test using `agents-cli run "checkin to the conference"`.
- [x] Verify screenshot upload still works with the new configuration.

### Phase: Cleanup
- [x] Remove any leftover Melbourne-specific hardcodings.
- [x] Document the new environment variables in a local `README.md` or `GEMINI.md`.
