// src/router/index.js

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import mainDashboard from "@/components/mainDashboard.vue";
import office from "@/components/office.vue";

const routes = [
    {
        path: '/',
        name: 'Home',
        component: mainDashboard,
        meta: {title: "BGITU Computers management"}
    },
    {
        path: '/Office/:officeNumber',
        name: 'Office',
        component: office,
        props: true,
        meta: {title: (route) => `${route.params.officeNumber} корпус`},
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
    const title = typeof to.meta.title === 'function'
        ? to.meta?.title(to)
        : to.meta?.title
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