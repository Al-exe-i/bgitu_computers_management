// src/services/api.js

import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import {getApiUrl} from "@/config/api.js";

const api = axios.create({
    baseURL: getApiUrl(),
    timeout: 10000,
    withCredentials: true
})

// Интерцептор запросов
api.interceptors.request.use(
    (config) => {
        const authStore = useAuthStore()
        if (authStore.accessToken) {
            config.headers.Authorization = `Bearer ${authStore.accessToken}`
        }
        return config
    },
    (error) => Promise.reject(error)
)

// Интерцептор ответов — автоматический рефреш при 401
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config
        const authStore = useAuthStore()

        if (error.response?.status === 401 && !originalRequest._retry)
        {
            originalRequest._retry = true

            if (await authStore.refreshToken())
            {
                originalRequest.headers.Authorization = `Bearer ${authStore.accessToken}`
                return api(originalRequest)
            }
            else
            {
                authStore.clearAccessTokenAndFreeUser()
            }
        }

        return Promise.reject(error)
    }
)

export default api