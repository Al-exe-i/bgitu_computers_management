// src/stores/auth.js

import {defineStore} from 'pinia'
import api from '@/services/api'
import {useNotificationsStore} from "@/stores/notifications.js";

export const useAuthStore = defineStore('auth', {
    state: () => ({
        accessToken: localStorage.getItem('accessToken') || null,
        user: null,
        loading: false,
        error: null
    }),

    getters: {
        isAuthenticated: (state) => !!state.accessToken,
        isTokenExpired: (state) => {
            if (!state.accessToken) return true
            try
            {
                const payload = JSON.parse(atob(state.accessToken.split('.')[1]))
                return payload.exp * 1000 < Date.now()
            }
            catch
            {
                return true
            }
        }
    },

    actions: {
        async login(email, password)
        {
            this.loading = true
            this.error = null
            try
            {
                const response = await api.post('/token', new URLSearchParams({
                    username: email,
                    password: password
                }), {
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
                })
                this.setAccessToken(response.data.access_token)
                await this.fetchUser()
                return true
            }
            catch (err)
            {
                this.error = err.response?.data?.detail || 'Проверьте интернет-соединение'
                this.clearAccessTokenAndFreeUser()
                throw err
            }
            finally
            {
                this.loading = false
            }
        },

        async fetchUser()
        {
            try
            {
                const userResponse = await api.get(`/users/me`);
                this.user = userResponse.data;
                this.user.photo = null;

                try
                {
                    const userPhotoResponse = await api.get(`/users/me/photo`, { responseType: 'blob' });
                    this.user.photo = URL.createObjectURL(userPhotoResponse.data);
                }
                catch (photoError)
                {
                    if (photoError.response && photoError.response.status !== 404)
                    {
                        console.error('Failed to fetch user photo', photoError);
                    }
                }
            }
            catch (err)
            {
                console.error('Failed to fetch main user data', err);
            }
        },

        async refreshToken()
        {
            if (!this.refreshToken)
            {
                this.clearAccessTokenAndFreeUser()
                return false
            }

            try
            {
                const response = await api.post('/users/refresh', {}, {
                    headers: { Authorization: `Bearer ${this.refreshToken}` }
                })

                this.setAccessToken(response.data.access_token)
                return true
            }
            catch (err)
            {
                this.clearAccessTokenAndFreeUser()
                return false
            }
        },

        setAccessToken(access)
        {
            this.accessToken = access
            localStorage.setItem('accessToken', access)
            api.defaults.headers.common['Authorization'] = `Bearer ${access}`
        },

        clearAccessTokenAndFreeUser()
        {
            this.accessToken = null
            if (this.user && this.user.photo)
            {
                URL.revokeObjectURL(this.user.photo)
            }
            this.user = null
            localStorage.removeItem('accessToken')
            delete api.defaults.headers.common['Authorization']
        },

        async logout()
        {
            const notify = useNotificationsStore()
            try
            {
                await api.post('/logout')
                notify.info("Вы вышли из аккаунта", 2700)
            }
            catch (e)
            {
                notify.error("Не удалось выйти. Попробуйте снова")
            }
            finally
            {
                this.clearAccessTokenAndFreeUser()
            }
        },

        async initialize()
        {
            const token = localStorage.getItem('accessToken')
            if (token)
            {
                this.accessToken = token
                api.defaults.headers.common['Authorization'] = `Bearer ${token}`
                await this.fetchUser()
            }
        },
    }
})