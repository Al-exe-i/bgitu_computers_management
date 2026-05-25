// API
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// WebSocket
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || '/ws';

export const getApiUrl = () =>
{
    return API_BASE_URL;
};

export const getWsUrl = () => {
    const rawUrl = String(WS_BASE_URL || '/ws').trim();

    if (/^wss?:\/\//i.test(rawUrl)) {
        return rawUrl;
    }

    if (/^https?:\/\//i.test(rawUrl)) {
        return rawUrl.replace(/^http/i, 'ws');
    }

    if (typeof window === 'undefined') {
        return rawUrl;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const path = rawUrl.startsWith('/') ? rawUrl : `/${rawUrl}`;

    return `${protocol}//${window.location.host}${path}`;
};
