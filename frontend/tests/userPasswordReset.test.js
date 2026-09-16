import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';

function component(post = async () => {}, isSuperuser = true) {
  const source = readFileSync(new URL('../src/components/Layout/Settings/System/ManageUsers.vue', import.meta.url), 'utf8')
    .split('<script>')[1].split('</script>')[0]
    .replace(/^import[\s\S]*?from\s+['"][^'"]+['"];\r?\n/gm, '')
    .replace('export default', 'globalThis.component =');
  const context = vm.createContext({ api: { post }, ModalCloseButton: {},
    EntityInfoModal: {}, PasswordEyeButton: {}, PasswordStrength: {}, RoleHelp: {},
    document: { body: { style: { overflow: '' } }, addEventListener() {}, removeEventListener() {} } });
  vm.runInContext(source, context);
  const definition = context.component;
  const instance = { ...definition.data(), isSuperuser, authStore: { user: { id: 1 } },
    notify: { success() {} }, $refs: {}, $nextTick: fn => fn() };
  for (const [key, fn] of Object.entries(definition.methods)) instance[key] = fn.bind(instance);
  return instance;
}
const target = { id: 7, email: 'teacher@example.ru', is_superuser: false };

test('only SU can open reset for another non-SU user', () => {
  const form = component();
  assert.equal(form.canResetPassword(target), true);
  assert.equal(form.canResetPassword({ ...target, id: 1 }), false);
  assert.equal(form.canResetPassword({ ...target, is_superuser: true }), false);
  assert.equal(component(undefined, false).canResetPassword(target), false);
});

test('invalid and mismatching passwords do not send a request', async () => {
  const form = component(() => assert.fail('Unexpected request'));
  form.openPasswordModal(target);
  for (const [password, repeat] of [['short', 'short'], ['x'.repeat(129), 'x'.repeat(129)], ['newpass', 'different']]) {
    form.passwordForm = { password, repeat };
    await form.resetPassword();
    assert.ok(form.passwordError);
  }
});

test('pending reset cannot close or send twice; successful reset clears secrets', async () => {
  let resolve;
  const calls = [];
  const form = component((...args) => { calls.push(args); return new Promise(done => { resolve = done; }); });
  form.openPasswordModal(target);
  form.passwordForm = { password: 'newpass', repeat: 'newpass' };
  const pending = form.resetPassword();
  form.closePasswordModal();
  await form.resetPassword();
  assert.equal(form.passwordTarget, target);
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0], '/users/7/password');
  assert.equal(calls[0][1].new_password, 'newpass');
  resolve();
  await pending;
  assert.equal(form.passwordTarget, null);
  assert.equal(form.passwordForm.password, '');
  assert.equal(form.passwordForm.repeat, '');
});

test('server errors remain in the modal without exposing server payload', async () => {
  const form = component(async () => { throw { response: { status: 403, data: { detail: 'secret' } } }; });
  form.openPasswordModal(target);
  form.passwordForm = { password: 'newpass', repeat: 'newpass' };
  await form.resetPassword();
  assert.equal(form.passwordTarget, target);
  assert.equal(form.passwordLoading, false);
  assert.ok(form.passwordError);
  assert.equal(form.passwordError.includes('secret'), false);
  form.closePasswordModal();
  assert.equal(form.passwordForm.password, '');
});
