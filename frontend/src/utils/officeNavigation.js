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

export function audienceOriginQuery(view, floor, search = '') {
  const mode = officeView(view);
  const number = officeFloor(floor);
  return mode ? { officeView: mode, ...(number === null ? {} : { officeFloor: String(number) }),
    ...(mode === 'plan' && typeof search === 'string' && search ? { officeSearch: search.slice(0, 100) } : {}) } : {};
}

export function preserveAudienceOrigin(query = {}) {
  return audienceOriginQuery(query.officeView, query.officeFloor, query.officeSearch);
}

export function officeBackLocation(classroom, query = {}) {
  if (!classroom?.office_id) return { name: 'Home' };
  const floor = officeFloor(query.officeFloor) ?? officeFloor(classroom.floor);
  if (officeView(query.officeView) === 'plan' && floor !== null) {
    return { name: 'FloorPlan', params: { officeNumber: String(classroom.office_id), floorNumber: String(floor) },
      query: { q: typeof query.officeSearch === 'string' ? query.officeSearch.slice(0, 100) : '' } };
  }
  return { name: 'Office', params: { officeNumber: String(classroom.office_id) },
    query: { view: officeView(query.officeView) ?? 'cards', ...(floor === null ? {} : { floor: String(floor) }) } };
}

export function audienceBackLabel(query = {}) {
  return officeView(query.officeView) === 'plan' ? 'К схеме этажа' : 'К списку аудиторий';
}
