// src/router/index.js

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {useNotificationsStore} from "@/stores/notifications.js";

const HomeView = () => import("@/views/HomeView.vue");
const OfficeView = () => import("@/views/OfficeView.vue");
const AudienceView = () => import("@/views/AudienceView.vue");
const NotFoundView = () => import("@/views/NotFoundView.vue");
const InviteRegistrationView = () => import("@/views/InviteRegistrationView.vue");
const CreateAudience = () => import("@/components/Layout/CreateAudience.vue");
const SettingsLayout = () => import("@/components/Layout/Settings/SettingsLayout.vue");
const UserProfile = () => import("@/components/Layout/Settings/UserProfile.vue");
const SecuritySettings = () => import("@/components/Layout/Settings/SecuritySettings.vue");
const SystemLayout = () => import("@/components/Layout/Settings/System/SystemLayout.vue");
const ManageUsers = () => import("@/components/Layout/Settings/System/ManageUsers.vue");
const ManageOffices = () => import("@/components/Layout/Settings/System/ManageOffices.vue");
const ManageAudiences = () => import("@/components/Layout/Settings/System/ManageAudiences.vue");
const ManageInvites = () => import("@/components/Layout/Settings/System/ManageInvites.vue");
const ManageHardwareAnalytics = () => import("@/components/Layout/Settings/System/ManageHardwareAnalytics.vue");
const ManageAuditLogs = () => import("@/components/Layout/Settings/System/ManageAuditLogs.vue");

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
        path: `/audience/:audienceId/edit`,
        redirect: to => ({ name: 'ChangeAudience', params: { audienceId: to.params.audienceId } }),
    },

    {
        path: `/audience/:audienceId`,
        redirect: to => ({ name: 'Audience', params: { audienceId: to.params.audienceId } }),
    },

    {
        path: `/audiences/:audienceId/edit`,
        name: 'ChangeAudience',
        component: CreateAudience,
        props: route => ({ id: route.params.audienceId }),
        meta: {requiresAuth: true, title: 'Редактирование аудитории'},
    },

    {
        path: `/audiences/:audienceId`,
        name: 'Audience',
        component: AudienceView,
        props: true,
        meta: {title: 'Аудитория'},
    },

    {
        path: '/new-audience',
        name: 'New Audience',
        component: CreateAudience,
        meta: {requiresAuth: true, title: (route) => `Создание аудитории`}
    },

    {
        path: '/register',
        name: 'InviteRegister',
        component: InviteRegistrationView,
        meta: { title: 'Регистрация' }
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
                redirect: { name: 'SettingsSecurity' } // По умолчанию открываем настройки безопасности
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
                        path: 'invites',
                        name: 'SystemInvites',
                        component: ManageInvites,
                        meta: { title: 'Пригласительные ссылки' }
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
