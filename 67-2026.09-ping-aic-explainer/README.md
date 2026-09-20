# PingOne AIC Explainer

Code-first ADK rewrite of an Agent Studio exercise agent. The coordinator
explains PingOne Advanced Identity Cloud from public docs, delegates Ping
product questions to a specialist, and only expands generic IAM terms when the
user asks or says they are a beginner.

Scaffolded with `agents-cli` 1.6.1 (`adk` template, Agent Runtime, prototype).
Older deploy scripts in other repos (`adk-deep-dives`, `agents`) wrap the
Agent Engine Python SDK directly; this project uses `agents-cli deploy`.

## Layout

```
app/agent.py          # coordinator + specialists + built-in search/URL tools
Taskfile.yml          # setup, preflight, playground, deploy
.env.example          # copy to .env; do not commit real project ids
```

## Setup

```bash
cp .env.example .env   # set GOOGLE_CLOUD_PROJECT
task setup
task preflight
task playground
```

Required env: `GOOGLE_CLOUD_PROJECT`. Optional: `GOOGLE_CLOUD_LOCATION`
(defaults to `global` in `.env.example` for Gemini 3), `GOOGLE_CLOUD_REGION`
(Taskfile deploy default `us-central1`).

## Deploy

```bash
task deploy:dry-run
task deploy            # Agent Runtime in $GOOGLE_CLOUD_PROJECT / us-central1
task deploy:status     # if the CLI times out; the job keeps running server-side
```

Do not commit `.env`, Terraform `env.tfvars`, or `deployment_metadata.json`
(those files hold project and engine identifiers).

## Studio leftover

Agent Studio create/update can leave an Agent Runtime in `us-west1` named
`agent_studio_agent_*` with no source code — only an agent identity. That stub
does not serve the playground agent and can block later Studio deploys. Delete
it from the Cloud Console (Agent Runtime) or via the Reasoning Engine API with
`force=true` so child sessions are removed. Leave other runtimes in
`us-central1` alone; those belong to other agents.
