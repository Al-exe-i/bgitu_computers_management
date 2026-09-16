import assert from 'node:assert/strict';
import { test } from 'node:test';
import { audienceOriginQuery, preserveAudienceOrigin, officeBackLocation, officeView } from '../src/utils/officeNavigation.js';

test('audience returns to original floor and view even after a URL reload', () => {
  for (const view of ['plan', 'cards', 'compact']) {
    const query = Object.fromEntries(new URLSearchParams(audienceOriginQuery(view, 3)));
    const location = officeBackLocation({ office_id: 2, floor: 3 }, query);
    assert.deepEqual(location, { name: 'Office', params: { officeNumber: '2' }, query: { view, floor: '3' } });
    assert.deepEqual(preserveAudienceOrigin(query), query);
  }
});

test('direct audience links return to their building, not an unrelated history entry', () => {
  assert.deepEqual(officeBackLocation({ office_id: 1, floor: 0 }), {
    name: 'Office', params: { officeNumber: '1' }, query: { view: 'cards', floor: '0' },
  });
  assert.deepEqual(officeBackLocation(null), { name: 'Home' });
});

test('return query accepts only known modes and integer floors', () => {
  for (const view of ['https://example.com', ['plan'], '', null]) assert.equal(officeView(view), null);
  assert.deepEqual(preserveAudienceOrigin({ officeView: 'plan', officeFloor: ['2'], redirect: 'https://example.com' }), { officeView: 'plan' });
  assert.deepEqual(officeBackLocation({ office_id: 1, floor: 2 }, { officeView: 'bad', officeFloor: 'NaN' }).query,
    { view: 'cards', floor: '2' });
});
