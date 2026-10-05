import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';

function deferred() {
    let resolve, reject;
    const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
    return { promise, resolve, reject };
}

function loadStore({ refresh, get = async () => ({ data: { id: 7 } }), post = async () => {} }) {
    const source = readFileSync(new URL('../src/stores/auth.js', import.meta.url), 'utf8')
        .replace(/^import .*;\r?\n/gm, '')
        .replace('export const useAuthStore =', 'globalThis.storeDefinition =');
    const context = vm.createContext({
        defineStore: (_name, definition) => definition,
        createSessionCoordinator: () => ({ refresh, mutate: operation => operation() }),
        axios: { create: () => ({ post }) },
        api: { get }, console,
        router: { currentRoute: { value: { meta: {} } } },
        URL: { revokeObjectURL() {}, createObjectURL: () => 'blob:test' },
    });
    vm.runInContext(source.replace('import.meta.env.VITE_API_BASE_URL', "'/api/v1'"), context);
    const definition = context.storeDefinition;
    const store = { ...definition.state(), ...definition.actions };
    store.user = { id: 7 };
    store.isAuthenticated = true;
    return store;
}

test('late refresh cannot restore a logged-out profile', async () => {
    const request = deferred();
    const store = loadStore({ refresh: () => request.promise });
    const pending = store.refreshToken();
    await store.logout();
    request.resolve({ id: 7 });
    await assert.rejects(pending, { code: 'AUTH_SESSION_CHANGED' });
    assert.equal(store.user, null);
    assert.equal(store.isAuthenticated, false);
});

test('late refresh rejection cannot clear a newer login', async () => {
    const request = deferred();
    const store = loadStore({ refresh: () => request.promise });
    const pending = store.refreshToken();
    store.sessionRevision++;
    store.user = { id: 8 };
    request.reject({ response: { status: 401 } });
    await assert.rejects(pending, { code: 'AUTH_SESSION_CHANGED' });
    assert.equal(store.user.id, 8);
    assert.equal(store.isAuthenticated, true);
});

test('current denial clears local state without a server logout', async () => {
    let logouts = 0;
    const store = loadStore({
        refresh: async () => { throw { response: { status: 401 } }; },
        post: async () => { logouts++; },
    });
    await assert.rejects(store.refreshToken());
    assert.equal(store.user, null);
    assert.equal(logouts, 0);
});

test('late profile response cannot restore a logged-out profile', async () => {
    const request = deferred();
    const store = loadStore({ get: () => request.promise });
    const pending = store.fetchUser();
    await store.logout();
    request.resolve({ data: { id: 7 } });
    await pending;
    assert.equal(store.user, null);
    assert.equal(store.isAuthenticated, false);
});

function loadApp() {
    const source = readFileSync(new URL('../src/App.vue', import.meta.url), 'utf8')
        .split('<script>')[1].split('</script>')[0]
        .replace(/^import .*;\r?\n/gm, '')
        .replace('export default', 'globalThis.component =');
    const sources = [];
    const timers = new Map();
    class FakeEventSource {
        constructor() { this.listeners = {}; sources.push(this); }
        addEventListener(name, listener) { this.listeners[name] = listener; }
        close() { this.closed = true; }
    }
    const context = vm.createContext({
        AppHeader: {}, LoginModal: {}, NotificationsModal: {}, AppFooter: {}, ConfirmationModal: {},
        EventSource: FakeEventSource,
        getNotificationSseUrl: () => '/events/notifications',
        getRealtimeClientId: () => 'test-client', withSseParams: url => url,
        window: {
            setTimeout(callback) { const id = timers.size + 1; timers.set(id, callback); return id; },
            clearTimeout(id) { timers.delete(id); },
        }, console,
    });
    vm.runInContext(source, context);
    const component = context.component;
    const app = { ...component.data(), ...component.methods };
    app.authStore = { isAuthenticated: true, refreshToken: async () => {} };
    return { app, sources, timers };
}

test('SSE expiry closes old source, refreshes and opens only one replacement', async () => {
    const { app, sources } = loadApp();
    const refresh = deferred();
    app.authStore.refreshToken = () => refresh.promise;
    app.openNotificationStream();
    const pending = app.recoverNotificationStream();
    assert.equal(sources[0].closed, true);
    sources[0].listeners.error(); // Queued error from the old source must be ignored.
    await app.recoverNotificationStream();
    refresh.resolve();
    await pending;
    assert.equal(sources.length, 2);
    assert.equal(app.notificationReconnectTimer, null);
});

test('SSE recovery does not reopen after pagehide or confirmed logout', async () => {
    for (const logout of [false, true]) {
        const { app, sources } = loadApp();
        const refresh = deferred();
        app.authStore.refreshToken = () => refresh.promise;
        app.openNotificationStream();
        const pending = app.recoverNotificationStream();
        if (logout) app.authStore.isAuthenticated = false;
        else app.handlePageLifecycleEnd();
        refresh.resolve();
        await pending;
        assert.equal(sources.length, 1);
    }
});

test('SSE recovery uses backoff on network failure without logout', async () => {
    const { app, sources, timers } = loadApp();
    app.authStore.refreshToken = async () => { throw new Error('Network unavailable'); };
    app.openNotificationStream();
    await app.recoverNotificationStream();
    assert.equal(app.authStore.isAuthenticated, true);
    assert.equal(sources.length, 1);
    assert.equal(timers.size, 1);
    assert.equal(app.notificationReconnectAttempts, 1);
});
