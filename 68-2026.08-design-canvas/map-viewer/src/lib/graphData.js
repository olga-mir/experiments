const DEFAULT_EDGE_STYLE = { stroke: '#64748b', strokeWidth: 2 };
const DASHED_EDGE_STYLE = { stroke: '#64748b', strokeWidth: 2, strokeDasharray: '6 4' };

export function validateGraphData(raw) {
  if (!raw || typeof raw !== 'object') {
    throw new Error('Expected a JSON object with nodes and edges arrays.');
  }
  if (!Array.isArray(raw.nodes) || !Array.isArray(raw.edges)) {
    throw new Error('graph-map-data.json must include "nodes" and "edges" arrays.');
  }
  for (const node of raw.nodes) {
    if (!node.id || !node.position) {
      throw new Error(`Each node needs id and position (bad node: ${JSON.stringify(node)})`);
    }
  }
  for (const edge of raw.edges) {
    if (!edge.id || !edge.source || !edge.target) {
      throw new Error(`Each edge needs id, source, and target (bad edge: ${JSON.stringify(edge)})`);
    }
  }
  return raw;
}

function nodeTypeFor(node) {
  if (node.kind === 'start' || node.kind === 'end') return 'terminal';
  return 'contract';
}

function edgeStyleFor(edge) {
  if (edge.dashed || edge.style === 'dashed') return DASHED_EDGE_STYLE;
  return DEFAULT_EDGE_STYLE;
}

export function toFlowElements(raw) {
  const data = validateGraphData(raw);
  const nodes = data.nodes.map((n) => ({
    id: n.id,
    position: n.position,
    type: nodeTypeFor(n),
    data: {
      label: n.label ?? n.id,
      kind: n.kind,
      contract: n.contract,
    },
  }));
  const edges = data.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.label,
    animated: Boolean(e.animated ?? e.label),
    style: edgeStyleFor(e),
  }));
  return { nodes, edges };
}
