# 68-2026.08-design-canvas

**Status: runnable.** `map-viewer/` is a Vite+React app that renders a design's `graph-map-data.json` — `cd map-viewer && npm run dev`. Shares the `68` / `2026.08` number+date with [`68-2026.08-moaar-agents-and-design-canvas`](../68-2026.08-moaar-agents-and-design-canvas/) per this repo's naming convention (see `../AGENTS.md`).

## What this is

An interactive viewer for a **design's** graph topology and per-node contracts — inputs, outputs, state reads/writes, side effects, idempotency, failure behavior — rendered as a React Flow canvas. Click a node to expand its contract instead of rendering everything at once.

It consumes the synthesis output of the `/design-review` pipeline (`graph-map-data.json`, plus companion `graph-topology.mmd` and `node-contracts.md`). The bundled `sample-data/` is real pipeline-shaped output for the alert-triage-agent design (copied from work on the sibling experiment), not a toy graph.

**Product shape:** one canvas per design document. Open the `graph-map-data.json` produced when you review that design — not a per-run diff/history browser.

## What's here

- `map-viewer/` — Vite+React + React Flow viewer
  - Loads bundled `sample-data/graph-map-data.json` on startup
  - **Open graph-map-data.json** toolbar control to pick a different design's file
  - Custom `ContractNode` (click-to-expand contracts) and `TerminalNode` (START/END)
  - Edges with arrow markers; dashed style for delegation edges (`dashed: true` in JSON)
- `sample-data/` — alert-triage-agent design artifacts:
  - `graph-map-data.json` — React Flow data (`nodes[].{id,label,position,kind?,contract?}`, `edges[].{id,source,target,label?,dashed?}`)
  - `graph-topology.mmd` — same graph as Mermaid
  - `node-contracts.md` — same contracts as markdown

## Usage

```bash
cd map-viewer && npm run dev
```

Use **Open graph-map-data.json** to load the synthesis artifact from any `/design-review` run for a different design.

## JSON schema notes

| Field | Where | Meaning |
|-------|-------|---------|
| `kind: "start"` \| `"end"` | node | Renders as a terminal pill instead of a contract box |
| `contract` | node | Collapsed contract details (omitted on START/END) |
| `label` | edge | Route name shown on the edge |
| `dashed: true` | edge | Dotted line (task delegation, sub-agent calls, etc.) |
