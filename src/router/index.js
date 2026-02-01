// src/router/index.js

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import OfficeView from "@/views/OfficeView.vue";
import AudienceView from "@/views/AudienceView.vue";
import HomeView from "@/views/HomeView.vue";
import NotFoundView from "@/views/NotFoundView.vue";
import CreateAudience from "@/components/Layout/CreateAudience.vue";
import {useNotificationsStore} from "@/stores/notifications.js";
import SettingsLayout from "@/components/Layout/Settings/SettingsLayout.vue";
import UserProfile from "@/components/Layout/Settings/UserProfile.vue";
import SecuritySettings from "@/components/Layout/Settings/SecuritySettings.vue";

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
        path: `/audience/:id/edit`,
        name: 'ChangeAudience',
        component: CreateAudience,
        props: true,
        meta: {requiresAuth: true, title: (route) => `Редактирование аудитории №${route.params.audienceId}`},
    },

    {
        path: `/audience/:audienceId`,
        name: 'Audience',
        component: AudienceView,
        props: true,
        meta: {title: (route) => `Аудитория №${route.params.audienceId}`},
    },

    {
        path: '/new-audience',
        name: 'New Audience',
        component: CreateAudience,
        meta: {requiresAuth: true, title: (route) => `Создание аудитории`}
    },

    {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: NotFoundView
    },

    {
        path: '/settings',
        component: SettingsLayout,
        meta: { requiresAuth: true },
        children: [
            {
                path: '',
                redirect: { name: 'SettingsProfile' } // По умолчанию открываем профиль
            },
            {
                path: 'profile',
                name: 'SettingsProfile',
                component: UserProfile,
                meta: { title: 'Профиль пользователя' }
            },
            {
                path: 'security',
                name: 'SettingsSecurity',
                component: SecuritySettings, // Создадим простую заглушку
                meta: { title: 'Безопасность' }
            }
        ]
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach(async (to, from) => {
    const auth = useAuthStore()
    const notify = useNotificationsStore()

    if (!auth.isInitialized)
    {
        await auth.fetchUser()
    }

    if(to.meta.requiresAuth && !auth.isAuthenticated)
    {
        notify.warning("Вам необходимо авторизоваться")
        return `/`
    }
    const title = typeof to.meta.title === 'function'
        ? to.meta?.title(to)
        : to.meta?.title
    const defaultTitle = 'BGITU Computers management';
    document.title = title || defaultTitle
})

export default router