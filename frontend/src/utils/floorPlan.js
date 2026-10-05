export const FLOOR_DIRECTIONS = Object.freeze({ north: 'Север', south: 'Юг', west: 'Запад', east: 'Восток' });

export function normalizeFloorLandmarks(source = {}) {
  return Object.fromEntries(Object.keys(FLOOR_DIRECTIONS).map(key => [key, String(source?.[key] ?? '').trim()]));
}

export function planDraft(plan) {
  return {
    width: plan.width,
    height: plan.height,
    landmarks: normalizeFloorLandmarks(plan.landmarks),
    rooms: plan.rooms.filter(room => room.placement).map(room => ({ ...room.placement })),
  };
}

export function planSnapshot(plan) {
  return JSON.stringify({
    width: plan.width,
    height: plan.height,
    landmarks: normalizeFloorLandmarks(plan.landmarks),
    rooms: plan.rooms.map(({ audience_public_id, x, y, width, height }) =>
      ({ audience_public_id, x, y, width, height }))
      .sort((a, b) => a.audience_public_id.localeCompare(b.audience_public_id)),
  });
}

export function planError(plan) {
  const size = n => Number.isInteger(n) && n >= 1 && n <= 50;
  if (!size(plan.width) || !size(plan.height)) return 'Размер этажа: от 1 до 50 клеток.';
  if (Object.values(normalizeFloorLandmarks(plan.landmarks)).some(text => text.length > 128)) return 'Название ориентира: не больше 128 символов.';
  if (plan.rooms.length > 400) return 'На схеме может быть не больше 400 кабинетов.';
  const ids = new Set();
  for (let i = 0; i < plan.rooms.length; i++) {
    const room = plan.rooms[i];
    if (ids.has(room.audience_public_id)) return 'Кабинет уже размещён на схеме.';
    ids.add(room.audience_public_id);
    if (!size(room.width) || !size(room.height)
        || !Number.isInteger(room.x) || !Number.isInteger(room.y)
        || room.x < 0 || room.y < 0
        || room.x + room.width > plan.width || room.y + room.height > plan.height) {
      return 'Кабинет выходит за границы этажа.';
    }
    if (plan.rooms.slice(0, i).some(other =>
      room.x < other.x + other.width && room.x + room.width > other.x
      && room.y < other.y + other.height && room.y + room.height > other.y)) {
      return 'Кабинеты не должны пересекаться.';
    }
  }
  return '';
}

export function placeRoom(plan, placement) {
  return { ...plan, rooms: [...plan.rooms.filter(room =>
    room.audience_public_id !== placement.audience_public_id), placement] };
}

export function moveFromPointer(drag, clientX, clientY, rect, columns) {
  const cell = rect.width / columns;
  return {
    ...drag.room,
    x: drag.room.x + Math.round((clientX - rect.left - drag.localX) / cell),
    y: drag.room.y + Math.round((clientY - rect.top - drag.localY) / cell),
  };
}

export function resizeFromPointer(drag, clientX, clientY, rect, columns) {
  const cell = rect.width / columns;
  return {
    ...drag.room,
    width: Math.max(1, drag.room.width + Math.round((clientX - rect.left - drag.localX) / cell)),
    height: Math.max(1, drag.room.height + Math.round((clientY - rect.top - drag.localY) / cell)),
  };
}

export function pointInRect(x, y, rect) {
  return Boolean(rect && x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom);
}
