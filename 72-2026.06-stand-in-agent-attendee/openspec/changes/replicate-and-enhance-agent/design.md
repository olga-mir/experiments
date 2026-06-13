# Design: replicate-and-enhance-agent

## Approach
The core strategy is to refactor the hardcoded dependencies into a flexible configuration layer. We will use `python-dotenv` for local environment management and a structured `AgentConfiguration` dataclass to provide type-safe access to these settings. The `Taskfile.yml` will serve as the entry point for all operations, ensuring that the environment is validated before the agent starts.

## Architecture
- **Taskfile.yml**: The orchestrator. Runs `preflight` and then `uv run agent.py`.
- **config.py**: The source of truth for settings. Decides the `BASE_URL` based on `SIMULATION_MODE`.
- **tools.py**: Stateless functions that take their base URL from `config.py`.
- **agent.py**: The ADK agent definition, using the tools and configuration.

## Key Decisions

### Decision: Environment Variable Validation
- **Options considered:** Validate inside Python (`config.py`) or in the Taskfile.
- **Chosen:** Both. Taskfile for immediate feedback to the user; `config.py` for runtime safety.
- **Rationale:** Prevents the agent from starting and failing halfway through a tool call due to a missing secret or project ID.

### Decision: Simulation Mode Implementation
- **Options considered:** Separate tool versions for simulation vs live.
- **Chosen:** Single toolset with parameterized URLs.
- **Rationale:** Maintains DRY (Don't Repeat Yourself) and ensures that testing in simulation mode validates the exact logic used in live mode.

## Implementation Notes
- **Monkey-patching**: Retain the monkey-patch for `validate_app_name` if it's still needed for Vertex AI Agent Engine compatibility.
- **Shared Tools**: If `shared_tools` is a local folder in the source, it must be copied. If it's a library, it should be in `requirements.txt`. (Based on `ls`, it's a directory).

## Testing Strategy
- **Manual Verification**: Use `agents-cli run` with `SIMULATION_MODE=true` to verify the agent correctly points to the mock endpoint.
- **Preflight Check**: Intentionally unset a required variable and verify `task run` fails.
- **Tool Integrity**: Run a script that calls each tool in `tools.py` individually and asserts the URL construction.
