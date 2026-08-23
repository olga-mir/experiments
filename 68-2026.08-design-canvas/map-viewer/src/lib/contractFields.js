/** @typedef {{ name: string, type: string, note?: string }} ContractField */

/**
 * Accept structured arrays from graph-map-data.json or legacy prose strings.
 * @param {unknown} value
 * @returns {ContractField[]}
 */
export function normalizeFieldList(value) {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value.map((field) => ({
      name: field.name ?? field.field ?? '—',
      type: field.type ?? 'unknown',
      note: field.note ?? field.description,
    }));
  }
  if (typeof value === 'string') {
    return parseFieldString(value);
  }
  return [];
}

/** @param {string} raw */
function parseFieldString(raw) {
  const text = raw.trim();
  if (!text || text.toLowerCase() === 'none') {
    return [{ name: '—', type: 'none' }];
  }

  const eventMatch = text.match(/^Event\((.+)\)(.*)$/);
  if (eventMatch) {
    const suffix = eventMatch[2]?.replace(/^[\s—-]+/, '').trim();
    return eventMatch[1].split(',').map((part) => {
      const eq = part.indexOf('=');
      if (eq === -1) {
        return { name: part.trim(), type: 'unknown', note: suffix || undefined };
      }
      return {
        name: part.slice(0, eq).trim(),
        type: part.slice(eq + 1).trim(),
        note: suffix || undefined,
      };
    });
  }

  const parenMatch = text.match(/^([^(]+)\((.+)\)$/);
  if (parenMatch) {
    return [{ name: 'value', type: parenMatch[1].trim(), note: parenMatch[2].trim() }];
  }

  return [{ name: 'value', type: text }];
}
