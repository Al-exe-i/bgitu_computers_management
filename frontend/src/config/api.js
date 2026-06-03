// API
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// Server-Sent Events
export const SSE_BASE_URL = import.meta.env.VITE_SSE_BASE_URL || '/events';
export const NOTIFICATIONS_SSE_BASE_URL =
    import.meta.env.VITE_NOTIFICATIONS_SSE_BASE_URL || `${SSE_BASE_URL}/notifications`;

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
