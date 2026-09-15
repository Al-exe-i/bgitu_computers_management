import { defineStore } from 'pinia';
import api from '@/services/api';
import router from "@/router/index.js";
import axios from "axios";
import { createSessionCoordinator } from '@/services/sessionCoordinator';

const plain = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    withCredentials: true,
    timeout: 15000,
});

const sessionCoordinator = createSessionCoordinator({ client: plain });
let fetchUserPromise = null;

function sessionChangedError() {
    return Object.assign(new Error('Session changed while the request was pending.'), {
        code: 'AUTH_SESSION_CHANGED',
    });
}

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: null,
        isAuthenticated: false,
        isInitialized: false,
        isLoggingOut: false,
        sessionRevision: 0,
    }),

    actions: {
        // LOGIN
        async login(email, password)
        {
            const revision = ++this.sessionRevision;
            fetchUserPromise = null;
            try
            {
                const formData = new URLSearchParams();
                formData.append('username', email);
                formData.append('password', password);

                await sessionCoordinator.mutate(() => plain.post('/token', formData, {
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                }));

                if (revision !== this.sessionRevision) throw sessionChangedError();
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
            if (this.isLoggingOut) return;
            if (fetchUserPromise) {
                return fetchUserPromise;
            }

            const revision = this.sessionRevision;
            const pending = (async () => {
            try
            {
                const response = await api.get('/users/me');
                if (revision !== this.sessionRevision || this.isLoggingOut) return;
                if (this.user?.photo) {
                    URL.revokeObjectURL(this.user.photo);
                }
                this.user = response.data;
                this.isAuthenticated = true;

                this.user.photo = null;
                try
                {
                    const photoRes = await api.get('/users/me/photo', { responseType: 'blob' });
                    if (revision !== this.sessionRevision || this.user?.id !== response.data.id) return;
                    this.user.photo = URL.createObjectURL(photoRes.data);
                }
                catch (e) { }

            }
            catch (error)
            {
                if (revision !== this.sessionRevision || this.isLoggingOut) return;
                if (this.user?.photo) {
                    URL.revokeObjectURL(this.user.photo);
                }
                this.user = null;
                this.isAuthenticated = false;
                // Не кидаем ошибку, чтобы не ломать приложение при старте
                //console.warn('User session not active');
            }
            finally
            {
                this.isInitialized = true;
                if (fetchUserPromise === pending) fetchUserPromise = null;
            }
            })();

            fetchUserPromise = pending;
            return fetchUserPromise;
        },

        // REFRESH
        async refreshToken()
        {
            if (this.isLoggingOut) throw sessionChangedError();
            const revision = this.sessionRevision;
            let user;
            try {
                user = await sessionCoordinator.refresh();
            } catch (error) {
                if (revision !== this.sessionRevision || this.isLoggingOut) throw sessionChangedError();
                if (error.response?.status === 401) await this.clearSession();
                throw error;
            }
            if (revision !== this.sessionRevision || this.isLoggingOut) throw sessionChangedError();
            const sameUser = this.user?.id === user.id;
            const photo = sameUser ? this.user?.photo : null;
            if (!sameUser && this.user?.photo) URL.revokeObjectURL(this.user.photo);
            this.user = { ...user, photo };
            this.isAuthenticated = true;
        },

        async clearSession()
        {
            this.sessionRevision += 1;
            fetchUserPromise = null;
            if (this.user?.photo) URL.revokeObjectURL(this.user.photo);
            this.user = null;
            this.isAuthenticated = false;
            if (router.currentRoute.value.meta.requiresAuth) await router.push('/');
        },

        // LOGOUT
        async logout(all = false)
        {
            if (this.isLoggingOut) return;
            this.sessionRevision += 1;
            fetchUserPromise = null;
            this.isLoggingOut = true;
            try
            {
                if(all) {
                    await sessionCoordinator.mutate(() => plain.post('/logout_all'));
                }
                else {
                    await sessionCoordinator.mutate(() => plain.post('/logout'));
                }

            }
            catch (error)
            {
                console.error('Server logout error', error);
            }
            finally
            {
                await this.clearSession();
                this.isLoggingOut = false;
            }
        }
    }
});
