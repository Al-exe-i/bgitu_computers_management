import axios from 'axios';
import { useAuthStore } from '@/stores/auth';
import router from '@/router';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    withCredentials: true,
});

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (error.response && error.response.status === 401)
        {
            if (originalRequest.url.includes('/users/refresh') || originalRequest.url.includes('/token')) {
                const authStore = useAuthStore();
                await authStore.logout();
                return Promise.reject(error);
            }

            if (!originalRequest._retry)
            {
                originalRequest._retry = true;
                const authStore = useAuthStore();

                try
                {
                    await authStore.refreshToken();
                    return api(originalRequest);
                }
                catch (refreshError)
                {
                    await authStore.logout();
                    return Promise.reject(refreshError);
                }
            }
        }

        return Promise.reject(error);
    }
);

export default api;
