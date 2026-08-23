import { normalizeFieldList } from '../lib/contractFields.js';

function FieldSection({ title, fields }) {
  if (!fields.length) return null;

  return (
    <section className="contract-io">
      <div className="contract-io__heading">{title}</div>
      <ul className="contract-io__list">
        {fields.map((field) => (
          <li key={`${field.name}-${field.type}`} className="contract-io__row">
            <span className="contract-io__name">{field.name}</span>
            <span className="contract-io__type">{field.type}</span>
            {field.note && <span className="contract-io__note">{field.note}</span>}
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function ContractDetails({ contract }) {
  const inputs = normalizeFieldList(contract.inputs);
  const outputs = normalizeFieldList(contract.outputs);

  return (
    <div className="contract-details">
      <FieldSection title="IN" fields={inputs} />
      <FieldSection title="OUT" fields={outputs} />
      {contract.reads?.length > 0 && (
        <div className="contract-meta">
          <span className="contract-meta__label">reads</span>
          {contract.reads.join(', ')}
        </div>
      )}
      {contract.writes?.length > 0 && (
        <div className="contract-meta">
          <span className="contract-meta__label">writes</span>
          {contract.writes.join(', ')}
        </div>
      )}
      {contract.sideEffects?.length > 0 && (
        <div className="contract-meta">
          <span className="contract-meta__label">side fx</span>
          <ul className="contract-meta__list">
            {contract.sideEffects.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      )}
      <div className="contract-meta">
        <span className="contract-meta__label">idempotent</span>
        {String(contract.idempotent)}
      </div>
      <div className="contract-meta">
        <span className="contract-meta__label">on failure</span>
        {contract.failureBehavior}
      </div>
    </div>
  );
}
