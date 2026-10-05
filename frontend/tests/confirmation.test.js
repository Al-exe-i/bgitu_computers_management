import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';
import { createConfirmationScope, confirmationRequest, answerConfirmation } from '../src/services/confirmation.js';

const answer = accepted => answerConfirmation(confirmationRequest.value.id, accepted);

test('confirmation waits for an explicit answer and settles only once', async () => {
  const scope = createConfirmationScope();
  let settled = false;
  const result = scope.ask({ title: 'Удалить?', tone: 'danger' }).then(value => { settled = true; return value; });
  await Promise.resolve();
  assert.equal(settled, false);
  const id = confirmationRequest.value.id;
  answerConfirmation(id + 1, true);
  assert.equal(confirmationRequest.value.id, id);
  answer(true);
  answerConfirmation(id, false);
  assert.equal(await result, true);
  assert.equal(confirmationRequest.value, null);
});

test('competing clicks are cancelled rather than queued or sharing an approval', async () => {
  const scope = createConfirmationScope();
  const first = scope.ask({ title: 'Первое действие' });
  assert.equal(await scope.ask({ title: 'Второе действие' }), false);
  assert.equal(await createConfirmationScope().ask({ title: 'Другая страница' }), false);
  assert.equal(confirmationRequest.value.title, 'Первое действие');
  answer(false);
  assert.equal(await first, false);
});

test('owner unmount cancels its dialog and invalidates an already resolved approval', async () => {
  const scope = createConfirmationScope();
  const first = scope.ask({});
  scope.cancel();
  assert.equal(await first, false);
  assert.equal(await scope.ask({}), false);
  const next = createConfirmationScope();
  const result = next.ask({});
  answer(true);
  next.cancel();
  assert.equal(await result, false);
});

test('unmounting a different owner cannot close the active dialog', async () => {
  const owner = createConfirmationScope();
  const other = createConfirmationScope();
  const result = owner.ask({});
  other.cancel();
  assert.ok(confirmationRequest.value);
  answer(false);
  assert.equal(await result, false);
});

function component(file, extra = {}) {
  const source = readFileSync(new URL(`../src/${file}`, import.meta.url), 'utf8')
    .split('<script>')[1].split('</script>')[0]
    .replace(/^import[\s\S]*?from\s+['"][^'"]+['"];[^\r\n]*\r?\n/gm, '')
    .replace('export default', 'globalThis.component =');
  const writes = [];
  const context = vm.createContext({
    createConfirmationScope, ModalCloseButton: {}, EntityInfoModal: {}, OFFICE_INFO_FIELDS: [],
    PasswordEyeButton: {}, PasswordStrength: {}, RoleHelp: {}, RealtimeNotificationsSection: {}, TrustedSvgIcon: {},
    api: { delete: async url => { writes.push(url); }, post: async () => ({ data: { public_id: 'new-room' } }) },
    router: { push() {} }, document: { removeEventListener() {}, body: { style: {} } }, window: { removeEventListener() {} },
  });
  vm.runInContext(source, context);
  const definition = context.component;
  const instance = { ...definition.data(), notify: { success() {}, info() {}, error() {}, warning() {} }, ...extra };
  for (const [key, fn] of Object.entries(definition.methods)) instance[key] = fn.bind(instance);
  return { instance, definition, writes, context };
}

const cases = [
  { file: 'components/Layout/Settings/System/ManageUsers.vue', method: 'deleteUser', target: { id: 7, email: 'test@example.ru', is_superuser: false },
    extra: { isSuperuser: true, authStore: { user: { id: 1 } }, users: [{ id: 7, is_superuser: false }] } },
  { file: 'components/Layout/Settings/System/ManageOffices.vue', method: 'deleteOffice', target: { id: 2, address: 'Университет' },
    extra: { isSuperuser: true, offices: [{ id: 2 }], officeStore: { removeOffice() {} } } },
  { file: 'components/Layout/Settings/System/ManageAudiences.vue', method: 'deleteAudience', target: { id: 7, public_id: 'room', number: 111, office_id: 1, floor: 1 },
    extra: { isAdmin: true, audiences: [{ id: 7 }] } },
  { file: 'components/Layout/Settings/UserProfile.vue', method: 'handleDeleteAvatar',
    extra: { authStore: { user: { id: 7 }, async fetchUser() {} }, userPhoto: 'photo.jpg' } },
];

for (const item of cases) {
  test(`${item.method}: no request before approval or after cancellation`, async () => {
    const { instance, writes } = component(item.file, item.extra);
    const pending = instance[item.method](item.target);
    assert.equal(writes.length, 0);
    assert.equal(confirmationRequest.value.tone, 'danger');
    await instance[item.method](item.target);
    answer(false);
    await pending;
    assert.equal(writes.length, 0);
    const approved = instance[item.method](item.target);
    answer(true);
    await approved;
    assert.equal(writes.length, 1);
  });
  test(`${item.method}: unmount cancels pending deletion`, async () => {
    const { instance, writes, definition } = component(item.file, item.extra);
    const pending = instance[item.method](item.target);
    definition.beforeUnmount.call(instance);
    await pending;
    assert.equal(writes.length, 0);
    assert.equal(confirmationRequest.value, null);
  });
}

test('permission loss during confirmation prevents user deletion', async () => {
  const item = cases[0];
  const { instance, writes } = component(item.file, item.extra);
  const pending = instance.deleteUser(item.target);
  instance.isSuperuser = false;
  answer(true);
  await pending;
  assert.equal(writes.length, 0);
});

test('equipment outside a reduced grid requires approval and a matching snapshot', async () => {
  const { instance, context } = component('components/Layout/CreateAudience.vue', {
    classroomNumber: 111, roomType: 'administrative', isEditMode: false,
    outOfBoundsEquipmentItems: [{ x: 7 }],
  });
  let calls = 0;
  context.api.post = async () => { calls++; return { data: { public_id: 'new-room' } }; };
  const cancelled = instance.saveClassroom();
  assert.equal(calls, 0);
  answer(false);
  await cancelled;
  assert.equal(calls, 0);
  const stale = instance.saveClassroom();
  instance.gridWidth++;
  answer(true);
  await stale;
  assert.equal(calls, 0);
  const accepted = instance.saveClassroom();
  answer(true);
  await accepted;
  assert.equal(calls, 1);
});
