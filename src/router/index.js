// src/router/index.js

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import mainDashboard from "@/components/mainDashboard.vue";
import floor from "@/components/floor.vue";

const routes = [
    {
        path: '/',
        name: 'Home',
        component: mainDashboard,
        meta: {title: "BGITU Computers management"}
    },
    {
        path: '/floor',
        name: 'Floor',
        component: floor
    }
    // {
    //     path: '/login',
    //     name: 'Login',
    //     component: LoginView,
    //     meta: { requiresGuest: true }
    // },
    // {
    //     path: '/profile',
    //     name: 'Profile',
    //     component: ProfileView,
    //     meta: { requiresAuth: true }
    // }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach(async (to, from, next) => {
    const { title } = to.meta;
    const defaultTitle = 'BGITU Computers management';
    document.title = title || defaultTitle

    // const authStore = useAuthStore()
    //
    // if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    //     next('/login')
    // } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    //     next('/')
    // } else {
    //     next()
    // }
    next() //Вызов next() обязателен
})

export default router