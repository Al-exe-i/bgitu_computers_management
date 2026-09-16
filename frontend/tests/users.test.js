import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { isRuEmail, isValidEmail, mapUserApiError, RU_EMAIL_ERROR_MESSAGE, getUserRoleLabel } from '../src/utils/users.js';

test('manual user creation keeps email validation after invitation removal', () => {
  assert.equal(isValidEmail('teacher@example.ru'), true);
  assert.equal(isRuEmail(' teacher@BGITU.RU '), true);
  for (const email of ['teacher@example.com', 'teacher@ru', 'teacher@example.ru.invalid', 'bad email@example.ru', '']) {
    assert.equal(isRuEmail(email), false);
  }
});

test('manual creation errors remain readable without exposing server payloads', () => {
  assert.equal(mapUserApiError({ response: { status: 422, data: { detail: [{ loc: ['body', 'email'], msg: 'Email must use a .ru domain' }] } } }), RU_EMAIL_ERROR_MESSAGE);
  assert.match(mapUserApiError({ response: { status: 422, data: { detail: [{ loc: ['body', 'password'], ctx: { min_length: 6 } }] } } }), /6/);
  assert.match(mapUserApiError({ response: { status: 409 } }), /уже существует/);
  assert.match(mapUserApiError({ response: { status: 403 } }), /Недостаточно прав/);
  assert.match(mapUserApiError({ code: 'ECONNABORTED' }), /слишком долго/);
  assert.match(mapUserApiError({ request: {} }), /подключение/);
  assert.equal(mapUserApiError({ response: { status: 500, data: { detail: 'private server error' } } }).includes('private'), false);
  assert.equal(getUserRoleLabel(1), 'Администратор');
  assert.equal(getUserRoleLabel('teacher'), 'Преподаватель');
});

test('registration by invitation is absent from routes and settings navigation', () => {
  const router = readFileSync(new URL('../src/router/index.js', import.meta.url), 'utf8');
  const navigation = readFileSync(new URL('../src/components/Layout/Settings/System/SystemLayout.vue', import.meta.url), 'utf8');
  assert.doesNotMatch(router, /InviteRegister|SystemInvites|ManageInvites|path: '\/register'/);
  assert.doesNotMatch(navigation, /SystemInvites/);
  assert.match(router, /component: ManageUsers/);
});
