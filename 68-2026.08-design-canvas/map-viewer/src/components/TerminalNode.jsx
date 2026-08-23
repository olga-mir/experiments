import { Handle, Position } from 'reactflow';

export default function TerminalNode({ data }) {
  const isStart = data.kind === 'start';

  return (
    <div
      style={{
        border: '2px solid #334155',
        borderRadius: isStart ? 999 : 8,
        padding: isStart ? '6px 14px' : '6px 12px',
        background: isStart ? '#e0f2fe' : '#f1f5f9',
        fontFamily: 'ui-sans-serif, system-ui',
        fontSize: 12,
        fontWeight: 600,
        color: '#0f172a',
        minWidth: isStart ? undefined : 72,
        textAlign: 'center',
      }}
    >
      {!isStart && (
        <Handle type="target" position={Position.Left} style={{ background: '#64748b' }} />
      )}
      <div>{data.label}</div>
      {isStart && (
        <Handle type="source" position={Position.Right} style={{ background: '#64748b' }} />
      )}
    </div>
  );
}
