import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';

function form() {
  const writes = [];
  const warnings = [];
  const context = vm.createContext({ TrustedSvgIcon: {}, document: {},
    api: { post: async (url, payload) => { writes.push(payload); return { data: { public_id: 'room-id' } }; } },
    router: { push() {} },
  });
  const source = readFileSync(new URL('../src/components/Layout/CreateAudience.vue', import.meta.url), 'utf8')
    .split('<script>')[1].split('</script>')[0]
    .replace(/^import .*;\r?\n/gm, '').replace('export default', 'globalThis.component =');
  vm.runInContext(source, context);
  const definition = context.component;
  const instance = { ...definition.data(), isEditMode: false, outOfBoundsEquipmentItems: [],
    notify: { warning: message => warnings.push(message), success() {}, error: message => assert.fail(message) },
    $nextTick: callback => Promise.resolve().then(callback),
  };
  for (const [key, fn] of Object.entries(definition.methods)) instance[key] = fn.bind(instance);
  return { instance, writes, warnings };
}

test('administrative cabinet can be created without equipment; educational validation is preserved', () => {
  const { instance, writes, warnings } = form();
  instance.classroomNumber = '105';
  instance.saveClassroom();
  assert.equal(writes.length, 0);
  assert.equal(warnings.length, 1);
  instance.roomType = 'administrative';
  instance.saveClassroom();
  assert.equal(writes.length, 1);
  assert.equal(writes[0].room_type, 'administrative');
  assert.equal(writes[0].hardware.length, 0);
});

test('room type participates in change detection and restores with undo history', async () => {
  const { instance } = form();
  const before = instance.buildAudienceSnapshot();
  instance.roomType = 'administrative';
  const after = instance.buildAudienceSnapshot();
  assert.notEqual(before, after);
  instance.applyAudienceSnapshot(before);
  await Promise.resolve();
  assert.equal(instance.roomType, 'educational');
  instance.applyAudienceSnapshot(after);
  await Promise.resolve();
  assert.equal(instance.roomType, 'administrative');
});
