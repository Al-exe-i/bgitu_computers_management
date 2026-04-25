import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    withCredentials: true,
});

// глобальный lock на refresh
let refreshPromise = null;

const SKIP_REFRESH_URLS = ['/token', '/refresh', '/logout', '/logout_all'];

const shouldSkipRefresh = (url = '') =>
    SKIP_REFRESH_URLS.some((item) => url.includes(item));

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        const status = error.response?.status;
        if (status !== 401) return Promise.reject(error);

        if (shouldSkipRefresh(originalRequest?.url)) {
            return Promise.reject(error);
        }

        // защита от бесконечного retry одного и того же запроса
        if (originalRequest._retry) {
            return Promise.reject(error);
        }
        originalRequest._retry = true;

        const authStore = useAuthStore();

        try {
            // если refresh уже идёт — ждём его
            if (!refreshPromise) {
                refreshPromise = authStore.refreshToken()
                    .finally(() => { refreshPromise = null; });
            }

            await refreshPromise;

            // повторяем исходный запрос
            return api(originalRequest);
        } catch (refreshError) {
            await authStore.logout();
            return Promise.reject(refreshError);
        }
    }
);

export default api;
