// src/router/index.js

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import OfficeView from "@/views/OfficeView.vue";
import AudienceView from "@/views/AudienceView.vue";
import HomeView from "@/views/HomeView.vue";
import NotFoundView from "@/views/NotFoundView.vue";

const routes = [
    {
        path: '/',
        name: 'Home',
        component: HomeView,
        meta: {title: "BGITU Computers management"}
    },
    {
        path: '/Office/:officeNumber',
        name: 'Office',
        component: OfficeView,
        props: true,
        meta: {title: (route) => `${route.params.officeNumber} корпус`},
    },
    {
        path: `/audience/:audienceId`,
        name: 'Audience',
        component: AudienceView,
        props: true,
        meta: {title: (route) => `Аудитория №${route.params.audienceId}`},
    },
    {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: NotFoundView
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