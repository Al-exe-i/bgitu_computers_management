// API
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// WebSocket
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || '/ws';

export const getApiUrl = () =>
{
    return API_BASE_URL;
};

export const getWsUrl = () => {
    return WS_BASE_URL
};