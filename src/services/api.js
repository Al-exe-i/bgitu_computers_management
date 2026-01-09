import axios from 'axios';
import { useAuthStore } from '@/stores/auth';
import router from '@/router';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    withCredentials: true,
});


// Response Interceptor (Обработка 401 и Refresh)
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // Если ошибка 401 и мы еще не пробовали обновить токен
        if (error.response && error.response.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            const authStore = useAuthStore();

            try {
                // Просто вызываем эндпоинт. Куки обновятся сами (Set-Cookie).
                await authStore.refreshToken();

                // Повторяем оригинальный запрос.
                // Браузер сам подставит новую access-куку.
                return api(originalRequest);
            } catch (refreshError) {
                // Если refresh не удался (например, токен протух окончательно)
                await authStore.logout();
                await router.push('/auth');
                return Promise.reject(refreshError);
            }
        }
        return Promise.reject(error);
    }
);

export default api;
