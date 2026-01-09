import { defineStore } from 'pinia';
import api from '@/services/api';

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: null,
        // isAuthenticated — это просто флаг.
        // Изначально false, пока мы не проверим пользователя.
        isAuthenticated: false,
    }),

    actions: {
        // LOGIN
        async login(email, password) {
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
                console.warn('User session not active');
            }
        },

        // REFRESH
        async refreshToken()
        {
            await api.post('/users/refresh');
        },

        // LOGOUT
        async logout() {
            try
            {
                // Сначала говорим серверу удалить куки
                await api.post('/logout');
            }
            catch (error)
            {
                console.error('Logout API error', error);
            }
            finally
            {
                // Чистим клиентское состояние в любом случае
                this.user = null;
                this.isAuthenticated = false;

                // Очистка URL фото из памяти, если было
                if (this.user?.photo) URL.revokeObjectURL(this.user.photo);
            }
        }
    }
});
