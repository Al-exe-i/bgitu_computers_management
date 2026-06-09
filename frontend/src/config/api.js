// API
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// Server-Sent Events
export const SSE_BASE_URL = import.meta.env.VITE_SSE_BASE_URL || '/events';
export const NOTIFICATIONS_SSE_BASE_URL =
    import.meta.env.VITE_NOTIFICATIONS_SSE_BASE_URL || `${SSE_BASE_URL}/notifications`;

const REALTIME_TAB_ID_STORAGE_KEY = 'bgitu-realtime-tab-id';
let realtimeTabIdFallback = null;

const makeRealtimeTabId = () => {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        return crypto.randomUUID();
    }

    return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
};

export const getRealtimeClientId = (scope = 'default') => {
    if (typeof window === 'undefined') {
        return `${scope}:server`;
    }

    let tabId = realtimeTabIdFallback;

    try {
        tabId = window.sessionStorage.getItem(REALTIME_TAB_ID_STORAGE_KEY);
    } catch {
        tabId = realtimeTabIdFallback;
    }

    if (!tabId) {
        tabId = makeRealtimeTabId();
        realtimeTabIdFallback = tabId;

        try {
            window.sessionStorage.setItem(REALTIME_TAB_ID_STORAGE_KEY, tabId);
        } catch {
            // In restricted browser modes the in-memory fallback is enough for the current page lifetime.
        }
    }

    return `${scope}:${tabId}`;
};

export const getApiUrl = () =>
{
    return API_BASE_URL;
};

export const getSseUrl = () => {
    const rawUrl = String(SSE_BASE_URL || '/events').trim();

    if (/^https?:\/\//i.test(rawUrl)) {
        return rawUrl;
    }

    if (typeof window === 'undefined') {
        return rawUrl;
    }

    const path = rawUrl.startsWith('/') ? rawUrl : `/${rawUrl}`;

    return `${window.location.origin}${path}`;
};

export const getNotificationSseUrl = () => {
    const rawUrl = String(NOTIFICATIONS_SSE_BASE_URL || '/events/notifications').trim();

    if (/^https?:\/\//i.test(rawUrl)) {
        return rawUrl;
    }

    if (typeof window === 'undefined') {
        return rawUrl;
    }

    const path = rawUrl.startsWith('/') ? rawUrl : `/${rawUrl}`;

    return `${window.location.origin}${path}`;
};

export const withSseParams = (baseUrl, params = {}) => {
    const url = new URL(baseUrl, typeof window === 'undefined' ? 'http://localhost' : window.location.origin);

    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
            url.searchParams.set(key, String(value));
        }
    });

    return url.toString();
};
