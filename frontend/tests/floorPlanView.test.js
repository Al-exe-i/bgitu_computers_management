import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';
import { readFloorView, saveFloorView } from '../src/utils/floorPlanViewState.js';
import { officeFloor } from '../src/utils/officeNavigation.js';

test('view state is bounded, normalized and works without storage', () => {
  let value = '[]';
  const storage = { getItem: () => value, setItem: (_, data) => { value = data; } };
  for (let floor = 0; floor < 30; floor++) saveFloorView(`1:${floor}`, { search: '22', x: 100, y: 200, pageY: 300 }, storage);
  assert.equal(JSON.parse(value).length, 20);
  assert.equal(readFloorView('1:0', storage).search, '');
  assert.deepEqual(readFloorView('1:29', storage), { search: '22', x: 100, y: 200, pageY: 300 });
  saveFloorView('1:29', { search: 'a'.repeat(150), x: -1, y: Infinity }, storage);
  assert.equal(readFloorView('1:29', storage).search.length, 100);
  assert.equal(readFloorView('1:29', storage).x, 0);
  assert.equal(readFloorView('1:29', storage).y, 0);
  assert.doesNotThrow(() => saveFloorView('1:1', {}, null));
  assert.deepEqual(readFloorView('1:1', null), { search: '', x: 0, y: 0, pageY: 0 });
  value = '{invalid';
  assert.equal(readFloorView('1:1', storage).search, '');
});

function page(get, confirm = () => false) {
  const source = readFileSync(new URL('../src/views/FloorPlanView.vue', import.meta.url), 'utf8')
    .split('<script>')[1].split('</script>')[0].replace(/^import .*;\r?\n/gm, '')
    .replace('export default', 'globalThis.component =');
  const context = vm.createContext({ api: { get }, FloorPlan: {}, EntityInfoModal: {}, FLOOR_INFO_FIELDS: [], officeFloor,
    readFloorView: () => ({ search: '', x: 0, y: 0, pageY: 0 }), saveFloorView() {},
    useNotificationsStore: () => ({ info() {} }), window: { confirm, scrollY: 0, scrollTo() {} } });
  vm.runInContext(source, context);
  const definition = context.component;
  const instance = { ...definition.data(), officeNumber: '1', floorNumber: '2', $route: { query: {} }, $refs: {} };
  for (const [key, fn] of Object.entries(definition.methods)) instance[key] = fn.bind(instance);
  for (const [key, fn] of Object.entries(definition.computed)) Object.defineProperty(instance, key, { get: fn.bind(instance) });
  return instance;
}

test('floor leave is blocked while saving and dirty drafts need confirmation', () => {
  const instance = page();
  instance.editState.saving = true;
  assert.equal(instance.allowLeave(), false);
  instance.editState = { saving: false, dirty: true };
  assert.equal(instance.allowLeave(), false);
  instance.editState.dirty = false;
  assert.equal(instance.allowLeave(), true);
});

test('late office response cannot replace a newly selected building', async () => {
  let resolve;
  const pending = new Promise(done => { resolve = done; });
  const instance = page(url => url.endsWith('/1') ? pending : Promise.resolve({ data: { id: 2, audiences: [{ floor: 2 }] } }));
  const first = instance.load();
  instance.officeNumber = '2';
  await instance.load();
  resolve({ data: { id: 1, audiences: [] } });
  await first;
  assert.equal(instance.office.id, 2);
  assert.equal(instance.error, '');
});

test('missing floors and malformed routes display an error instead of an editor', async () => {
  let calls = 0;
  const instance = page(async () => { calls++; return { data: { audiences: [{ floor: 3 }] } }; });
  await instance.load();
  assert.match(instance.error, /нет указанного этажа/);
  instance.floorNumber = 'NaN';
  await instance.load();
  assert.match(instance.error, /Некорректный адрес/);
  assert.equal(calls, 1);
  assert.equal(instance.loading, false);
});

test('search on the floor page never removes rooms from the source data', () => {
  const instance = page();
  instance.office = { audiences: [{ floor: 2, number: 228, public_id: 'a' }, { floor: 2, number: 229, public_id: 'b' }] };
  instance.search = '228';
  assert.deepEqual(Array.from(instance.matchingIds), ['a']);
  instance.search = '000';
  assert.equal(instance.matchingIds.length, 0);
  instance.search = '';
  assert.equal(instance.matchingIds, null);
  assert.equal(instance.office.audiences.length, 2);
});

test('scroll restoration waits for render and ignores an obsolete page', async () => {
  const instance = page();
  let restoreCount = 0;
  instance.$refs.plan = { getScrollElement: () => ({ scrollTo: () => { restoreCount++; } }) };
  instance.$nextTick = async () => {};
  await instance.restorePosition();
  assert.equal(restoreCount, 1);
  instance.$nextTick = async () => { instance.requestId++; };
  await instance.restorePosition();
  assert.equal(restoreCount, 1);
  instance.editState = { dirty: true, saving: false };
  let prevented = false;
  instance.beforeUnload({ preventDefault: () => { prevented = true; } });
  assert.equal(prevented, true);
});
