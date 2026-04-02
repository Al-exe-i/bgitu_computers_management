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
import SystemLayout from "@/components/Layout/Settings/System/SystemLayout.vue";
import ManageUsers from "@/components/Layout/Settings/System/ManageUsers.vue";
import ManageOffices from "@/components/Layout/Settings/System/ManageOffices.vue";
import ManageAudiences from "@/components/Layout/Settings/System/ManageAudiences.vue";
import ManageHardwareAnalytics from "@/components/Layout/Settings/System/ManageHardwareAnalytics.vue";
import ManageAuditLogs from "@/components/Layout/Settings/System/ManageAuditLogs.vue";

const adminGuard = async (to, from, next) => {
    const authStore = useAuthStore();
    if (!authStore.isInitialized) await authStore.fetchUser();
    if (authStore.user && authStore.user.role === 1) {
        next();
    } else {
        next('/settings');
    }
};

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
        meta: {requiresAuth: true, title: (route) => `Редактирование аудитории №${route.params.id}`},
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
                component: SecuritySettings,
                meta: { title: 'Безопасность' }
            },

            {
                path: 'system',
                component: SystemLayout, // Оболочка раздела
                beforeEnter: adminGuard, // Защита
                children: [
                    { path: '', redirect: { name: 'SystemOffices' } },
                    {
                        path: 'offices',
                        name: 'SystemOffices',
                        component: ManageOffices,
                        meta: { title: 'Управление корпусами' }
                    },

                    {
                        path: 'users',
                        name: 'SystemUsers',
                        component: ManageUsers,
                        meta: { title: 'Управление пользователями' }
                    },

                    {
                        path: 'audiences',
                        name: 'SystemAudiences',
                        component: ManageAudiences,
                        meta: { title: 'Управление аудиториями' }
                    },

                    {
                        path: 'hardware-analytics',
                        name: 'SystemHardwareAnalytics',
                        component: ManageHardwareAnalytics,
                        meta: { title: 'Аналитика оборудования' }
                    },

                    {
                        path: 'logs',
                        name: 'SystemLogs',
                        component: ManageAuditLogs,
                        meta: { title: 'Журнал действий' }
                    },
                ]
            },
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
