import { useState, useCallback } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  applyNodeChanges,
  applyEdgeChanges,
} from 'reactflow';
import 'reactflow/dist/style.css';
import graphData from '../../sample-data/graph-map-data.json';

// Custom node: shows label always, contract details on click (expand toggle)
// instead of everything rendered at once - this is the fix for "too much on
// one page" - each node's inputs/outputs/state/side-effects stay collapsed
// until you want them.
function ContractNode({ data }) {
  const [expanded, setExpanded] = useState(false);
  const c = data.contract;
  return (
    <div
      onClick={() => setExpanded((e) => !e)}
      style={{
        border: '1px solid #444',
        borderRadius: 8,
        padding: '8px 12px',
        background: c.idempotent ? '#f0fdf4' : '#fef2f2',
        minWidth: 160,
        cursor: 'pointer',
        fontFamily: 'ui-sans-serif, system-ui',
      }}
    >
      <div style={{ fontWeight: 600 }}>{data.label}</div>
      {expanded && c && (
        <div style={{ fontSize: 11, marginTop: 6, lineHeight: 1.5, textAlign: 'left' }}>
          <div><b>in:</b> {c.inputs}</div>
          <div><b>out:</b> {c.outputs}</div>
          {c.reads?.length > 0 && <div><b>reads:</b> {c.reads.join(', ')}</div>}
          {c.writes?.length > 0 && <div><b>writes:</b> {c.writes.join(', ')}</div>}
          {c.sideEffects?.length > 0 && <div><b>side fx:</b> {c.sideEffects.join(', ')}</div>}
          <div><b>idempotent:</b> {String(c.idempotent)}</div>
          <div><b>on failure:</b> {c.failureBehavior}</div>
        </div>
      )}
    </div>
  );
}

const nodeTypes = { contract: ContractNode };

export default function App() {
  const [nodes, setNodes] = useState(
    graphData.nodes.map((n) => ({
      id: n.id,
      position: n.position,
      data: { label: n.label, contract: n.contract },
      type: 'contract',
    }))
  );
  const [edges, setEdges] = useState(
    graphData.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      label: e.label,
      animated: !!e.label,
    }))
  );

  const onNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );
  const onEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}
