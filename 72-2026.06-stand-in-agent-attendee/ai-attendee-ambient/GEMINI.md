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
| `task schedule` | Set up the 5-minute Cloud Scheduler cron |

## Deployment & Scheduling

1. **Deploy** as a separate Reasoning Engine entity:
   ```bash
   task deploy
   ```
2. **Schedule** the periodic sweeps:
   ```bash
   task schedule
   ```
