import { useState } from 'react';
import { Handle, Position } from 'reactflow';

export default function ContractNode({ data }) {
  const [expanded, setExpanded] = useState(false);
  const c = data.contract;

  return (
    <div
      onClick={() => setExpanded((e) => !e)}
      style={{
        border: '1px solid #444',
        borderRadius: 8,
        padding: '8px 12px',
        background: c?.idempotent ? '#f0fdf4' : '#fef2f2',
        minWidth: 160,
        cursor: 'pointer',
        fontFamily: 'ui-sans-serif, system-ui',
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: '#64748b' }} />
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
      <Handle type="source" position={Position.Right} style={{ background: '#64748b' }} />
    </div>
  );
}
