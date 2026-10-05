import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { test } from 'node:test';
import { parse, compileStyle } from '@vue/compiler-sfc';

const audience = readFileSync(new URL('../src/views/AudienceView.vue', import.meta.url), 'utf8');
const { descriptor } = parse(audience);
const css = descriptor.styles.map(style => compileStyle({ source: style.content, filename: 'AudienceView.vue',
  id: 'data-v-test', scoped: style.scoped }).code).join('\n');

test('dark modal overrides retain their target after Vue scoped CSS compilation', () => {
  for (const selector of [
    '.audience-drop-classroom-overlay .action-btn.cancel-btn',
    '.audience-drop-classroom-overlay .action-btn.delete-btn',
    '.equipment-modal-content .problem-input',
  ]) {
    assert.ok(css.includes(`html[data-theme='dark'] ${selector}[data-v-test]`), selector);
  }
});

test('specification close control is circular and templates reset between editing sessions', () => {
  assert.match(audience, /<ModalCloseButton @click="closeSpecsModal"/);
  assert.match(audience, /cancelSpecsEdit\(\)\s*\{\s*this.specTemplatesExpanded = false/);
  assert.match(audience, /@click="specsEdit = true; specTemplatesExpanded = false"/);
  assert.match(audience, /specTemplatesExpanded: false/);
});

test('global dark header rules do not decorate equipment headings', () => {
  const app = readFileSync(new URL('../src/App.vue', import.meta.url), 'utf8');
  assert.match(app, /html\[data-theme='dark'\] #app > header,/);
  assert.doesNotMatch(app, /html\[data-theme='dark'\] header,/);
  assert.match(app, /<Teleport to="body"><NotificationsModal/);
});

test('legacy close button dimensions do not override the shared round control', () => {
  const block = audience.match(/\.modal-close-upper\s*\{[\s\S]*?(?=\n\.modal-content \{)/)?.[0];
  assert.ok(block);
  assert.match(block, /button:not\(\.modal-round-close\)\s*\{/);
  assert.doesNotMatch(block, /\n\s*button\s*\{/);
});

test('component theme selectors never collapse into styling the document root', () => {
  function check(directory) {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const url = new URL(entry.name + (entry.isDirectory() ? '/' : ''), directory);
      if (entry.isDirectory()) { check(url); continue; }
      if (!entry.name.endsWith('.vue')) continue;
      const { descriptor } = parse(readFileSync(url, 'utf8'));
      for (const style of descriptor.styles) {
        if (!style.scoped) continue;
        const result = compileStyle({ source: style.content, filename: url.pathname, id: 'data-v-test', scoped: true });
        assert.equal(result.errors.length, 0, url.pathname);
        assert.doesNotMatch(result.code, /(?:^|\n)\s*html\[data-theme=['"]dark['"]\]\s*\{/, url.pathname);
      }
    }
  }
  check(new URL('../src/', import.meta.url));
});
