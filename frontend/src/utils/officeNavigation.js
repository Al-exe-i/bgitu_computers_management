const MODES = new Set(['cards', 'compact', 'plan']);

export function officeView(value) {
  return typeof value === 'string' && MODES.has(value) ? value : null;
}

export function officeFloor(value) {
  if (typeof value !== 'string' && typeof value !== 'number') return null;
  if (String(value).trim() === '') return null;
  const floor = Number(value);
  return Number.isSafeInteger(floor) ? floor : null;
}

export function audienceOriginQuery(view, floor) {
  const mode = officeView(view);
  const number = officeFloor(floor);
  return mode ? { officeView: mode, ...(number === null ? {} : { officeFloor: String(number) }) } : {};
}

export function preserveAudienceOrigin(query = {}) {
  return audienceOriginQuery(query.officeView, query.officeFloor);
}

export function officeBackLocation(classroom, query = {}) {
  if (!classroom?.office_id) return { name: 'Home' };
  const floor = officeFloor(query.officeFloor) ?? officeFloor(classroom.floor);
  return { name: 'Office', params: { officeNumber: String(classroom.office_id) },
    query: { view: officeView(query.officeView) ?? 'cards', ...(floor === null ? {} : { floor: String(floor) }) } };
}
