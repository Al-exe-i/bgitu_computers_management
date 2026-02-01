import { defineStore } from 'pinia';
import api from '@/services/api';
import router from "@/router/index.js";

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: null,
        isAuthenticated: false,
        isInitialized: false,
        isLoggingOut: false
    }),

    actions: {
        // LOGIN
        async login(email, password)
        {
            try
            {
                const formData = new URLSearchParams();
                formData.append('username', email);
                formData.append('password', password);

                await api.post('/token', formData, {
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                });

                this.isAuthenticated = true;
                await this.fetchUser();
                return true;
            }
            catch (error)
            {
                console.error('Login failed:', error.response?.data || error.message);
                throw error;
            }
        },

        // FETCH USER
        async fetchUser()
        {
            try
            {
                const response = await api.get('/users/me');
                this.user = response.data;
                this.isAuthenticated = true;

                this.user.photo = null;
                try
                {
                    const photoRes = await api.get('/users/me/photo', { responseType: 'blob' });
                    this.user.photo = URL.createObjectURL(photoRes.data);
                }
                catch (e) { /* ignore 404 */ }

            }
            catch (error)
            {
                this.user = null;
                this.isAuthenticated = false;
                // Не кидаем ошибку, чтобы не ломать приложение при старте
                //console.warn('User session not active');
            }
            finally
            {
                this.isInitialized = true;
            }
        },

        // REFRESH
        async refreshToken()
        {
            await api.post('/users/refresh');
        },

        // LOGOUT
        async logout()
        {
            this.isLoggingOut = true;
            try
            {
                await api.post('/logout'); // Сообщаем серверу убрать куки
            }
            catch (error)
            {
                console.error('Server logout error', error);
            }
            finally
            {
                // Чистим клиентское состояние в любом случае
                if (this.user?.photo) URL.revokeObjectURL(this.user.photo);
                this.user = null;
                this.isAuthenticated = false;
                // Очистка URL фото из памяти, если было

                const currentRoute = router.currentRoute.value;

                if (currentRoute.meta.requiresAuth)
                {
                    await router.push('/');
                }
                this.isLoggingOut = false;
            }
        }
    }
});
