import assert from 'node:assert/strict';
import { test } from 'node:test';
import { audienceOriginQuery, preserveAudienceOrigin, officeBackLocation, officeView, audienceBackLabel } from '../src/utils/officeNavigation.js';

test('audience returns to original floor and view even after a URL reload', () => {
  for (const view of ['plan', 'cards', 'compact']) {
    const query = Object.fromEntries(new URLSearchParams(audienceOriginQuery(view, 3)));
    const location = officeBackLocation({ office_id: 2, floor: 3 }, query);
    assert.deepEqual(location, view === 'plan'
      ? { name: 'FloorPlan', params: { officeNumber: '2', floorNumber: '3' }, query: { q: '' } }
      : { name: 'Office', params: { officeNumber: '2' }, query: { view, floor: '3' } });
    assert.deepEqual(preserveAudienceOrigin(query), query);
  }
});

test('floor search survives audience viewing and editing without accepting arbitrary query fields', () => {
  const query = audienceOriginQuery('plan', 0, '22');
  assert.deepEqual(preserveAudienceOrigin({ ...query, redirect: 'https://example.com' }), query);
  assert.deepEqual(officeBackLocation({ office_id: 1, floor: 5 }, query), {
    name: 'FloorPlan', params: { officeNumber: '1', floorNumber: '0' }, query: { q: '22' },
  });
  assert.equal(audienceBackLabel(query), 'К схеме этажа');
  assert.equal(audienceBackLabel({}), 'К списку аудиторий');
  assert.ok(!('officeSearch' in audienceOriginQuery('cards', 2, '22')));
  assert.ok(!('officeSearch' in preserveAudienceOrigin({ officeView: 'plan', officeSearch: ['22'] })));
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
