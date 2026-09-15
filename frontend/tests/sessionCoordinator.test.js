import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createSessionCoordinator } from '../src/services/sessionCoordinator.js';

const unauthorized = () => Object.assign(new Error('Unauthorized'), { response: { status: 401 } });

function sharedLocks() {
    let tail = Promise.resolve();
    return {
        request(name, options, operation) {
            const next = tail.then(operation);
            tail = next.catch(() => {});
            return next;
        },
    };
}

test('multiple tabs and concurrent callers rotate the shared token only once', async () => {
    const locks = sharedLocks();
    let valid = false;
    let rotations = 0;
    const client = {
        async get() {
            if (!valid) throw unauthorized();
            return { data: { id: 7 } };
        },
        async post(url) {
            assert.equal(url, '/refresh');
            rotations++;
            await new Promise(resolve => setTimeout(resolve, 5));
            valid = true;
        },
    };
    const tabs = Array.from({ length: 5 }, () => createSessionCoordinator({ client, getLocks: () => locks }));
    const first = tabs[0].refresh();
    assert.equal(tabs[0].refresh(), first);
    const users = await Promise.all([first, ...tabs.map(tab => tab.refresh())]);
    assert.equal(rotations, 1);
    assert.ok(users.every(user => user.id === 7));
    await tabs[1].refresh(); // A late 401 must not rotate again.
    assert.equal(rotations, 1);
});

test('a failed refresh releases the lock and single-flight state', async () => {
    const locks = sharedLocks();
    let valid = false;
    let fail = true;
    let attempts = 0;
    const client = {
        async get() {
            if (!valid) throw unauthorized();
            return { data: { id: 7 } };
        },
        async post() {
            attempts++;
            if (fail) throw unauthorized();
            valid = true;
        },
    };
    const tab = createSessionCoordinator({ client, getLocks: () => locks });
    await assert.rejects(tab.refresh(), { response: { status: 401 } });
    fail = false;
    assert.deepEqual(await tab.refresh(), { id: 7 });
    assert.equal(attempts, 2);
});

test('network failures do not trigger refresh or logout', async () => {
    const requests = [];
    const tab = createSessionCoordinator({
        getLocks: sharedLocks,
        client: {
            async get() { throw new Error('Network unavailable'); },
            async post(url) { requests.push(url); },
        },
    });
    await assert.rejects(tab.refresh(), /Network unavailable/);
    assert.deepEqual(requests, []);
});

test('logout uses the same cross-tab lock as refresh', async () => {
    const locks = sharedLocks();
    const operations = [];
    let valid = false;
    const client = {
        async get() {
            if (!valid) throw unauthorized();
            return { data: { id: 7 } };
        },
        async post(url) {
            operations.push(url);
            valid = url === '/refresh';
        },
    };
    const first = createSessionCoordinator({ client, getLocks: () => locks });
    const second = createSessionCoordinator({ client, getLocks: () => locks });
    await Promise.all([first.refresh(), second.mutate(() => client.post('/logout'))]);
    assert.deepEqual(operations, ['/refresh', '/logout']);
    assert.equal(valid, false);
});

test('missing Web Locks fails closed for refresh but permits manual login', async () => {
    let requests = 0;
    const tab = createSessionCoordinator({
        getLocks: () => undefined,
        client: { async post() { requests++; } },
    });
    await assert.rejects(tab.refresh(), { code: 'AUTH_COORDINATION_UNAVAILABLE' });
    assert.equal(requests, 0);
    await tab.mutate(async () => { requests++; });
    assert.equal(requests, 1);
});
