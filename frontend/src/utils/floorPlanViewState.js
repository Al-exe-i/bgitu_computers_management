const STORAGE_KEY = 'bgitu-floor-view-state';
const LIMIT = 20;

function browserStorage() {
  try { return globalThis.sessionStorage; } catch { return null; }
}

function entries(storage) {
  try {
    const data = JSON.parse(storage.getItem(STORAGE_KEY) || '[]');
    return Array.isArray(data) ? data.filter(item => Array.isArray(item) && typeof item[0] === 'string').slice(-LIMIT) : [];
  } catch { return []; }
}

function normalize(value = {}) {
  const position = input => Number.isFinite(input) ? Math.max(0, Math.min(input, 100000)) : 0;
  return { search: typeof value?.search === 'string' ? value.search.slice(0, 100) : '',
    x: position(value?.x), y: position(value?.y), pageY: position(value?.pageY) };
}

export function readFloorView(key, storage = browserStorage()) {
  return normalize(entries(storage).find(item => item[0] === key)?.[1]);
}

export function saveFloorView(key, value, storage = browserStorage()) {
  try {
    const data = entries(storage).filter(item => item[0] !== key);
    data.push([key, normalize(value)]);
    storage.setItem(STORAGE_KEY, JSON.stringify(data.slice(-LIMIT)));
  } catch { /* Схема доступна и при запрете браузерного хранилища. */ }
}
