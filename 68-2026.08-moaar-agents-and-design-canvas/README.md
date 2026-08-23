# 68-2026.08-moaar-agents-and-design-canvas

## alert-triage-agent

An ADK re-implementation of NVIDIA's [Alert Triage Agent](https://github.com/NVIDIA/NeMo-Agent-Toolkit/tree/develop/examples/advanced_agents/alert_triage_agent) example (NeMo Agent Toolkit + LangGraph), retargeted from bare-metal/SSH diagnostics to GKE clusters (Kubernetes API + Cloud Monitoring) and deployed to Gemini Enterprise Agent Platform (Agent Engine).

The original investigates server-monitoring alerts by dynamically calling diagnostic tools (hardware/IPMI, host performance, network connectivity, monitoring-process checks, telemetry analysis), then produces a structured triage report with root-cause categorization. This port keeps that shape — a deterministic maintenance gate, an LLM agent that dynamically selects diagnostic tools, a telemetry sub-agent, and root-cause classification — while:

- swapping SSH/Ansible/IPMI for Kubernetes API + Cloud Monitoring calls against a GKE cluster,
- rebuilding the orchestration as an ADK graph-based `Workflow` (nodes + routed edges) instead of LangGraph's `StateGraph`, mirroring the original's explicit-graph design more closely than ADK's linear `SequentialAgent` would,
- reducing the diagnostic tool set for the initial build (see `spec.md` §3 for what's implemented vs. deferred).

See [`spec.md`](spec.md) for the full design — data/API contracts, tool scope, the orchestration graph, and open questions — and [`alert-triage-agent/`](alert-triage-agent/) for the implementation (ADK + `agents-cli` project, Agent Engine deployment target).

**Not yet started:** "design canvas," the other half of this experiment's name — a separate feature planned for a later step, not part of the alert triage agent's design.
