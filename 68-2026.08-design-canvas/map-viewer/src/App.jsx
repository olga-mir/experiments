import { useCallback, useRef, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  applyNodeChanges,
  applyEdgeChanges,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import defaultGraphData from '../../sample-data/graph-map-data.json';
import ContractNode from './components/ContractNode.jsx';
import TerminalNode from './components/TerminalNode.jsx';
import { toFlowElements, validateGraphData } from './lib/graphData.js';

const nodeTypes = { contract: ContractNode, terminal: TerminalNode };

function applyMarkerDefaults(edges) {
  return edges.map((edge) => ({
    ...edge,
    markerEnd: edge.markerEnd ?? { type: MarkerType.ArrowClosed, color: '#64748b' },
  }));
}

function GraphToolbar({ sourceLabel, error, onPickFile }) {
  const inputRef = useRef(null);

  return (
    <div className="graph-toolbar">
      <div className="graph-toolbar__title">Design canvas</div>
      <label className="graph-toolbar__pick">
        <input
          ref={inputRef}
          type="file"
          accept="application/json,.json"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) onPickFile(file);
            event.target.value = '';
          }}
        />
        Open graph-map-data.json
      </label>
      <div className="graph-toolbar__source" title={sourceLabel}>
        {sourceLabel}
      </div>
      {error && <div className="graph-toolbar__error">{error}</div>}
    </div>
  );
}

export default function App() {
  const [sourceLabel, setSourceLabel] = useState('sample-data/graph-map-data.json');
  const [error, setError] = useState('');
  const initial = toFlowElements(defaultGraphData);
  const [nodes, setNodes] = useState(initial.nodes);
  const [edges, setEdges] = useState(applyMarkerDefaults(initial.edges));

  const loadGraphData = useCallback((raw, label) => {
    const parsed = validateGraphData(raw);
    const { nodes: nextNodes, edges: nextEdges } = toFlowElements(parsed);
    setNodes(nextNodes);
    setEdges(applyMarkerDefaults(nextEdges));
    setSourceLabel(label);
    setError('');
  }, []);

  const onPickFile = useCallback(
    async (file) => {
      try {
        const text = await file.text();
        const raw = JSON.parse(text);
        loadGraphData(raw, file.name);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Could not load that file.');
      }
    },
    [loadGraphData]
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
    <div className="app-shell">
      <GraphToolbar sourceLabel={sourceLabel} error={error} onPickFile={onPickFile} />
      <div className="graph-pane">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.2 }}
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>
    </div>
  );
}
