# Ambient Conference Attendee Agent

This project contains the **Event-Driven Ambient Agent** for conference attendance.

## Development Commands

| Command | Purpose |
|---------|---------|
| `task preflight` | Check environment variables |
| `task install` | Install dependencies |
| `task run` | Run a manual sweep |
| `task server` | Run local server (for triggers) |
| `task trigger` | Simulate a local webhook trigger |
| `task deploy` | Deploy to GCP Agent Platform |
| `task logs` | Tail recent Reasoning Engine logs |
| `task session:create` | Create a persistent session (required before scheduling) |
| `task session:list` | List sessions for user_id=scheduler |
| `task session:reset` | Delete and recreate the session (use between test runs) |
| `task setup:infra` | One-time: enable APIs, create SA, grant IAM roles |
| `task schedule` | Create/update the Cloud Scheduler cron job |

## Deployment & Scheduling

1. **Deploy** to Vertex AI Agent Engine:
   ```bash
   task deploy
   ```

2. **Create a session** (must exist before the scheduler can use it):
   ```bash
   task session:create
   ```

3. **Schedule** periodic sweeps (reads session ID from `.ambient_session_id` automatically):
   ```bash
   AGENT_URL=https://us-east1-aiplatform.googleapis.com/v1/projects/<PROJECT_NUM>/locations/us-east1/reasoningEngines/<ENGINE_ID> \
     task schedule
   ```

4. **View outputs**:
   ```bash
   task logs
   ```

## How Cloud Scheduler calls the agent

Cloud Scheduler POSTs to `<AGENT_URL>:streamQuery` (Reasoning Engine REST API) with OAuth auth
and the body `{"input": {"message": "tick", "user_id": "scheduler", "session_id": "<id>"}}`.
The `input` envelope is required by the Reasoning Engine API. OAuth is required (not OIDC)
because the target URL ends in `.googleapis.com`.
