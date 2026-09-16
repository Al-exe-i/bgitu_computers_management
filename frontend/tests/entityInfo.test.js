import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';
import { passwordStrength } from '../src/utils/passwordStrength.js';

function modal(api) {
  const source = readFileSync(new URL('../src/components/Common/EntityInfoModal.vue', import.meta.url), 'utf8')
    .split('<script>')[1].split('</script>')[0]
    .replace(/^import .*;\r?\n/gm, '').replace('export default', 'globalThis.component =');
  const context = vm.createContext({ api, ModalCloseButton: {} });
  vm.runInContext(source, context);
  const definition = context.component;
  const events = [];
  const instance = { ...definition.data(), endpoint: '/offices/1', editable: true,
    fields: [{ key: 'name' }, { key: 'description' }, { key: 'address', readonly: true }],
    $emit: (...args) => events.push(args) };
  for (const [key, fn] of Object.entries(definition.methods)) instance[key] = fn.bind(instance);
  for (const [key, fn] of Object.entries(definition.computed)) Object.defineProperty(instance, key, { get: fn.bind(instance) });
  return { instance, events };
}

test('metadata sends only changed editable fields and preserves explicit clearing', async () => {
  const calls = [];
  const { instance } = modal({ get: async () => ({ data: { name: 'Name', description: 'Text', address: 'Address' } }),
    patch: async (url, data) => { calls.push([url, data]); return { data }; } });
  await instance.load();
  instance.editing = true;
  await instance.save();
  assert.equal(calls.length, 0);
  instance.draft.description = '';
  instance.draft.address = 'Must not be sent';
  await instance.save();
  assert.equal(calls.length, 1);
  assert.equal(JSON.stringify(calls[0][1]), '{"description":null}');
  assert.equal(instance.record.address, 'Address');
  assert.equal(instance.dirty, false);
});

test('readonly and pending metadata changes cannot send duplicate requests or close', async () => {
  let resolve;
  let count = 0;
  const { instance, events } = modal({ patch: () => { count++; return new Promise(done => { resolve = done; }); } });
  Object.assign(instance, { loading: false, editing: true, draft: { name: 'Changed' }, editable: false });
  await instance.save();
  assert.equal(count, 0);
  instance.editable = true;
  const pending = instance.save();
  await instance.save();
  instance.close();
  assert.equal(events.length, 0);
  assert.equal(count, 1);
  resolve({ data: { name: 'Changed' } });
  await pending;
  assert.equal(events[0][0], 'saved');
});

test('failed metadata load can retry; late load cannot overwrite new response', async () => {
  let mode = 'fail', resolve;
  const { instance } = modal({ get: () => {
    if (mode === 'fail') throw new Error('secret');
    if (mode === 'slow') return new Promise(done => { resolve = done; });
    return { data: { name: 'New' } };
  } });
  await instance.load();
  assert.ok(instance.error);
  assert.equal(instance.error.includes('secret'), false);
  mode = 'slow';
  const old = instance.load();
  mode = 'success';
  await instance.load();
  resolve({ data: { name: 'Old' } });
  await old;
  assert.equal(instance.record.name, 'New');
  assert.equal(instance.error, '');
});

test('unsaved close requires confirmation and server error keeps the draft', async () => {
  const { instance, events } = modal({ patch: async () => { throw { response: { status: 403 } }; } });
  Object.assign(instance, { loading: false, editing: true, draft: { name: 'Changed' } });
  instance.close();
  assert.equal(instance.discardRequested, true);
  assert.equal(events.length, 0);
  await instance.save();
  assert.ok(instance.error);
  assert.equal(instance.draft.name, 'Changed');
  assert.equal(instance.saving, false);
});

test('password feedback handles empty, common, repetitive and long passwords', () => {
  assert.equal(passwordStrength('').score, 0);
  for (const value of ['1234567890123456', 'qwertyqwerty', 'Ab1!'.repeat(8), 'Пароль1234567890']) {
    assert.equal(passwordStrength(value).score, 1);
  }
  assert.equal(passwordStrength('Different-42').score, 2);
  assert.equal(passwordStrength('Different words 42!').score, 3);
});

test('fourteen varied characters get the highest score without weakening pattern checks', () => {
  for (const value of ['!rVks#HCD6=YM2', '!яДжк#ФБЦ6=ЮМ2']) {
    assert.equal(passwordStrength(value).score, 3);
  }
  assert.equal(passwordStrength('onlylowercases').score, 2);
  assert.equal(passwordStrength('Ab2!'.repeat(4)).score, 1);
  assert.equal(passwordStrength('Qwerty!94#Longer').score, 1);
});

test('identity uses only permitted fields without duplicating details', () => {
  const { instance } = modal({});
  Object.assign(instance, { kind: 'user', title: 'Пользователь',
    record: { name: 'Алексей', surname: 'Иванов', email: 'user@example.ru', role: 1 },
    fields: [{ key: 'email' }, { key: 'name' }, { key: 'surname' }, { key: 'role', format: () => 'Администратор' }] });
  assert.equal(instance.identity.heading, 'Алексей Иванов');
  assert.equal(instance.identity.initials, 'АИ');
  assert.equal(instance.identity.role, 'Администратор');
  assert.deepEqual(instance.detailFields.map(field => field.key), ['email']);
  instance.fields = [{ key: 'email' }];
  assert.equal(instance.identity.heading, 'user@example.ru');
  assert.equal(instance.identity.role, '');
  assert.equal(instance.identity.initials, '');
});

test('empty location name remains available instead of disappearing into heading', () => {
  const { instance } = modal({});
  Object.assign(instance, { kind: 'floor', title: '2 этаж', record: { name: null, description: null } });
  assert.equal(instance.identity.heading, '2 этаж');
  assert.equal(instance.identity.subtitle, '');
  assert.ok(instance.detailFields.some(field => field.key === 'name'));
});
