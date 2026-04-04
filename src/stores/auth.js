import { defineStore } from 'pinia';
import api from '@/services/api';
import router from "@/router/index.js";
import axios from "axios";

const plain = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    withCredentials: true,
});

let fetchUserPromise = null;

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
            if (fetchUserPromise) {
                return fetchUserPromise;
            }

            fetchUserPromise = (async () => {
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
                catch (e) { }

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
                fetchUserPromise = null;
            }
            })();

            return fetchUserPromise;
        },

        // REFRESH
        async refreshToken()
        {
            await plain.post('/refresh');
        },

        // LOGOUT
        async logout(all = false)
        {
            this.isLoggingOut = true;
            try
            {
                if(all) {
                    await api.post('/logout_all');
                }
                else {
                    await api.post('/logout');
                }

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
