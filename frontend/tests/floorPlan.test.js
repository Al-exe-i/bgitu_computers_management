import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';
import * as geometry from '../src/utils/floorPlan.js';
import * as navigation from '../src/utils/officeNavigation.js';

const room = (id, x = 0, y = 0, width = 3, height = 2) => ({ audience_public_id: id, x, y, width, height });
const layout = (rooms = []) => ({ width: 20, height: 12, rooms });
const response = () => ({ ...layout(), office_id: 1, floor: 2, revision: 0, rooms: [
  { audience_public_id: 'a', number: 228, room_type: 'educational', placement: room('a') },
  { audience_public_id: 'b', number: 229, room_type: 'administrative', placement: null },
] });
const deferred = () => {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
};

function component({ get = async () => ({ data: response() }), put = async () => {}, confirm = () => true, role = 1 } = {}) {
  const source = readFileSync(new URL('../src/components/Common/FloorPlan.vue', import.meta.url), 'utf8')
    .split('<script>')[1].split('</script>')[0]
    .replace(/^import .*;\r?\n/gm, '').replace('export default', 'globalThis.component =');
  const navigations = [];
  const auth = { isAuthenticated: role !== null, user: role === null ? null : { role } };
  const context = vm.createContext({ ...geometry, ...navigation, ContextHelp: {}, api: { get, put }, window: { confirm },
    useAuthStore: () => auth, useThemeStore: () => ({ isDark: false }),
    useAudienceContext: () => ({ setOffice() {} }) });
  vm.runInContext(source, context);
  const definition = context.component;
  const instance = { ...definition.data(), officeId: 1, floor: 2, matchingIds: null,
    $router: { push: route => navigations.push(route) }, $emit() {},
    $refs: { grid: { getBoundingClientRect: () => ({ left: 0, top: 0, width: 640 }) } } };
  for (const [key, fn] of Object.entries(definition.methods)) instance[key] = fn.bind(instance);
  for (const [key, fn] of Object.entries(definition.computed)) Object.defineProperty(instance, key, { get: fn.bind(instance) });
  instance.accept(response());
  instance.loading = false;
  instance.editing = true;
  return { instance, definition, auth, navigations };
}

test('search highlights placed and unplaced matches without changing layout or selection', () => {
  const { instance } = component();
  const snapshot = geometry.planSnapshot(instance.draft);
  instance.selectedId = 'a';
  instance.matchingIds = ['b'];
  assert.equal(instance.matchingCount, 1);
  assert.equal(instance.matchesFilter(instance.plan.rooms[0]), false);
  assert.equal(instance.matchesFilter(instance.plan.rooms[1]), true);
  instance.matchingIds = [];
  assert.equal(instance.matchingCount, 0);
  instance.matchingIds = null;
  assert.equal(instance.matches, null);
  assert.equal(instance.matchesFilter(instance.plan.rooms[0]), true);
  assert.equal(instance.selectedId, 'a');
  assert.equal(geometry.planSnapshot(instance.draft), snapshot);
});

test('inspector is before the canvas, not after it', () => {
  const source = readFileSync(new URL('../src/components/Common/FloorPlan.vue', import.meta.url), 'utf8');
  assert.ok(source.indexOf('class="fp-inspector"') < source.indexOf('class="fp-compass"'));
  assert.match(source, /\.fp-inspector \{ position: sticky;/);
});

test('draft copies only placements; snapshot ignores order and revision', () => {
  const data = response();
  const draft = geometry.planDraft(data);
  draft.rooms[0].x = 2;
  assert.equal(data.rooms[0].placement.x, 0);
  assert.equal(draft.rooms.length, 1);
  const a = layout([room('a'), room('b', 3)]);
  assert.equal(geometry.planSnapshot(a), geometry.planSnapshot({ ...a, revision: 3, rooms: [...a.rooms].reverse() }));
});

test('landmark edits are tracked, normalized and saved without changing geometry', async () => {
  let payload;
  const { instance } = component({ put: async (_, data) => {
    payload = data;
    return { data: { ...response(), landmarks: data.landmarks, revision: 1 } };
  } });
  instance.draft.landmarks.north = 'Лестница';
  assert.equal(instance.dirty, true);
  await instance.save();
  assert.equal(payload.landmarks.north, 'Лестница');
  assert.equal(instance.dirty, false);
  instance.draft.landmarks.north = 'Лестница  ';
  assert.equal(instance.dirty, false);
  instance.draft.landmarks.west = 'x'.repeat(129);
  assert.ok(geometry.planError(instance.draft));
});

test('geometry allows shared edges and rejects overlaps, duplicate IDs, bounds and nonintegers', () => {
  assert.equal(geometry.planError(layout([room('a'), room('b', 3)])), '');
  for (const plan of [layout([room('a'), room('b', 2)]), layout([room('a'), room('a', 3)]),
    layout([room('a', -1)]), layout([room('a', 19)]), layout([room('a', 0.5)]),
    layout([room('a', 0, 0, 0)]), { ...layout(), width: NaN }, { ...layout(), height: 51 }]) {
    assert.notEqual(geometry.planError(plan), '');
  }
});

test('in-place landmark changes are applied explicitly, not while typing', () => {
  const { instance } = component();
  instance.$nextTick = fn => fn();
  instance.editLandmark('west');
  instance.landmarkDraft = '  Вход  ';
  assert.equal(instance.dirty, false);
  instance.editingLandmark = null;
  assert.equal(instance.dirty, false);
  instance.editLandmark('east');
  instance.landmarkDraft = '  Окна  ';
  instance.saveLandmark();
  assert.equal(instance.draft.landmarks.east, 'Окна');
  assert.equal(instance.editingLandmark, null);
  assert.equal(instance.dirty, true);
});

test('pointer movement accounts for scrolled grid and snaps to cells', () => {
  const drag = { room: room('a', 2, 3), localX: 80, localY: 110 };
  const moved = geometry.moveFromPointer(drag, 116, 162, { left: 4, top: 20, width: 640 }, 20);
  assert.equal(moved.x, 3);
  assert.equal(moved.y, 4);
  assert.equal(drag.room.x, 2);
});

test('unchanged draft does not send PUT; successful save updates baseline and revision', async () => {
  let calls = 0;
  const { instance } = component({ put: async (url, payload) => {
    calls++;
    assert.equal(url, '/offices/1/floors/2/plan');
    assert.equal(payload.revision, 0);
    const data = response();
    data.revision = 1;
    data.rooms[0].placement = payload.rooms[0];
    return { data };
  } });
  await instance.save();
  assert.equal(calls, 0);
  instance.commit(geometry.placeRoom(instance.draft, room('a', 4)));
  await instance.save();
  assert.equal(calls, 1);
  assert.equal(instance.plan.revision, 1);
  assert.equal(instance.dirty, false);
});

test('conflict preserves draft and blocks blind retry until explicit reload', async () => {
  let calls = 0;
  const { instance } = component({ put: async () => { calls++; throw { response: { status: 409 } }; } });
  instance.commit(geometry.placeRoom(instance.draft, room('a', 4)));
  await instance.save();
  assert.equal(instance.conflict, true);
  assert.equal(instance.draft.rooms[0].x, 4);
  assert.equal(instance.dirty, true);
  await instance.save();
  assert.equal(calls, 1);
  await instance.load();
  assert.equal(instance.conflict, false);
  assert.equal(instance.dirty, false);
});

test('saving blocks mutations, repeated save and reload', async () => {
  const request = deferred();
  let calls = 0;
  const { instance } = component({ put: () => { calls++; return request.promise; } });
  instance.commit(geometry.placeRoom(instance.draft, room('a', 4)));
  const pending = instance.save();
  assert.equal(instance.saving, true);
  assert.equal(instance.commit(layout()), false);
  await instance.save();
  await instance.load();
  instance.discard();
  assert.equal(instance.draft.rooms[0].x, 4);
  assert.equal(calls, 1);
  request.resolve({ data: response() });
  await pending;
});

test('failed save and rejected reload confirmation preserve edits', async () => {
  const { instance } = component({ put: async () => { throw new Error('network'); }, confirm: () => false });
  instance.commit(geometry.placeRoom(instance.draft, room('a', 4)));
  await instance.save();
  await instance.load();
  instance.discard();
  assert.equal(instance.saving, false);
  assert.equal(instance.draft.rooms[0].x, 4);
  assert.equal(instance.dirty, true);
});

test('late response after unmount cannot change state', async () => {
  const request = deferred();
  const { instance, definition } = component({ get: () => request.promise });
  const pending = instance.load();
  definition.beforeUnmount.call(instance);
  const data = response();
  data.revision = 99;
  request.resolve({ data });
  await pending;
  assert.equal(instance.plan.revision, 0);
});

test('guests and teachers can navigate but cannot change or save plan', async () => {
  for (const role of [null, 2]) {
    const { instance, navigations } = component({ role, put: () => assert.fail('unexpected write') });
    assert.equal(instance.commit(layout()), false);
    await instance.save();
    instance.editing = false;
    instance.activate(response().rooms[0]);
    assert.equal(navigations[0].params.audiencePublicId, 'a');
  }
});

test('invalid resizing and pointer cancellation leave saved positions intact', () => {
  const { instance } = component();
  const event = { target: { value: '2' } };
  instance.resizePlan('width', event);
  assert.equal(instance.draft.width, 20);
  assert.equal(event.target.value, 20);
  const pointer = { pointerId: 1, isPrimary: true, button: 0, clientX: 10, clientY: 10,
    currentTarget: { setPointerCapture() {} } };
  instance.startDrag(pointer, response().rooms[0]);
  instance.moveDrag({ ...pointer, clientX: 110 });
  assert.ok(instance.preview);
  instance.cancelPointer({ pointerId: 2 });
  assert.ok(instance.preview);
  instance.cancelPointer({ pointerId: 1 });
  assert.equal(instance.dirty, false);
  assert.equal(instance.preview, null);
});

test('unplacing retains room metadata and auto placement cannot overlap other rooms', () => {
  const { instance } = component();
  instance.selectedId = 'b';
  instance.placeFirstFree();
  assert.equal(instance.selectedPlacement.x, 3);
  assert.equal(geometry.planError(instance.draft), '');
  instance.unplace();
  assert.equal(instance.unplacedRooms[0].audience_public_id, 'b');
  assert.equal(instance.dirty, false);
});

function officeComponent(confirm = () => false) {
  const scrolls = [];
  const source = readFileSync(new URL('../src/views/OfficeView.vue', import.meta.url), 'utf8')
    .split('<script>')[1].split('</script>')[0]
    .replace(/^import .*;\r?\n/gm, '').replace('export default', 'globalThis.component =');
  const context = vm.createContext({ ...navigation, FloorSection: {}, LoaderContainer: {},
    EntityInfoModal: {}, OFFICE_INFO_FIELDS: [],
    document: { getElementById: id => ({ scrollIntoView: () => scrolls.push(id) }) },
    window: { confirm, localStorage: { getItem: () => null, setItem() {} } },
    useNotificationsStore: () => ({ info() {} }),
  });
  vm.runInContext(source, context);
  const definition = context.component;
  const instance = { ...definition.data(), $nextTick: () => Promise.resolve() };
  for (const [key, fn] of Object.entries(definition.methods)) instance[key] = fn.bind(instance);
  for (const [key, fn] of Object.entries(definition.computed)) Object.defineProperty(instance, key, { get: fn.bind(instance) });
  return { instance, definition, scrolls };
}

test('return scroll waits for all floor plans and runs only once', async () => {
  const { instance, definition, scrolls } = officeComponent();
  instance.$route = { query: { view: 'plan', floor: '3' } };
  assert.equal(definition.data.call(instance).audienceViewMode, 'plan');
  instance.audienceViewMode = 'plan';
  instance.returnPositionPending = true;
  instance.office = { id: 1 };
  instance.floors = { 2: {}, 3: {} };
  instance.floorPlansReady = { 2: true };
  await instance.restoreFloorPosition();
  assert.equal(scrolls.length, 0);
  instance.floorPlansReady[3] = true;
  await instance.restoreFloorPosition();
  await instance.restoreFloorPosition();
  assert.deepEqual(scrolls, ['office-1-floor-3']);
});

test('mode and route changes preserve drafts when leave confirmation is rejected', () => {
  const { instance, definition } = officeComponent();
  instance.audienceViewMode = 'plan';
  instance.planStates = { 2: { dirty: true, saving: false } };
  instance.setAudienceViewMode('cards');
  assert.equal(instance.audienceViewMode, 'plan');
  assert.equal(instance.planStates[2].dirty, true);
  assert.equal(definition.beforeRouteLeave.call(instance), false);
  assert.equal(definition.beforeRouteUpdate.call(instance,
    { params: { officeNumber: '2' } }, { params: { officeNumber: '1' } }), false);
  let prevented = false;
  instance.handlePlanBeforeUnload({ preventDefault: () => { prevented = true; } });
  assert.equal(prevented, true);
});

test('filtering does not unmount floor editors or remove their rooms', () => {
  const { instance } = officeComponent();
  const audiences = [{ public_id: 'a', number: 228, hardware: [{ state: false }] },
    { public_id: 'b', number: 229, hardware: [] }];
  instance.floors = { 2: { number: 2, audiences } };
  instance.audienceViewMode = 'plan';
  instance.filterMode = 'broken';
  instance.applyFilters();
  assert.equal(instance.visibleFloors[2].audiences.length, 2);
  assert.deepEqual(Array.from(instance.floorMatchingIds('2')), ['a']);
  instance.searchField = '000';
  instance.applyFilters();
  assert.equal(instance.visibleFloors[2].audiences.length, 2);
  assert.equal(instance.floorMatchingIds('2').length, 0);
});

test('leaving while saving is blocked even when discard confirmation would be accepted', () => {
  const { instance } = officeComponent(() => true);
  instance.planStates = { 2: { dirty: false, saving: true } };
  assert.equal(instance.confirmPlanLeave(), false);
});
