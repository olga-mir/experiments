# 68-2026.08-design-canvas

**Status: not started.** This folder holds setup notes and sample data only — no code has been written yet. Shares the `68` / `2026.08` number+date with [`68-2026.08-moaar-agents-and-design-canvas`](../68-2026.08-moaar-agents-and-design-canvas/) per this repo's naming convention (see `../AGENTS.md`) since they're related but separate experiments; this one is a distinct slug, not a subfolder of that one.

## What this is

A viewer for the output of an ADK graph-agent design review: a graph topology + per-node contracts (inputs, outputs, state reads/writes, side effects, idempotency, failure behavior), rendered as an interactive React Flow canvas — click a node to expand its contract instead of rendering everything at once.

It's meant to consume the output of the `/design-review` skill pipeline (already installed for this user — check `available skills` for `my:design-review`, `my:design-scrutiny`, `my:adversarial-review`, `my:synthesis`, `my:grounding-check`). That pipeline runs scrutiny → adversarial → synthesis over an ADK design doc and produces `stage1-scrutiny.md`, `stage2-adversarial.md`, `final-design.md`, `graph-topology.mmd`, `node-contracts.md`, and `graph-map-data.json`. The last three are what this canvas renders.

## What's here

- `map-viewer/App.jsx` — a working React Flow component (custom `ContractNode` with click-to-expand contract details). Not yet a runnable project — needs a Vite scaffold around it (see Next steps).
- `sample-data/` — real output for testing the viewer against, generated from the actual [`alert-triage-agent`](../68-2026.08-moaar-agents-and-design-canvas/alert-triage-agent/) implementation (its `app/agent.py` `Workflow` graph), not a toy example:
  - `graph-map-data.json` — the React Flow data file `App.jsx` expects (`nodes[].{id,label,position,contract{...}}`, `edges[].{id,source,target,label}`)
  - `graph-topology.mmd` — the same graph as a Mermaid flowchart
  - `node-contracts.md` — the same contracts as a markdown table

## Next steps (for whoever picks this up)

1. `cd map-viewer && npm create vite@latest . -- --template react` (scaffold in place, don't nest — or scaffold elsewhere and move `App.jsx` in), then `npm i reactflow`.
2. Point `App.jsx`'s `import graphData from './graph-map-data.json'` at `../sample-data/graph-map-data.json` (or copy the file in) and `npm run dev` to confirm it renders `sample-data/`'s 7-node alert-triage-agent graph correctly.
3. Decide the open product question this repo doesn't answer yet: is this a **static per-review viewer** (swap the JSON file, `npm run dev` again — what the original notes below describe) or does "design canvas" mean something with live/multiple-graph browsing, diffing between review runs, or editing? That decision isn't made — don't assume either way.
4. If useful: `sample-data/`'s three files were hand-derived from the alert-triage-agent's source code by an agent, not produced by an actual `/design-review` run — worth running `/design-review` for real against a design doc once the viewer works, to confirm the pipeline's actual output shape matches `App.jsx`'s expectations exactly (field names, position values, etc.) rather than relying on this hand-authored approximation.

## Making this reusable across reviews (carried over from earlier notes)

The `/design-review` pipeline's three stages are already framework-agnostic in structure — the ADK-specificity lives in the prompts, so if you keep hitting "generic first draft" on other frameworks too, duplicate the agent files and swap the framework-specific language.

Worth adding over time, since the root problem is the base model reaching for its most-represented training pattern rather than the best one:

- **Pin real reference repos.** Give the scrutiny stage a short list of repos you trust as "idiomatic ADK" via DeepWiki or a local clone it can Grep — grounding beats search when search results are themselves mostly tutorial-tier content.
- **Grep.app / Sourcegraph** for cross-repo code search when you want to see how a pattern is actually used in production code, not just documented.
- **Keep a running "anti-patterns we keep generating" file** — feed it into the scrutiny stage's context so it stops re-proposing things already rejected in prior reviews. This compounds; worth starting even with 3-4 entries.
- **GitHub code search MCP** if you want the scrutiny stage to search public repos directly rather than through Exa's index.
