import { useState } from 'react';
import { Handle, Position } from 'reactflow';
import ContractDetails from './ContractDetails.jsx';

export default function ContractNode({ data }) {
  const [expanded, setExpanded] = useState(false);
  const c = data.contract;
  const expandable = Boolean(c);

  return (
    <div
      className={`contract-node${expanded ? ' contract-node--expanded' : ''}${c?.idempotent ? ' contract-node--idempotent' : ' contract-node--mutating'}`}
      onClick={() => expandable && setExpanded((value) => !value)}
    >
      <Handle type="target" position={Position.Left} className="contract-node__handle" />

      {expandable && (
        <span className="contract-node__toggle" aria-hidden="true">
          {expanded ? '−' : '+'}
        </span>
      )}

      <div className="contract-node__label">{data.label}</div>

      {expanded && c && <ContractDetails contract={c} />}

      <Handle type="source" position={Position.Right} className="contract-node__handle" />
    </div>
  );
}
