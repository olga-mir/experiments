# Tasks: replicate-and-enhance-agent

## Progress
0 / 12 complete

## Implementation Tasks

### Phase: Setup & Replication
- [ ] Initialize `agents-cli` project structure: `agents-cli scaffold create ai-attendee-v2`
- [ ] Copy source files from `~/dev/dummy-folder2/` to the new project directory.
- [ ] Verify `uv` environment setup and install dependencies from `requirements.txt`.

### Phase: Core Implementation (Genericity & Simulation)
- [ ] Refactor `config.py`: Add `SIMULATION_MODE`, `CONFERENCE_BASE_URL`, and `SIMULATION_BASE_URL` support.
- [ ] Refactor `tools.py`: Replace hardcoded `BASE_URL` with dynamic lookup from `config.py`.
- [ ] Refactor `agent.py`: Update system instructions to be conference-agnostic (using placeholders from config).
- [ ] Create `Taskfile.yml` with `preflight` and `run` tasks.

### Phase: Testing & Validation
- [ ] Verify `preflight` task correctly catches missing required environment variables.
- [ ] Verify `SIMULATION_MODE=true` correctly routes tool calls to the simulation endpoint.
- [ ] Perform a smoke test using `agents-cli run "checkin to the conference"`.
- [ ] Verify screenshot upload still works with the new configuration.

### Phase: Cleanup
- [ ] Remove any leftover Melbourne-specific hardcodings.
- [ ] Document the new environment variables in a local `README.md` or `GEMINI.md`.
