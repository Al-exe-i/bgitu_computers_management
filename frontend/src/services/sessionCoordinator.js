const AUTH_LOCK = 'bgitu:auth-cookies';

export function createSessionCoordinator({ client, getLocks = () => globalThis.navigator?.locks }) {
    let refreshPromise = null;

    async function withLock(operation, { required = false } = {}) {
        const locks = getLocks();
        if (!locks?.request) {
            if (!required) return operation();
            const error = new Error('Session refresh requires HTTPS and a browser with Web Locks support.');
            error.code = 'AUTH_COORDINATION_UNAVAILABLE';
            throw error;
        }

        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 30000);
        try {
            return await locks.request(AUTH_LOCK, { signal: controller.signal }, async () => {
                clearTimeout(timer);
                return operation();
            });
        } finally {
            clearTimeout(timer);
        }
    }

    async function readUser() {
        const response = await client.get('/users/me', { headers: { 'Cache-Control': 'no-cache' } });
        return response.data;
    }

    function refresh() {
        if (!refreshPromise) {
            refreshPromise = withLock(async () => {
                try {
                    // Another tab may already have replaced the shared HttpOnly cookies.
                    return await readUser();
                } catch (error) {
                    if (error.response?.status !== 401) throw error;
                }
                await client.post('/refresh');
                return readUser();
            }, { required: true }).finally(() => { refreshPromise = null; });
        }
        return refreshPromise;
    }

    return { refresh, mutate: withLock };
}
