import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    withCredentials: true,
});

// глобальный lock на refresh
let refreshPromise = null;

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        const status = error.response?.status;
        if (status !== 401) return Promise.reject(error);

        // не пытаемся refresh логин
        if (originalRequest?.url?.includes('/token')) {
            return Promise.reject(error);
        }

        // если 401 на самом refresh — значит сессия умерла
        if (originalRequest?.url?.includes('/refresh')) {
            const authStore = useAuthStore();
            await authStore.logout();
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