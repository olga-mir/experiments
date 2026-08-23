# 68-2026.08-design-canvas

**Status: runnable.** `map-viewer/` is a scaffolded Vite+React app that renders `sample-data/graph-map-data.json` — `cd map-viewer && npm run dev`. Shares the `68` / `2026.08` number+date with [`68-2026.08-moaar-agents-and-design-canvas`](../68-2026.08-moaar-agents-and-design-canvas/) per this repo's naming convention (see `../AGENTS.md`) since they're related but separate experiments; this one is a distinct slug, not a subfolder of that one.

## What this is

A viewer for the output of an ADK graph-agent design review: a graph topology + per-node contracts (inputs, outputs, state reads/writes, side effects, idempotency, failure behavior), rendered as an interactive React Flow canvas — click a node to expand its contract instead of rendering everything at once.

It's meant to consume the output of the `/design-review` skill pipeline (already installed for this user — check `available skills` for `my:design-review`, `my:design-scrutiny`, `my:adversarial-review`, `my:synthesis`, `my:grounding-check`). That pipeline runs scrutiny → adversarial → synthesis over an ADK design doc and produces `stage1-scrutiny.md`, `stage2-adversarial.md`, `final-design.md`, `graph-topology.mmd`, `node-contracts.md`, and `graph-map-data.json`. The last three are what this canvas renders.

## What's here

- `map-viewer/` — a scaffolded Vite+React app (`npm create vite -- --template react` + `npm i reactflow`). `src/App.jsx` is the working React Flow component (custom `ContractNode` with click-to-expand contract details); `src/App.jsx` imports data from `../../sample-data/graph-map-data.json`. Verified with `npm run dev` and `vite build`.
- `sample-data/` — real output for testing the viewer against, generated from the actual [`alert-triage-agent`](../68-2026.08-moaar-agents-and-design-canvas/alert-triage-agent/) implementation (its `app/agent.py` `Workflow` graph), not a toy example:
  - `graph-map-data.json` — the React Flow data file `App.jsx` expects (`nodes[].{id,label,position,contract{...}}`, `edges[].{id,source,target,label}`)
  - `graph-topology.mmd` — the same graph as a Mermaid flowchart
  - `node-contracts.md` — the same contracts as a markdown table

## Gaps / open questions (for whoever picks this up next)

- **The JSON path is hardcoded to sample data.** `src/App.jsx` imports `../../sample-data/graph-map-data.json` directly — there's no file picker or config, so viewing a different review's output means editing that import (or overwriting the sample file) and reloading.
- **`sample-data/`'s files are hand-derived, not pipeline output.** They were hand-authored by an agent from the alert-triage-agent's source to match `App.jsx`'s expected shape — not produced by an actual `/design-review` run. Worth running the real pipeline against a design doc to confirm its actual `graph-map-data.json` shape (field names, position values, etc.) matches what `App.jsx` expects.
- **Product question still undecided:** is this a **static per-review viewer** (swap the JSON file, reload — what it does today) or does "design canvas" mean something with live/multiple-graph browsing, diffing between review runs, or editing? Not decided — don't assume either way.

## Making this reusable across reviews (carried over from earlier notes)

The `/design-review` pipeline's three stages are already framework-agnostic in structure — the ADK-specificity lives in the prompts, so if you keep hitting "generic first draft" on other frameworks too, duplicate the agent files and swap the framework-specific language.

Worth adding over time, since the root problem is the base model reaching for its most-represented training pattern rather than the best one:

- **Pin real reference repos.** Give the scrutiny stage a short list of repos you trust as "idiomatic ADK" via DeepWiki or a local clone it can Grep — grounding beats search when search results are themselves mostly tutorial-tier content.
- **Grep.app / Sourcegraph** for cross-repo code search when you want to see how a pattern is actually used in production code, not just documented.
- **Keep a running "anti-patterns we keep generating" file** — feed it into the scrutiny stage's context so it stops re-proposing things already rejected in prior reviews. This compounds; worth starting even with 3-4 entries.
- **GitHub code search MCP** if you want the scrutiny stage to search public repos directly rather than through Exa's index.
