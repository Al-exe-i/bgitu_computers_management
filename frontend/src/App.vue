<script>

import AppHeader from "@/components/Layout/AppHeader.vue";
import LoginModal from "@/components/Layout/LoginModal.vue";
import NotificationsModal from "@/components/Layout/NotificationsModal.vue";
import AppFooter from "@/components/Layout/AppFooter.vue";
import {useAuthStore} from "@/stores/auth.js";
import {useNotificationsStore} from "@/stores/notifications.js";
import {getNotificationSseUrl, getRealtimeClientId, withSseParams} from "@/config/api.js";

export default {
  name: "AppView",
  components: {AppFooter, NotificationsModal, LoginModal, AppHeader},
  data()
  {
    return {
      isLoginModalOpen: false,
      notificationEventSource: null,
      notificationReconnectTimer: null,
      notificationReconnectAttempts: 0,
    }
  },
  computed: {
    authStore() {
      return useAuthStore();
    },

    notificationsStore() {
      return useNotificationsStore();
    }
  },
  methods: {
    handleLoginModalClose() {
      this.isLoginModalOpen = false;

      if (this.$route?.query?.login) {
        const nextQuery = { ...this.$route.query };
        delete nextQuery.login;
        this.$router.replace({ query: nextQuery });
      }
    },

    syncLoginModalWithRoute() {
      if (this.$route?.query?.login === '1') {
        this.isLoginModalOpen = true;
      }
    },

    syncNotificationStream() {
      if (this.authStore.isAuthenticated) {
        this.openNotificationStream();
        return;
      }

      this.closeNotificationStream();
    },

    openNotificationStream() {
      if (this.notificationEventSource || !this.authStore.isAuthenticated) {
        return;
      }

      const source = new EventSource(
        withSseParams(getNotificationSseUrl(), {
          client_id: getRealtimeClientId('notifications'),
        }),
        { withCredentials: true }
      );
      this.notificationEventSource = source;

      source.addEventListener('open', () => {
        this.notificationReconnectAttempts = 0;
      });

      source.addEventListener('notification', (event) => {
        try {
          const data = JSON.parse(event.data);
          const notification = data.notification || data;
          this.notificationsStore.realtime(notification);
        } catch (error) {
          console.warn('Realtime notification parse failed', error);
        }
      });

      source.addEventListener('error', () => {
        this.closeNotificationStream({ keepReconnectTimer: true });
        this.scheduleNotificationReconnect();
      });
    },

    scheduleNotificationReconnect() {
      if (!this.authStore.isAuthenticated || this.notificationReconnectTimer) {
        return;
      }

      const delay = Math.min(30000, 3000 * 2 ** this.notificationReconnectAttempts);
      this.notificationReconnectAttempts += 1;
      this.notificationReconnectTimer = window.setTimeout(() => {
        this.notificationReconnectTimer = null;
        this.openNotificationStream();
      }, delay);
    },

    closeNotificationStream({ keepReconnectTimer = false } = {}) {
      if (this.notificationEventSource) {
        this.notificationEventSource.close();
        this.notificationEventSource = null;
      }

      if (!keepReconnectTimer && this.notificationReconnectTimer) {
        window.clearTimeout(this.notificationReconnectTimer);
        this.notificationReconnectTimer = null;
      }
    },

    handlePageLifecycleEnd() {
      this.closeNotificationStream();
    }
  },
  watch: {
    '$route.query.login': {
      immediate: true,
      handler() {
        this.syncLoginModalWithRoute();
      }
    },

    'authStore.isAuthenticated': {
      immediate: true,
      handler() {
        this.syncNotificationStream();
      }
    }
  },
  mounted() {
    window.addEventListener('pagehide', this.handlePageLifecycleEnd);
  },
  beforeUnmount() {
    window.removeEventListener('pagehide', this.handlePageLifecycleEnd);
    this.closeNotificationStream();
  }
}
</script>

<template>
  <app-header @open-login="isLoginModalOpen = true"></app-header>
  <login-modal :is-open="isLoginModalOpen" @close="handleLoginModalClose"></login-modal>
  <router-view></router-view>
  <NotificationsModal></NotificationsModal>
  <app-footer></app-footer>
</template>

<style>
:root {
  --login-error: #ef4444;
  --bg-start: #f0f9ff;
  --bg-end: #e0f2fe;
  --text-primary: #0f172a;
  --text-secondary: #64748b;
  --surface: #ffffff;
  --surface-soft: #f8fafc;
  --surface-muted: rgba(255, 255, 255, 0.88);
  --border: #dbeafe;
  --border-strong: #cbd5e1;
  --input-bg: #ffffff;
  --input-border: #cbd5e1;
  --shadow-elev: 0 10px 30px rgba(15, 23, 42, 0.1);
}

html[data-theme='dark'] {
  --bg-start: #0b1220;
  --bg-end: #0f172a;
  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --surface: #111827;
  --surface-soft: #1e293b;
  --surface-muted: rgba(15, 23, 42, 0.82);
  --border: #334155;
  --border-strong: #475569;
  --input-bg: #0f172a;
  --input-border: #334155;
  --shadow-elev: 0 10px 30px rgba(2, 6, 23, 0.45);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

html,
body,
#app {
  min-height: 100%;
}

body {
  background: linear-gradient(135deg, var(--bg-start), var(--bg-end));
  color: var(--text-primary);
  min-height: 100vh;
  padding: 0;
  transition: background 0.25s ease, color 0.25s ease;
}

html[data-theme='dark'] a {
  color: #93c5fd;
}

html[data-theme='dark'] header,
html[data-theme='dark'] .site-footer,
html[data-theme='dark'] .settings-layout,
html[data-theme='dark'] .settings-subheader,
html[data-theme='dark'] .profile-card,
html[data-theme='dark'] .security-card,
html[data-theme='dark'] .card,
html[data-theme='dark'] .audit-card,
html[data-theme='dark'] .table-wrapper,
html[data-theme='dark'] .table-container,
html[data-theme='dark'] .modal-content,
html[data-theme='dark'] .modal-card,
html[data-theme='dark'] .building-info,
html[data-theme='dark'] .controls-panel,
html[data-theme='dark'] .office-stats,
html[data-theme='dark'] .floor-section,
html[data-theme='dark'] .row-container,
html[data-theme='dark'] .profile-dropdown-content,
html[data-theme='dark'] .office-dropdown,
html[data-theme='dark'] .office-mobile-dropdown,
html[data-theme='dark'] .login-container,
html[data-theme='dark'] .notification,
html[data-theme='dark'] .workspace-modal-content,
html[data-theme='dark'] .hardware-modal-content {
  background: var(--surface) !important;
  border-color: var(--border) !important;
  color: var(--text-primary) !important;
  box-shadow: var(--shadow-elev) !important;
}

html[data-theme='dark'] .stat-card,
html[data-theme='dark'] .empty-state,
html[data-theme='dark'] .session-item,
html[data-theme='dark'] .icon-tabs,
html[data-theme='dark'] .segmented-control,
html[data-theme='dark'] .office-switch,
html[data-theme='dark'] .office-mobile-trigger,
html[data-theme='dark'] .collapse-icon,
html[data-theme='dark'] .filters-container,
html[data-theme='dark'] .filters-section,
html[data-theme='dark'] .search-bar {
  background: var(--surface-soft) !important;
  border-color: var(--border) !important;
  color: var(--text-primary) !important;
}

html[data-theme='dark'] .office-stats {
  background: #1e293b !important;
  border: 1px solid #334155 !important;
}

html[data-theme='dark'] .dashboard-title,
html[data-theme='dark'] .page-title,
html[data-theme='dark'] .office-title,
html[data-theme='dark'] .building-title,
html[data-theme='dark'] .section-title,
html[data-theme='dark'] .profile-name,
html[data-theme='dark'] .profile-fullname,
html[data-theme='dark'] .notification-title,
html[data-theme='dark'] .session-device,
html[data-theme='dark'] .floor-title,
html[data-theme='dark'] .row-title,
html[data-theme='dark'] .classroom-number {
  color: var(--text-primary) !important;
}

html[data-theme='dark'] .building-description,
html[data-theme='dark'] .stat-label,
html[data-theme='dark'] .breakdowns-title,
html[data-theme='dark'] .notification-message,
html[data-theme='dark'] .menu-item,
html[data-theme='dark'] .session-details,
html[data-theme='dark'] .footer-text,
html[data-theme='dark'] .section-subtitle,
html[data-theme='dark'] .empty-state-title,
html[data-theme='dark'] .empty-state-text {
  color: var(--text-secondary) !important;
}

html[data-theme='dark'] input:not([type='range']),
html[data-theme='dark'] textarea,
html[data-theme='dark'] select,
html[data-theme='dark'] .form-input,
html[data-theme='dark'] .login-input,
html[data-theme='dark'] .search-box input {
  background-color: var(--input-bg) !important;
  color: var(--text-primary) !important;
  border-color: var(--input-border) !important;
}

html[data-theme='dark'] input::placeholder,
html[data-theme='dark'] textarea::placeholder {
  color: var(--text-secondary) !important;
}

html[data-theme='dark'] table,
html[data-theme='dark'] th,
html[data-theme='dark'] td {
  background: transparent !important;
  color: var(--text-primary) !important;
  border-color: var(--border) !important;
}

html[data-theme='dark'] .icon-tab.active,
html[data-theme='dark'] .segment-btn.active {
  background: var(--surface) !important;
  color: #93c5fd !important;
}

html[data-theme='dark'] .modal-content,
html[data-theme='dark'] .modal-card,
html[data-theme='dark'] .hw-confirm-box {
  background: #111827 !important;
  border: 1px solid #334155 !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .modal-header,
html[data-theme='dark'] .modal-footer,
html[data-theme='dark'] .modal-body {
  background: transparent !important;
  border-color: #334155 !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .modal-title,
html[data-theme='dark'] .modal-subtitle,
html[data-theme='dark'] .hw-confirm-title {
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .hw-confirm-text,
html[data-theme='dark'] .hw-confirm-checkbox,
html[data-theme='dark'] .meta-label,
html[data-theme='dark'] .meta-value {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .close-btn,
html[data-theme='dark'] .modal-close-upper button {
  background: #0f172a !important;
  border: 1px solid #334155 !important;
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .close-btn:hover,
html[data-theme='dark'] .modal-close-upper button:hover {
  background: #1e293b !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .system-users-modal-overlay .close-btn,
html[data-theme='dark'] .audit-log-modal-overlay .close-btn {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

html[data-theme='dark'] .system-users-modal-overlay .close-btn:hover,
html[data-theme='dark'] .audit-log-modal-overlay .close-btn:hover {
  background: rgba(30, 41, 59, 0.72) !important;
  border: none !important;
}

html[data-theme='dark'] .system-users-modal-content .modal-action-btn-cancel {
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.88)) !important;
  border: 1px solid #334155 !important;
  color: #cbd5e1 !important;
  box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.03),
      0 10px 22px rgba(2, 6, 23, 0.22) !important;
}

html[data-theme='dark'] .system-users-modal-content .modal-action-btn-cancel:hover:not(:disabled) {
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.94), rgba(51, 65, 85, 0.92)) !important;
  border-color: #475569 !important;
  color: #f8fafc !important;
}

html[data-theme='dark'] .system-users-modal-content .modal-action-btn-submit {
  background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
  border: 1px solid rgba(96, 165, 250, 0.28) !important;
  color: #ffffff !important;
  box-shadow:
      0 14px 28px rgba(29, 78, 216, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
}

html[data-theme='dark'] .system-users-modal-content .modal-action-btn-submit:hover:not(:disabled) {
  background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
  border-color: rgba(147, 197, 253, 0.34) !important;
}

html[data-theme='dark'] .system-users-modal-content .modal-action-btn-submit:disabled,
html[data-theme='dark'] .system-users-modal-content .modal-action-btn-cancel:disabled {
  box-shadow: none !important;
}

html[data-theme='dark'] .system-offices-modal-content .modal-action-btn-cancel {
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.88)) !important;
  border: 1px solid #334155 !important;
  color: #cbd5e1 !important;
  box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.03),
      0 10px 22px rgba(2, 6, 23, 0.22) !important;
}

html[data-theme='dark'] .system-offices-modal-content .modal-action-btn-cancel:hover:not(:disabled) {
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.94), rgba(51, 65, 85, 0.92)) !important;
  border-color: #475569 !important;
  color: #f8fafc !important;
}

html[data-theme='dark'] .system-offices-modal-content .modal-action-btn-submit {
  background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
  border: 1px solid rgba(96, 165, 250, 0.28) !important;
  color: #ffffff !important;
  box-shadow:
      0 14px 28px rgba(29, 78, 216, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
}

html[data-theme='dark'] .system-offices-modal-content .modal-action-btn-submit:hover:not(:disabled) {
  background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
  border-color: rgba(147, 197, 253, 0.34) !important;
}

html[data-theme='dark'] .system-offices-modal-content .modal-action-btn-submit:disabled,
html[data-theme='dark'] .system-offices-modal-content .modal-action-btn-cancel:disabled {
  box-shadow: none !important;
}

html[data-theme='dark'] .hw-btn-cancel {
  background: #1e293b !important;
  color: #cbd5e1 !important;
  border: 1px solid #475569 !important;
}

html[data-theme='dark'] .hw-btn-cancel:hover {
  background: #334155 !important;
}

html[data-theme='dark'] .status-confirm-sheet {
  background:
      radial-gradient(circle at top right, rgba(37, 99, 235, 0.18), transparent 32%),
      radial-gradient(circle at 12% 14%, rgba(148, 163, 184, 0.08), transparent 24%),
      linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(17, 24, 39, 0.98)) !important;
  border: 1px solid #334155 !important;
  box-shadow: 0 32px 70px rgba(2, 6, 23, 0.42) !important;
}

html[data-theme='dark'] .status-confirm-close {
  background: rgba(15, 23, 42, 0.82) !important;
  border-color: #334155 !important;
  color: #94a3b8 !important;
}

html[data-theme='dark'] .status-confirm-close:hover {
  background: #1e293b !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .status-confirm-kicker,
html[data-theme='dark'] .status-confirm-state-label {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .status-confirm-title,
html[data-theme='dark'] .status-confirm-equipment-name,
html[data-theme='dark'] .status-confirm-state strong {
  color: #f8fafc !important;
}

html[data-theme='dark'] .status-confirm-text,
html[data-theme='dark'] .status-confirm-note p,
html[data-theme='dark'] .status-confirm-equipment-meta span {
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .status-confirm-equipment,
html[data-theme='dark'] .status-confirm-state,
html[data-theme='dark'] .status-confirm-arrow,
html[data-theme='dark'] .status-confirm-note {
  border-color: #334155 !important;
}

html[data-theme='dark'] .status-confirm-equipment,
html[data-theme='dark'] .status-confirm-state.is-current {
  background: rgba(15, 23, 42, 0.7) !important;
}

html[data-theme='dark'] .status-confirm-equipment-meta span {
  background: rgba(30, 41, 59, 0.82) !important;
}

html[data-theme='dark'] .status-confirm-state.is-target.is-working {
  background: linear-gradient(135deg, rgba(6, 95, 70, 0.4), rgba(16, 185, 129, 0.18)) !important;
  border-color: rgba(52, 211, 153, 0.34) !important;
}

html[data-theme='dark'] .status-confirm-state.is-target.is-broken {
  background: linear-gradient(135deg, rgba(127, 29, 29, 0.38), rgba(239, 68, 68, 0.16)) !important;
  border-color: rgba(248, 113, 113, 0.28) !important;
}

html[data-theme='dark'] .status-confirm-arrow {
  background: rgba(30, 41, 59, 0.78) !important;
  color: #94a3b8 !important;
}

html[data-theme='dark'] .status-confirm-note.is-working {
  background: linear-gradient(135deg, rgba(6, 78, 59, 0.44), rgba(16, 185, 129, 0.12)) !important;
  border-color: rgba(52, 211, 153, 0.22) !important;
}

html[data-theme='dark'] .status-confirm-note.is-broken {
  background: linear-gradient(135deg, rgba(127, 29, 29, 0.42), rgba(239, 68, 68, 0.1)) !important;
  border-color: rgba(248, 113, 113, 0.2) !important;
}

html[data-theme='dark'] .status-confirm-note-icon {
  background: rgba(15, 23, 42, 0.62) !important;
}

html[data-theme='dark'] .status-confirm-session-toggle {
  background: rgba(15, 23, 42, 0.72) !important;
  border-color: #334155 !important;
}

html[data-theme='dark'] .status-confirm-session-switch {
  background: #475569 !important;
}

html[data-theme='dark'] .status-confirm-session-copy strong {
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .status-confirm-session-copy span {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .status-confirm-btn.is-cancel {
  background: #1e293b !important;
  color: #cbd5e1 !important;
  border: 1px solid #475569 !important;
}

html[data-theme='dark'] .status-confirm-btn.is-cancel:hover {
  background: #334155 !important;
}


html[data-theme='dark'] .profile-img {
  border-color: #475569 !important;
  box-shadow: 0 0 0 1px rgba(15, 23, 42, 0.9) !important;
}

html[data-theme='dark'] .profile-avatar-large {
  border-color: #475569 !important;
  box-shadow: 0 0 0 2px rgba(15, 23, 42, 0.85) !important;
}

html[data-theme='dark'] .profile-dropdown-content {
  border: 1px solid #334155 !important;
}

html[data-theme='dark'] .profile-card .profile-header {
  border-bottom-color: #334155 !important;
}

html[data-theme='dark'] .profile-card .avatar-wrapper {
  border-color: #334155 !important;
  background: #0f172a !important;
}

html[data-theme='dark'] .profile-card .user-email {
  color: #f8fafc !important;
}

html[data-theme='dark'] .office-switch .office-btn:not(.active) {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .office-switch-indicator {
  box-shadow:
      0 16px 30px rgba(30, 64, 175, 0.34),
      inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
}

html[data-theme='dark'] .office-btn:not(.active):hover,
html[data-theme='dark'] .icon-tab:hover:not(.active),
html[data-theme='dark'] .segment-btn:hover:not(.active),
html[data-theme='dark'] .menu-item:hover,
html[data-theme='dark'] .notification-close:hover {
  background: rgba(148, 163, 184, 0.15) !important;
}

html[data-theme='dark'] .profile-dropdown .menu-item:hover {
  background: transparent !important;
}

html[data-theme='dark'] .office-dropdown-item {
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .office-dropdown-item:hover {
  background: rgba(148, 163, 184, 0.16) !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .office-dropdown-item.active {
  background: rgba(37, 99, 235, 0.22) !important;
  color: #93c5fd !important;
}

html[data-theme='dark'] .office-mobile-trigger {
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.94), rgba(30, 41, 59, 0.96)) !important;
  box-shadow: 0 14px 28px rgba(2, 6, 23, 0.28) !important;
}

html[data-theme='dark'] .office-mobile-trigger.active {
  border-color: rgba(96, 165, 250, 0.55) !important;
  box-shadow: 0 18px 34px rgba(2, 6, 23, 0.34) !important;
}

html[data-theme='dark'] .office-mobile-icon,
html[data-theme='dark'] .office-mobile-option-mark {
  background: rgba(37, 99, 235, 0.16) !important;
  color: #93c5fd !important;
}

html[data-theme='dark'] .office-mobile-kicker,
html[data-theme='dark'] .office-mobile-option-subtitle {
  color: var(--text-secondary) !important;
}

html[data-theme='dark'] .office-mobile-value,
html[data-theme='dark'] .office-mobile-option-title {
  color: var(--text-primary) !important;
}

html[data-theme='dark'] .office-mobile-chevron,
html[data-theme='dark'] .office-mobile-option-check {
  color: #93c5fd !important;
}

html[data-theme='dark'] .office-mobile-option:hover {
  background: rgba(148, 163, 184, 0.14) !important;
}

html[data-theme='dark'] .office-mobile-option.active {
  background: rgba(37, 99, 235, 0.18) !important;
}

html[data-theme='dark'] .system-nav {
  border-color: var(--border) !important;
  background:
      radial-gradient(circle at top left, rgba(37, 99, 235, 0.18), transparent 36%),
      radial-gradient(circle at bottom right, rgba(14, 165, 233, 0.14), transparent 30%),
      linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(30, 41, 59, 0.98)) !important;
  box-shadow: 0 18px 38px rgba(2, 6, 23, 0.26) !important;
}

html[data-theme='dark'] .system-nav .nav-pill {
  background: transparent !important;
  border-color: transparent !important;
  color: var(--text-secondary) !important;
}

html[data-theme='dark'] .system-nav .nav-pill:hover:not(.is-active) {
  background: rgba(148, 163, 184, 0.12) !important;
  border-color: transparent !important;
  color: var(--text-primary) !important;
}

html[data-theme='dark'] .system-nav .nav-pill.is-active {
  background: transparent !important;
  border-color: transparent !important;
  color: #e2e8f0 !important;
  box-shadow: none !important;
}

html[data-theme='dark'] .settings-layout .glass-effect {
  background: rgba(15, 23, 42, 0.84) !important;
}

html[data-theme='dark'] .settings-layout .settings-tabs {
  border: 1px solid #334155 !important;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(17, 24, 39, 0.94)) !important;
  box-shadow:
      inset 0 1px 0 rgba(51, 65, 85, 0.34),
      0 12px 24px rgba(2, 6, 23, 0.22) !important;
}

html[data-theme='dark'] .settings-layout .settings-tab {
  background: transparent !important;
  color: #94a3b8 !important;
}

html[data-theme='dark'] .settings-layout .settings-tab:hover:not(.active) {
  background: rgba(51, 65, 85, 0.38) !important;
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .settings-layout .settings-tab.active {
  background: transparent !important;
  color: #bfdbfe !important;
  box-shadow: none !important;
}

html[data-theme='dark'] .settings-layout .settings-tab-indicator {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.98), rgba(17, 24, 39, 0.98)) !important;
  border: 1px solid #334155 !important;
  box-shadow:
      0 12px 24px rgba(2, 6, 23, 0.34),
      inset 0 1px 0 rgba(148, 163, 184, 0.08) !important;
}

html[data-theme='dark'] .nav-active-indicator {
  box-shadow:
      0 18px 34px rgba(30, 64, 175, 0.36),
      inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
}

html[data-theme='dark'] .system-content .card .user-email {
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .system-content .card .user-name,
html[data-theme='dark'] .system-content .card .text-muted {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .system-content .card .address-text {
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .system-content .card .card-header .btn-primary {
  background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
  color: #e2e8f0 !important;
  border: 1px solid #2563eb !important;
}

html[data-theme='dark'] .system-content .card .card-header .btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
  border-color: #3b82f6 !important;
}

html[data-theme='dark'] .invite-admin-page .invite-panel,
html[data-theme='dark'] .invite-admin-page .created-results {
  background:
      radial-gradient(circle at top right, rgba(37, 99, 235, 0.16), transparent 34%),
      linear-gradient(180deg, rgba(15, 23, 42, 0.94), rgba(17, 24, 39, 0.96)) !important;
  border: 1px solid #334155 !important;
  box-shadow: 0 18px 36px rgba(2, 6, 23, 0.2) !important;
}

html[data-theme='dark'] .invite-admin-page .created-result-card {
  background: rgba(15, 23, 42, 0.72) !important;
  border-color: #334155 !important;
}

html[data-theme='dark'] .error-shell {
  --error-card-border: #334155;
  --error-card-bg:
      radial-gradient(circle at top right, rgba(59, 130, 246, 0.14), transparent 28%),
      linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(17, 24, 39, 0.96));
  --error-card-shadow:
      0 28px 58px rgba(2, 6, 23, 0.42),
      inset 0 1px 0 rgba(255, 255, 255, 0.04);
  --error-orb-bg: radial-gradient(circle, rgba(59, 130, 246, 0.12), transparent 70%);
  --error-side-border: #334155;
  --error-side-bg: linear-gradient(180deg, rgba(11, 18, 32, 0.9), rgba(15, 23, 42, 0.82));
  --error-status-border: rgba(248, 113, 113, 0.2);
  --error-status-bg: rgba(127, 29, 29, 0.24);
  --error-status-text: #fecaca;
  --error-icon-glow: linear-gradient(135deg, rgba(244, 63, 94, 0.18), rgba(59, 130, 246, 0.14));
  --error-icon-border: rgba(248, 113, 113, 0.16);
  --error-icon-bg: linear-gradient(135deg, rgba(127, 29, 29, 0.34), rgba(30, 41, 59, 0.96));
  --error-icon-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.05),
      0 18px 34px rgba(2, 6, 23, 0.32);
  --error-icon-color: #fda4af;
  --error-kicker-color: #94a3b8;
  --error-details-border: #334155;
  --error-details-bg: rgba(15, 23, 42, 0.76);
  --error-details-label: #94a3b8;
  --error-details-text: #e2e8f0;
}

html[data-theme='dark'] .error-shell .error-title {
  color: #f8fafc !important;
}

html[data-theme='dark'] .error-shell .error-message {
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .not-found-view {
  --nf-surface:
      linear-gradient(180deg, rgba(15, 23, 42, 0.92), rgba(17, 24, 39, 0.96));
  --nf-surface-soft: rgba(15, 23, 42, 0.64);
  --nf-border: rgba(71, 85, 105, 0.56);
  --nf-border-strong: rgba(71, 85, 105, 0.8);
  --nf-shadow:
      0 28px 72px rgba(2, 6, 23, 0.36),
      inset 0 1px 0 rgba(255, 255, 255, 0.04);
  --nf-code-fill: linear-gradient(135deg, #f8fafc 0%, #93c5fd 52%, #38bdf8 100%);
  --nf-side-bg: rgba(15, 23, 42, 0.68);
  --nf-side-icon-bg: linear-gradient(135deg, rgba(37, 99, 235, 0.24), rgba(14, 165, 233, 0.18));
  --nf-side-icon-text: #93c5fd;
  --nf-tip-text: #cbd5e1;
  --nf-path-bg: rgba(2, 6, 23, 0.34);
  --nf-path-text: #e2e8f0;
  --nf-primary-shadow: 0 16px 36px rgba(29, 78, 216, 0.28);
}

html[data-theme='dark'] .not-found-view .not-found-grid {
  background-image:
      linear-gradient(rgba(71, 85, 105, 0.18) 1px, transparent 1px),
      linear-gradient(90deg, rgba(71, 85, 105, 0.18) 1px, transparent 1px);
}

html[data-theme='dark'] .not-found-view .nf-btn-secondary {
  background: rgba(15, 23, 42, 0.72) !important;
  color: #e2e8f0 !important;
  border-color: rgba(71, 85, 105, 0.8) !important;
}

html[data-theme='dark'] .not-found-view .nf-btn-secondary:hover {
  background: rgba(30, 41, 59, 0.92) !important;
}

html[data-theme='dark'] .security-card .actions-footer {
  border-top-color: #334155 !important;
}

html[data-theme='dark'] .security-settings-card {
  background: var(--security-card-bg) !important;
  border-color: var(--security-card-border) !important;
  box-shadow: var(--security-shadow) !important;
}

html[data-theme='dark'] .security-settings-card .security-tabs {
  background: var(--security-tab-bg) !important;
  border-color: var(--security-soft-border) !important;
}

html[data-theme='dark'] .security-settings-card .security-tab:hover:not(.active) {
  background: var(--security-tab-hover) !important;
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .security-settings-card .security-tab.active {
  background: var(--security-tab-active) !important;
  color: var(--security-tab-active-text) !important;
  box-shadow:
      0 14px 28px rgba(2, 6, 23, 0.28),
      inset 0 1px 0 rgba(148, 163, 184, 0.08) !important;
}

html[data-theme='dark'] .security-settings-card .alert-box.info {
  background: linear-gradient(135deg, rgba(3, 105, 161, 0.16), rgba(15, 23, 42, 0.82)) !important;
  border-color: rgba(56, 189, 248, 0.2) !important;
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .security-settings-card .alert-box.warning {
  background: linear-gradient(135deg, rgba(133, 77, 14, 0.22), rgba(15, 23, 42, 0.82)) !important;
  border-color: rgba(245, 158, 11, 0.24) !important;
  color: #fcd34d !important;
}

html[data-theme='dark'] .security-settings-card .sessions-stat-chip,
html[data-theme='dark'] .security-settings-card .session-item,
html[data-theme='dark'] .security-settings-card .sessions-empty-state {
  background: var(--security-session-bg) !important;
  border-color: var(--security-session-border) !important;
}

html[data-theme='dark'] .security-settings-card .session-item.is-current {
  background: var(--security-session-current-bg) !important;
  border-color: var(--security-session-current-border) !important;
}

html[data-theme='dark'] .security-settings-card .session-icon {
  background: var(--security-session-icon-bg) !important;
  color: var(--security-session-icon-color) !important;
}

html[data-theme='dark'] .security-settings-card .session-item.is-current .session-icon {
  background: var(--security-session-current-icon-bg) !important;
  color: var(--security-session-current-icon-color) !important;
}

html[data-theme='dark'] .security-settings-card .logout-link {
  background: var(--security-danger-soft-bg) !important;
  border-color: var(--security-danger-soft-border) !important;
  color: var(--security-danger-soft-text) !important;
}

html[data-theme='dark'] .security-settings-card .logout-link:hover:not(:disabled) {
  background: rgba(153, 27, 27, 0.34) !important;
  border-color: rgba(248, 113, 113, 0.3) !important;
  color: #fecdd3 !important;
}

html[data-theme='dark'] .security-settings-card .session-danger-btn {
  background: linear-gradient(135deg, rgba(127, 29, 29, 0.82), rgba(190, 24, 93, 0.82)) !important;
  border-color: rgba(244, 63, 94, 0.22) !important;
  color: #fff1f2 !important;
  box-shadow: 0 16px 30px rgba(127, 29, 29, 0.26) !important;
}

html[data-theme='dark'] .security-settings-card .session-danger-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(153, 27, 27, 0.92), rgba(225, 29, 72, 0.88)) !important;
  border-color: rgba(251, 113, 133, 0.28) !important;
}

html[data-theme='dark'] .security-settings-root .security-settings-card {
  background:
      radial-gradient(circle at top right, rgba(59, 130, 246, 0.12), transparent 30%),
      linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(17, 24, 39, 0.98)) !important;
  border: 1px solid #334155 !important;
  box-shadow:
      0 28px 64px rgba(2, 6, 23, 0.34),
      inset 0 1px 0 rgba(255, 255, 255, 0.04) !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .security-settings-root .section-title,
html[data-theme='dark'] .security-settings-root .session-device,
html[data-theme='dark'] .security-settings-root .sessions-empty-state strong {
  color: #f8fafc !important;
}

html[data-theme='dark'] .security-settings-root .section-subtitle,
html[data-theme='dark'] .security-settings-root .form-group label,
html[data-theme='dark'] .security-settings-root .password-strength-title,
html[data-theme='dark'] .security-settings-root .password-strength-label,
html[data-theme='dark'] .security-settings-root .session-details,
html[data-theme='dark'] .security-settings-root .sessions-stat-chip,
html[data-theme='dark'] .security-settings-root .sessions-empty-state,
html[data-theme='dark'] .security-settings-root .loading-state,
html[data-theme='dark'] .security-settings-root .security-tab {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .security-settings-root .security-tabs {
  background: rgba(15, 23, 42, 0.92) !important;
  border: 1px solid #334155 !important;
}

html[data-theme='dark'] .security-settings-root .security-tab:hover:not(.active) {
  background: rgba(51, 65, 85, 0.74) !important;
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .security-settings-root .security-tab.active {
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.98), rgba(17, 24, 39, 0.98)) !important;
  color: #bfdbfe !important;
  box-shadow:
      0 14px 28px rgba(2, 6, 23, 0.28),
      inset 0 1px 0 rgba(148, 163, 184, 0.08) !important;
}

html[data-theme='dark'] .security-settings-root .alert-box.info {
  background: linear-gradient(135deg, rgba(3, 105, 161, 0.16), rgba(15, 23, 42, 0.82)) !important;
  border-color: rgba(56, 189, 248, 0.2) !important;
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .security-settings-root .alert-box.warning {
  background: linear-gradient(135deg, rgba(133, 77, 14, 0.22), rgba(15, 23, 42, 0.82)) !important;
  border-color: rgba(245, 158, 11, 0.24) !important;
  color: #fcd34d !important;
}

html[data-theme='dark'] .security-settings-root .sessions-stat-chip,
html[data-theme='dark'] .security-settings-root .session-item,
html[data-theme='dark'] .security-settings-root .sessions-empty-state {
  background:
      radial-gradient(circle at top right, rgba(56, 189, 248, 0.1), transparent 32%),
      linear-gradient(180deg, rgba(15, 23, 42, 0.88), rgba(17, 24, 39, 0.92)) !important;
  border-color: rgba(51, 65, 85, 0.95) !important;
}

html[data-theme='dark'] .security-settings-root .session-item:hover {
  background:
      radial-gradient(circle at top right, rgba(59, 130, 246, 0.12), transparent 34%),
      linear-gradient(180deg, rgba(17, 24, 39, 0.96), rgba(30, 41, 59, 0.94)) !important;
  border-color: #475569 !important;
  box-shadow: 0 18px 28px rgba(2, 6, 23, 0.24) !important;
}

html[data-theme='dark'] .security-settings-root .session-item.is-current {
  background:
      radial-gradient(circle at top right, rgba(34, 197, 94, 0.12), transparent 30%),
      linear-gradient(180deg, rgba(6, 78, 59, 0.28), rgba(15, 23, 42, 0.92)) !important;
  border-color: rgba(34, 197, 94, 0.34) !important;
}

html[data-theme='dark'] .security-settings-root .session-icon {
  background: rgba(30, 41, 59, 0.9) !important;
  color: #93c5fd !important;
}

html[data-theme='dark'] .security-settings-root .session-item.is-current .session-icon {
  background: rgba(6, 78, 59, 0.72) !important;
  color: #86efac !important;
}

html[data-theme='dark'] .security-settings-root .sessions-empty-state {
  border-style: dashed !important;
}

html[data-theme='dark'] .security-settings-root .eye-btn {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .security-settings-root .eye-btn:hover {
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .security-settings-root .btn-primary {
  background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
  color: #ffffff !important;
  border: 1px solid rgba(96, 165, 250, 0.28) !important;
  box-shadow:
      0 14px 28px rgba(29, 78, 216, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
}

html[data-theme='dark'] .security-settings-root .btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
  border-color: rgba(147, 197, 253, 0.34) !important;
}

html[data-theme='dark'] .security-settings-root .btn-primary:disabled,
html[data-theme='dark'] .security-settings-root .btn-danger:disabled {
  box-shadow: none !important;
}

html[data-theme='dark'] .session-confirm-overlay {
  background: rgba(2, 6, 23, 0.64) !important;
}

html[data-theme='dark'] .session-confirm-card {
  background:
      radial-gradient(circle at top right, rgba(14, 165, 233, 0.12), transparent 32%),
      linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(17, 24, 39, 0.98)) !important;
  border-color: #334155 !important;
  box-shadow:
      0 34px 72px rgba(2, 6, 23, 0.48),
      inset 0 1px 0 rgba(255, 255, 255, 0.04) !important;
  color: #f8fafc !important;
}

html[data-theme='dark'] .session-confirm-title,
html[data-theme='dark'] .session-confirm-meta-value {
  color: #f8fafc !important;
}

html[data-theme='dark'] .session-confirm-text {
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .session-confirm-meta-label {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .session-confirm-icon {
  background: linear-gradient(135deg, rgba(127, 29, 29, 0.42), rgba(30, 41, 59, 0.94)) !important;
  color: #fecaca !important;
}

html[data-theme='dark'] .session-confirm-meta-item {
  background: rgba(15, 23, 42, 0.76) !important;
  border-color: #334155 !important;
}

html[data-theme='dark'] .session-confirm-close {
  background: rgba(15, 23, 42, 0.82) !important;
  border-color: #334155 !important;
  color: #94a3b8 !important;
}

html[data-theme='dark'] .session-confirm-close:hover:not(:disabled) {
  background: rgba(30, 41, 59, 0.96) !important;
  color: #f8fafc !important;
}

html[data-theme='dark'] .session-confirm-btn.is-cancel {
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.88)) !important;
  border-color: #334155 !important;
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .session-confirm-btn.is-cancel:hover:not(:disabled) {
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.96), rgba(51, 65, 85, 0.94)) !important;
  border-color: #475569 !important;
  color: #f8fafc !important;
}

html[data-theme='dark'] .security-card .password-strength-title {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .security-card .password-strength-track {
  background: #334155 !important;
}

html[data-theme='dark'] .audit-card .btn-secondary {
  background: #1e293b !important;
  color: #cbd5e1 !important;
  border: 1px solid #475569 !important;
}

html[data-theme='dark'] .audit-card .btn-secondary:hover:not(:disabled) {
  background: #334155 !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .audit-card .btn-primary {
  background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
  color: #e2e8f0 !important;
  border: 1px solid #2563eb !important;
}

html[data-theme='dark'] .audit-card .btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
  border-color: #3b82f6 !important;
}

html[data-theme='dark'] .audit-card .filters-section,
html[data-theme='dark'] .audit-card .audit-list-shell,
html[data-theme='dark'] .audit-card .audit-entry,
html[data-theme='dark'] .audit-card .audit-disclosure,
html[data-theme='dark'] .audit-card .audit-detail-card.compact {
  background: #0f172a !important;
  border-color: #334155 !important;
}

html[data-theme='dark'] .audit-card .audit-entry:hover {
  background: #111827 !important;
}

html[data-theme='dark'] .audit-card .section-subtitle,
html[data-theme='dark'] .audit-card .results-caption.muted,
html[data-theme='dark'] .audit-card .audit-entry-time,
html[data-theme='dark'] .audit-card .audit-entry-meta-item,
html[data-theme='dark'] .audit-card .filter-group label,
html[data-theme='dark'] .audit-card .meta-label,
html[data-theme='dark'] .audit-card .search-icon {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .audit-card .section-title,
html[data-theme='dark'] .audit-card .results-caption,
html[data-theme='dark'] .audit-card .audit-entry-title,
html[data-theme='dark'] .audit-card .audit-section-title,
html[data-theme='dark'] .audit-card .audit-detail-value,
html[data-theme='dark'] .audit-card .meta-value {
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .audit-card .audit-entry-summary {
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .audit-card .form-input,
html[data-theme='dark'] .audit-card .pagination-bar {
  background: #111827 !important;
  border-color: #334155 !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .audit-card .pagination-title {
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .audit-card .audit-entry-tag,
html[data-theme='dark'] .audit-card .audit-action-code,
html[data-theme='dark'] .audit-card .load-more-wrapper {
  background: #111827 !important;
  border-color: #334155 !important;
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .audit-card .audit-entry-meta-item::before {
  background: #475569 !important;
}

html[data-theme='dark'] .audit-card .audit-action-chip.tone-success {
  background: rgba(22, 101, 52, 0.28) !important;
  border-color: rgba(74, 222, 128, 0.28) !important;
  color: #bbf7d0 !important;
}

html[data-theme='dark'] .audit-card .audit-action-chip.tone-warning {
  background: rgba(133, 77, 14, 0.28) !important;
  border-color: rgba(250, 204, 21, 0.24) !important;
  color: #fde68a !important;
}

html[data-theme='dark'] .audit-card .audit-action-chip.tone-danger {
  background: rgba(153, 27, 27, 0.3) !important;
  border-color: rgba(248, 113, 113, 0.28) !important;
  color: #fecaca !important;
}

html[data-theme='dark'] .audit-card .audit-action-chip.tone-neutral {
  background: rgba(51, 65, 85, 0.86) !important;
  border-color: rgba(100, 116, 139, 0.8) !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .audit-log-modal-overlay .audit-modal-card,
html[data-theme='dark'] .audit-log-modal-overlay .audit-detail-card,
html[data-theme='dark'] .audit-log-modal-overlay .audit-disclosure {
  background: #111827 !important;
  border-color: #334155 !important;
}

html[data-theme='dark'] .audit-log-modal-overlay .audit-modal-header,
html[data-theme='dark'] .audit-log-modal-overlay .modal-footer {
  background: #111827 !important;
  border-color: #334155 !important;
}

html[data-theme='dark'] .audit-log-modal-overlay .modal-title,
html[data-theme='dark'] .audit-log-modal-overlay .audit-section-title,
html[data-theme='dark'] .audit-log-modal-overlay .audit-detail-value,
html[data-theme='dark'] .audit-log-modal-overlay .meta-value {
  color: #f8fafc !important;
}

html[data-theme='dark'] .audit-log-modal-overlay .modal-subtitle,
html[data-theme='dark'] .audit-log-modal-overlay .meta-label,
html[data-theme='dark'] .audit-log-modal-overlay .audit-detail-label,
html[data-theme='dark'] .audit-log-modal-overlay .audit-disclosure summary,
html[data-theme='dark'] .audit-log-modal-overlay .audit-action-code {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .audit-log-modal-overlay .audit-action-code,
html[data-theme='dark'] .audit-log-modal-overlay .audit-detail-card.compact {
  background: #0f172a !important;
  border-color: #334155 !important;
}

html[data-theme='dark'] .audit-log-modal-overlay .audit-disclosure-content {
  border-top-color: #334155 !important;
}

html[data-theme='dark'] .audit-log-modal-overlay .close-btn {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .audit-log-modal-overlay .close-btn:hover {
  color: #f8fafc !important;
}

html[data-theme='dark'] .audit-log-modal-overlay .audit-modal-close {
  background: rgba(15, 23, 42, 0.82) !important;
  border: 1px solid #334155 !important;
  color: #94a3b8 !important;
}

html[data-theme='dark'] .audit-log-modal-overlay .audit-modal-close:hover {
  background: rgba(30, 41, 59, 0.96) !important;
  color: #f8fafc !important;
}

html[data-theme='dark'] .analytics-jump-controls {
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(17, 24, 39, 0.94)) !important;
  border-color: #334155 !important;
  box-shadow: 0 16px 32px rgba(2, 6, 23, 0.42) !important;
  backdrop-filter: blur(18px) !important;
}

html[data-theme='dark'] .analytics-jump-controls .jump-arrow-btn {
  background: #0f172a !important;
  border-color: #334155 !important;
  color: #cbd5e1 !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03) !important;
}

html[data-theme='dark'] .analytics-jump-controls .jump-arrow-btn:hover {
  background: rgba(37, 99, 235, 0.18) !important;
  border-color: #60a5fa !important;
  color: #dbeafe !important;
}

html[data-theme='dark'] .table-row:hover,
html[data-theme='dark'] .clickable-row:hover {
  background-color: rgba(148, 163, 184, 0.12) !important;
}

html[data-theme='dark'] .role-btn.btn-down:hover {
  background: rgba(245, 158, 11, 0.18) !important;
  color: #fbbf24 !important;
}

html[data-theme='dark'] .role-btn.btn-up:hover {
  background: rgba(16, 185, 129, 0.18) !important;
  color: #34d399 !important;
}

html[data-theme='dark'] .action-btn.edit:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.2) !important;
  color: #93c5fd !important;
}

html[data-theme='dark'] .floor-section .floor-header:hover {
  background: rgba(148, 163, 184, 0.12) !important;
}

html[data-theme='dark'] .floor-section .classroom-card {
  background: var(--surface-soft) !important;
  border-color: var(--border) !important;
}

html[data-theme='dark'] .floor-section .classroom-card:hover {
  border-color: #60a5fa !important;
  box-shadow: 0 14px 30px rgba(2, 6, 23, 0.45) !important;
}

html[data-theme='dark'] .floor-section .classroom-info {
  border-top-color: var(--border) !important;
}

html[data-theme='dark'] .floor-section .classroom-number {
  color: #93c5fd !important;
  text-shadow: none !important;
}

html[data-theme='dark'] .floor-section .floor-subtitle {
  color: var(--text-secondary) !important;
}

html[data-theme='dark'] .floor-section .classroom-card.compact-mode {
  background: #0f172a !important;
  border-color: #334155 !important;
}

html[data-theme='dark'] .floor-section .compact-chip {
  background: linear-gradient(145deg, rgba(30, 41, 59, 0.96), rgba(15, 23, 42, 0.96)) !important;
  border-color: #334155 !important;
  box-shadow: none !important;
}

html[data-theme='dark'] .floor-section .classroom-row-title {
  color: var(--text-primary) !important;
}

html[data-theme='dark'] .floor-section .classroom-quick-stat,
html[data-theme='dark'] .floor-section .classroom-row-arrow {
  background: #1e293b !important;
  border-color: #334155 !important;
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .floor-section .classroom-quick-stat svg,
html[data-theme='dark'] .floor-section .classroom-row-arrow svg {
  color: #93c5fd !important;
}

html[data-theme='dark'] .floor-section .classroom-status-badge.status-working {
  background: rgba(20, 83, 45, 0.45) !important;
  border-color: rgba(34, 197, 94, 0.28) !important;
  color: #86efac !important;
}

html[data-theme='dark'] .floor-section .classroom-status-badge.status-broken {
  background: rgba(127, 29, 29, 0.4) !important;
  border-color: rgba(248, 113, 113, 0.28) !important;
  color: #fca5a5 !important;
}

@media (max-width: 480px) {
  html[data-theme='dark'] .floor-section .classroom-quick-stat,
  html[data-theme='dark'] .floor-section .classroom-status-badge.status-working,
  html[data-theme='dark'] .floor-section .classroom-status-badge.status-broken {
    background: transparent !important;
    border-color: transparent !important;
    box-shadow: none !important;
  }
}

html[data-theme='dark'] .create-audience-page {
  background: #020617 !important;
}

html[data-theme='dark'] .create-audience-page .page-title {
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .create-audience-page .back-btn {
  background: #0f172a !important;
  border-color: #334155 !important;
  color: #93c5fd !important;
}

html[data-theme='dark'] .create-audience-page .back-btn:hover {
  background: #1d4ed8 !important;
  border-color: #1d4ed8 !important;
  color: #f8fafc !important;
}

html[data-theme='dark'] .create-audience-page .panel,
html[data-theme='dark'] .create-audience-page .grid-panel {
  background: #111827 !important;
  border: 1px solid #334155 !important;
  box-shadow: 0 14px 32px rgba(2, 6, 23, 0.44) !important;
}

html[data-theme='dark'] .create-audience-page .collapse-icon {
  background: #1e293b !important;
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .create-audience-page .collapse-icon:hover {
  background: #334155 !important;
}

html[data-theme='dark'] .create-audience-page .panel-title {
  color: #f8fafc !important;
}

html[data-theme='dark'] .create-audience-page .panel-hint,
html[data-theme='dark'] .create-audience-page .form-label,
html[data-theme='dark'] .create-audience-page .grid-info,
html[data-theme='dark'] .create-audience-page .stat-label {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .create-audience-page .form-input,
html[data-theme='dark'] .create-audience-page .form-select {
  background-color: #0f172a !important;
  border-color: #334155 !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .create-audience-page .form-input::placeholder {
  color: #64748b !important;
}

html[data-theme='dark'] .create-audience-page .form-input:disabled {
  background: #111827 !important;
  border-color: #334155 !important;
  color: #94a3b8 !important;
}

html[data-theme='dark'] .create-audience-page .form-input:focus,
html[data-theme='dark'] .create-audience-page .form-select:focus {
  border-color: #60a5fa !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
}

html[data-theme='dark'] .create-audience-page .form-select {
  background-image: url("data:image/svg+xml,%3Csvg width='12' height='8' viewBox='0 0 12 8' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%23cbd5e1' stroke-width='2' fill='none'/%3E%3C/svg%3E") !important;
  background-repeat: no-repeat !important;
  background-position: right 14px center !important;
  background-size: 12px 8px !important;
  padding-right: 40px !important;
  appearance: none !important;
  -webkit-appearance: none !important;
  -moz-appearance: none !important;
}

html[data-theme='dark'] .create-audience-page .equipment-item {
  background: linear-gradient(145deg, #0f172a, #111827) !important;
  border-color: #334155 !important;
}

html[data-theme='dark'] .create-audience-page .equipment-item:hover {
  border-color: #60a5fa !important;
  box-shadow: 0 10px 20px rgba(2, 6, 23, 0.45) !important;
}

html[data-theme='dark'] .create-audience-page .equipment-item.selected {
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.34), rgba(37, 99, 235, 0.24)) !important;
  border-color: #60a5fa !important;
}

html[data-theme='dark'] .create-audience-page .equipment-name {
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .create-audience-page .stats-panel {
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.28), rgba(15, 23, 42, 0.8)) !important;
  border-color: #3b82f6 !important;
}

html[data-theme='dark'] .create-audience-page .stat-value {
  color: #bfdbfe !important;
}

html[data-theme='dark'] .create-audience-page .btn-secondary {
  background: #1e293b !important;
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .create-audience-page .btn-secondary:hover {
  background: #334155 !important;
  color: #f8fafc !important;
}

html[data-theme='dark'] .create-audience-page .clear-grid-btn {
  background: rgba(127, 29, 29, 0.2) !important;
  border-color: rgba(248, 113, 113, 0.48) !important;
  color: #fca5a5 !important;
}

html[data-theme='dark'] .create-audience-page .clear-grid-btn:hover {
  background: rgba(153, 27, 27, 0.3) !important;
  border-color: rgba(252, 165, 165, 0.58) !important;
}

html[data-theme='dark'] .create-audience-page .clear-grid-btn:disabled {
  background: rgba(30, 41, 59, 0.78) !important;
  border-color: #334155 !important;
  color: #64748b !important;
}

html[data-theme='dark'] .create-audience-page .clear-grid-btn.is-armed {
  background: linear-gradient(135deg, rgba(127, 29, 29, 0.36), rgba(159, 18, 57, 0.24)) !important;
  border-color: rgba(251, 113, 133, 0.52) !important;
  color: #fecdd3 !important;
}

html[data-theme='dark'] .create-audience-page .clear-grid-btn.is-danger {
  background: linear-gradient(135deg, #dc2626, #be123c) !important;
  border-color: transparent !important;
  color: #ffffff !important;
}

html[data-theme='dark'] .create-audience-page .clear-grid-confirm {
  background:
      radial-gradient(circle at top left, rgba(244, 63, 94, 0.18), transparent 34%),
      linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(30, 41, 59, 0.96)) !important;
  border-color: rgba(251, 113, 133, 0.28) !important;
  box-shadow: 0 24px 48px rgba(2, 6, 23, 0.42) !important;
}

html[data-theme='dark'] .create-audience-page .clear-grid-confirm-icon {
  background: linear-gradient(135deg, rgba(127, 29, 29, 0.48), rgba(159, 18, 57, 0.3)) !important;
  color: #fda4af !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04) !important;
}

html[data-theme='dark'] .create-audience-page .clear-grid-confirm-title {
  color: #ffe4e6 !important;
}

html[data-theme='dark'] .create-audience-page .clear-grid-confirm-text {
  color: #fbcfe8 !important;
}

html[data-theme='dark'] .create-audience-leave-modal {
  background: rgba(2, 6, 23, 0.78) !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}

html[data-theme='dark'] .create-audience-leave-modal .leave-guard-card {
  background:
      radial-gradient(circle at top right, rgba(37, 99, 235, 0.16), transparent 32%),
      linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(17, 24, 39, 0.98)) !important;
  border-color: rgba(250, 204, 21, 0.18) !important;
  box-shadow:
      0 28px 54px rgba(2, 6, 23, 0.44),
      inset 0 1px 0 rgba(255, 255, 255, 0.04) !important;
}

html[data-theme='dark'] .create-audience-leave-modal .leave-guard-close {
  background: rgba(15, 23, 42, 0.9) !important;
  border-color: #334155 !important;
  color: #94a3b8 !important;
}

html[data-theme='dark'] .create-audience-leave-modal .leave-guard-close:hover {
  background: rgba(30, 41, 59, 0.96) !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .create-audience-leave-modal .leave-guard-icon {
  background: linear-gradient(135deg, rgba(146, 64, 14, 0.38), rgba(180, 83, 9, 0.24)) !important;
  color: #fcd34d !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04) !important;
}

html[data-theme='dark'] .create-audience-leave-modal .leave-guard-kicker {
  color: #fbbf24 !important;
}

html[data-theme='dark'] .create-audience-leave-modal .leave-guard-title {
  color: #f8fafc !important;
}

html[data-theme='dark'] .create-audience-leave-modal .leave-guard-text {
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .create-audience-leave-modal .leave-guard-actions {
  border-top-color: #334155 !important;
}

html[data-theme='dark'] .create-audience-leave-modal .leave-guard-btn {
  background: #1e293b !important;
  border-color: #334155 !important;
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .create-audience-leave-modal .leave-guard-btn:hover {
  background: #334155 !important;
  color: #f8fafc !important;
}

html[data-theme='dark'] .create-audience-page .grid-container {
  background: #0b1220 !important;
  border-color: #334155 !important;
}

html[data-theme='dark'] .create-audience-page .grid-cell {
  background: #0f172a !important;
  border-color: #334155 !important;
}

html[data-theme='dark'] .create-audience-page .grid-cell:hover {
  background: #172554 !important;
  border-color: #60a5fa !important;
}

/* CreateAudience: новое оборудование поверх сетки */
html[data-theme='dark'] .create-audience-page .grid-equipment {
  background: linear-gradient(145deg, #0f172a, #111827) !important;
  border: 1px solid #334155 !important;
  box-shadow: 0 10px 20px rgba(2, 6, 23, 0.45) !important;
}

html[data-theme='dark'] .create-audience-page .grid-equipment:hover {
  border-color: #60a5fa !important;
  box-shadow: 0 14px 28px rgba(2, 6, 23, 0.52) !important;
}

html[data-theme='dark'] .create-audience-page .grid-equipment.broken {
  background: linear-gradient(135deg, rgba(127, 29, 29, 0.52), rgba(220, 38, 38, 0.24)) !important;
  border-color: rgba(248, 113, 113, 0.66) !important;
}

html[data-theme='dark'] .create-audience-page .size-btn {
  background: #0f172a !important;
  border-color: #334155 !important;
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .create-audience-page .size-btn:hover {
  background: #172554 !important;
  border-color: #60a5fa !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .create-audience-page .size-btn.active {
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.36), rgba(37, 99, 235, 0.24)) !important;
  border-color: #60a5fa !important;
  color: #dbeafe !important;
}

/* AudienceView: карточка оборудования в overlay */
html[data-theme='dark'] .create-audience-page .grid-landmark-line,
html[data-theme='dark'] .create-audience-page .grid-landmark-side {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .create-audience-page .landmark-edit-btn {
  background: rgba(15, 23, 42, 0.9) !important;
  border-color: rgba(71, 85, 105, 0.58) !important;
  color: #cbd5e1 !important;
  box-shadow: 0 12px 24px rgba(2, 6, 23, 0.3) !important;
}

html[data-theme='dark'] .create-audience-page .landmark-edit-btn:hover {
  border-color: rgba(96, 165, 250, 0.5) !important;
  color: #93c5fd !important;
}

html[data-theme='dark'] .create-audience-page .landmark-editor-popup {
  background: rgba(15, 23, 42, 0.96) !important;
  border-color: #334155 !important;
  box-shadow: 0 20px 40px rgba(2, 6, 23, 0.48) !important;
}

html[data-theme='dark'] .create-audience-page .landmark-editor-title {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .create-audience-page .landmark-editor-input {
  background: #0b1220 !important;
  border-color: #334155 !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .create-audience-page .landmark-editor-input::placeholder {
  color: #64748b !important;
}

html[data-theme='dark'] .create-audience-page .landmark-editor-input:focus {
  border-color: #60a5fa !important;
  background: #0f172a !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.18) !important;
}

html[data-theme='dark'] .create-audience-page .landmark-editor-action {
  background: #111827 !important;
  border-color: #334155 !important;
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .create-audience-page .landmark-editor-action:hover {
  border-color: #475569 !important;
  color: #f8fafc !important;
}

html[data-theme='dark'] .create-audience-page .landmark-editor-action.is-confirm {
  background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
  border-color: transparent !important;
  color: #ffffff !important;
}

html[data-theme='dark'] .page-viewer .grid-equipment {
  background: #111827 !important;
  border: 2px solid #334155 !important;
  box-shadow: 0 12px 24px rgba(2, 6, 23, 0.38) !important;
}

html[data-theme='dark'] .page-viewer .grid-equipment.working {
  background: linear-gradient(135deg, #14281c, #183223) !important;
  border-color: rgba(74, 222, 128, 0.42) !important;
}

html[data-theme='dark'] .page-viewer .grid-equipment.broken {
  background: linear-gradient(135deg, #2a1415, #38181b) !important;
  border-color: rgba(248, 113, 113, 0.46) !important;
}

html[data-theme='dark'] .page-viewer .grid-equipment:hover {
  border-color: #60a5fa !important;
  box-shadow: 0 14px 28px rgba(2, 6, 23, 0.5) !important;
}

html[data-theme='dark'] .page-viewer .specs-card {
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(17, 24, 39, 0.98)) !important;
  border-color: #334155 !important;
  box-shadow: 0 18px 40px rgba(2, 6, 23, 0.34) !important;
}

html[data-theme='dark'] .page-viewer .specs-modal-content {
  background:
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.2), transparent 34%),
    linear-gradient(180deg, #0f172a 0%, #111827 100%) !important;
}

html[data-theme='dark'] .page-viewer .specs-header-subtitle,
html[data-theme='dark'] .page-viewer .specs-modal-description,
html[data-theme='dark'] .page-viewer .specs-empty-text,
html[data-theme='dark'] .page-viewer .specs-form-banner-text,
html[data-theme='dark'] .page-viewer .specs-meta-label,
html[data-theme='dark'] .page-viewer .spec-card-label,
html[data-theme='dark'] .page-viewer .spec-suffix {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .page-viewer .specs-modal-heading,
html[data-theme='dark'] .page-viewer .specs-modal-name,
html[data-theme='dark'] .page-viewer .specs-meta-value,
html[data-theme='dark'] .page-viewer .spec-card-value,
html[data-theme='dark'] .page-viewer .specs-empty-title,
html[data-theme='dark'] .page-viewer .specs-form-banner-title,
html[data-theme='dark'] .page-viewer .spec-form-label,
html[data-theme='dark'] .page-viewer .spec-input,
html[data-theme='dark'] .page-viewer .bool-btn {
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .page-viewer .specs-meta-pill,
html[data-theme='dark'] .page-viewer .specs-modal-progress,
html[data-theme='dark'] .page-viewer .spec-form-group,
html[data-theme='dark'] .page-viewer .spec-card,
html[data-theme='dark'] .page-viewer .specs-empty {
  background: rgba(15, 23, 42, 0.72) !important;
  border-color: #334155 !important;
}

html[data-theme='dark'] .page-viewer .specs-modal-progress-head {
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .page-viewer .specs-modal-progress-track {
  background: #1e3a8a !important;
}

html[data-theme='dark'] .page-viewer .specs-modal-progress-track span {
  background: linear-gradient(135deg, #60a5fa, #2563eb) !important;
}

html[data-theme='dark'] .page-viewer .specs-meta-icon,
html[data-theme='dark'] .page-viewer .spec-card-icon {
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.46), rgba(37, 99, 235, 0.3)) !important;
  color: #bfdbfe !important;
}

html[data-theme='dark'] .page-viewer .spec-card-pair-divider {
  background: linear-gradient(180deg, rgba(96, 165, 250, 0.12), rgba(71, 85, 105, 0.9), rgba(96, 165, 250, 0.12)) !important;
}

html[data-theme='dark'] .page-viewer .specs-form-banner {
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.28), rgba(15, 23, 42, 0.82)) !important;
  border-color: rgba(96, 165, 250, 0.4) !important;
}

html[data-theme='dark'] .page-viewer .specs-form-banner-icon {
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.34) !important;
}

html[data-theme='dark'] .page-viewer .spec-input,
html[data-theme='dark'] .page-viewer .bool-btn {
  background-color: rgba(15, 23, 42, 0.88) !important;
  border-color: #475569 !important;
}

html[data-theme='dark'] .page-viewer .bool-segment-btn {
  background: rgba(15, 23, 42, 0.88) !important;
  border-color: #475569 !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .page-viewer .bool-segment-btn.active {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.42), rgba(30, 64, 175, 0.32)) !important;
  border-color: #60a5fa !important;
  color: #dbeafe !important;
  box-shadow: 0 10px 22px rgba(37, 99, 235, 0.22) !important;
}

html[data-theme='dark'] .page-viewer .bool-clear-btn {
  background: rgba(30, 41, 59, 0.9) !important;
  border-color: #475569 !important;
  color: #94a3b8 !important;
}

html[data-theme='dark'] .page-viewer .bool-clear-btn.active {
  background: linear-gradient(135deg, rgba(51, 65, 85, 0.96), rgba(30, 41, 59, 0.96)) !important;
  border-color: #64748b !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .page-viewer .spec-select {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20' fill='none'%3E%3Cpath d='m5 7.5l5 5l5-5' stroke='%2394a3b8' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") !important;
  background-repeat: no-repeat !important;
  background-position: right 14px center !important;
  background-size: 16px 16px !important;
}

html[data-theme='dark'] .page-viewer .bool-btn-muted {
  background: rgba(30, 41, 59, 0.9) !important;
  color: #94a3b8 !important;
  border-color: #475569 !important;
}

html[data-theme='dark'] .page-viewer .bool-btn.active {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.42), rgba(30, 64, 175, 0.32)) !important;
  border-color: #60a5fa !important;
  color: #dbeafe !important;
  box-shadow: 0 10px 22px rgba(37, 99, 235, 0.22) !important;
}

html[data-theme='dark'] .page-viewer .bool-btn-muted.active {
  background: linear-gradient(135deg, rgba(51, 65, 85, 0.96), rgba(30, 41, 59, 0.96)) !important;
  border-color: #64748b !important;
  color: #e2e8f0 !important;
  box-shadow: none !important;
}

html[data-theme='dark'] .page-viewer {
  background: #0b1220 !important;
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
}

html[data-theme='dark'] .create-audience-page .grid-cell.drag-over {
  background: rgba(30, 64, 175, 0.45) !important;
  border-color: #93c5fd !important;
}

html[data-theme='dark'] .create-audience-page .cell-label {
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .create-audience-page .remove-btn {
  border: 1px solid rgba(248, 113, 113, 0.6) !important;
}

html[data-theme='dark'] .create-audience-page .remove-btn:hover {
  background: #b91c1c !important;
}

html[data-theme='dark'] .create-audience-page .empty-grid {
  color: #94a3b8 !important;
}

/* CreateAudience: remove the gray glass effect from dark mode. */
html[data-theme='dark'] .create-audience-page,
html[data-theme='dark'] .create-audience-page .panel,
html[data-theme='dark'] .create-audience-page .grid-panel,
html[data-theme='dark'] .create-audience-page .grid-container,
html[data-theme='dark'] .create-audience-page .grid-cell,
html[data-theme='dark'] .create-audience-page .stats-panel,
html[data-theme='dark'] .create-audience-page .equipment-item,
html[data-theme='dark'] .create-audience-page .grid-equipment,
html[data-theme='dark'] .create-audience-page .history-actions,
html[data-theme='dark'] .create-audience-page .clear-grid-confirm,
html[data-theme='dark'] .create-audience-page .landmark-edit-btn,
html[data-theme='dark'] .create-audience-page .landmark-editor-popup,
html[data-theme='dark'] .create-audience-leave-modal,
html[data-theme='dark'] .create-audience-leave-modal .leave-guard-card {
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}

html[data-theme='dark'] .create-audience-page {
  background: #020617 !important;
}

html[data-theme='dark'] .create-audience-page .panel,
html[data-theme='dark'] .create-audience-page .grid-panel {
  background: #06101f !important;
  border-color: #1e3a8a !important;
  box-shadow: none !important;
}

html[data-theme='dark'] .create-audience-page .grid-container,
html[data-theme='dark'] .create-audience-page .history-actions {
  background: #020617 !important;
  border-color: #1e3a8a !important;
  box-shadow: none !important;
}

html[data-theme='dark'] .create-audience-page .grid-cell {
  background: #081426 !important;
  border-color: #1e293b !important;
}

html[data-theme='dark'] .create-audience-page .grid-cell:hover,
html[data-theme='dark'] .create-audience-page .grid-cell.drag-over {
  background: #102554 !important;
  border-color: #60a5fa !important;
}

html[data-theme='dark'] .create-audience-page .equipment-item,
html[data-theme='dark'] .create-audience-page .grid-equipment,
html[data-theme='dark'] .create-audience-page .stats-panel,
html[data-theme='dark'] .create-audience-page .form-input,
html[data-theme='dark'] .create-audience-page .form-select,
html[data-theme='dark'] .create-audience-page .landmark-editor-input,
html[data-theme='dark'] .create-audience-page .size-btn,
html[data-theme='dark'] .create-audience-page .btn-secondary,
html[data-theme='dark'] .create-audience-page .collapse-icon,
html[data-theme='dark'] .create-audience-page .landmark-edit-btn,
html[data-theme='dark'] .create-audience-page .landmark-editor-popup,
html[data-theme='dark'] .create-audience-page .landmark-editor-action {
  background: #0b1220 !important;
  border-color: #1e3a8a !important;
  box-shadow: none !important;
}

html[data-theme='dark'] .create-audience-page .equipment-item:hover,
html[data-theme='dark'] .create-audience-page .grid-equipment:hover,
html[data-theme='dark'] .create-audience-page .size-btn:hover,
html[data-theme='dark'] .create-audience-page .btn-secondary:hover,
html[data-theme='dark'] .create-audience-page .collapse-icon:hover,
html[data-theme='dark'] .create-audience-page .landmark-edit-btn:hover,
html[data-theme='dark'] .create-audience-page .landmark-editor-action:hover {
  background: #102554 !important;
  border-color: #60a5fa !important;
  color: #e2e8f0 !important;
  box-shadow: none !important;
}

html[data-theme='dark'] .create-audience-page .equipment-item.selected,
html[data-theme='dark'] .create-audience-page .size-btn.active {
  background: #12306b !important;
  border-color: #60a5fa !important;
  color: #dbeafe !important;
  box-shadow: none !important;
}

html[data-theme='dark'] .create-audience-page .grid-equipment.broken {
  background: #3b1218 !important;
  border-color: #fb7185 !important;
}

html[data-theme='dark'] .create-audience-page .clear-grid-confirm {
  background: #160b13 !important;
  border-color: #9f1239 !important;
  box-shadow: none !important;
}

html[data-theme='dark'] .create-audience-page .clear-grid-confirm-icon {
  background: #3b1218 !important;
  box-shadow: none !important;
}

html[data-theme='dark'] .create-audience-page .clear-grid-btn {
  background: #3b1218 !important;
  border-color: #9f1239 !important;
}

html[data-theme='dark'] .create-audience-page .clear-grid-btn:hover,
html[data-theme='dark'] .create-audience-page .clear-grid-btn.is-armed {
  background: #4c1420 !important;
  border-color: #fb7185 !important;
}

html[data-theme='dark'] .create-audience-page .clear-grid-btn:disabled {
  background: #0b1220 !important;
  border-color: #1e293b !important;
}

html[data-theme='dark'] .create-audience-leave-modal {
  background: rgba(2, 6, 23, 0.92) !important;
}

html[data-theme='dark'] .create-audience-leave-modal .leave-guard-card,
html[data-theme='dark'] .create-audience-leave-modal .leave-guard-close,
html[data-theme='dark'] .create-audience-leave-modal .leave-guard-btn {
  background: #06101f !important;
  border-color: #1e3a8a !important;
  box-shadow: none !important;
}

html[data-theme='dark'] .create-audience-leave-modal .leave-guard-icon {
  background: #2a1b08 !important;
  box-shadow: none !important;
}

html[data-theme='dark'] .page-viewer .classroom-number {
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .page-viewer .classroom-subtitle {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .page-viewer .back-btn {
  background: #1e293b !important;
  border-color: #475569 !important;
  color: #93c5fd !important;
}

html[data-theme='dark'] .page-viewer .back-btn:hover {
  background: #2563eb !important;
  border-color: #2563eb !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .page-viewer .stat-card {
  background: #111827 !important;
  border-color: #334155 !important;
}

html[data-theme='dark'] .page-viewer .stat-value {
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .page-viewer .stat-label {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .page-viewer .grid-section {
  background: #111827 !important;
  border-color: #334155 !important;
}

html[data-theme='dark'] .page-viewer .grid-title {
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .page-viewer .grid-landmark-line,
html[data-theme='dark'] .page-viewer .grid-landmark-side {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .page-viewer .grid-info {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .page-viewer .top-header {
  background: transparent !important;
  box-shadow: none !important;
  border: none !important;
}

html[data-theme='dark'] .page-viewer .grid-tools > .scale-type-btn {
  background: #1e293b !important;
  border-color: #475569 !important;
  color: #93c5fd !important;
  box-shadow: none !important;
}

html[data-theme='dark'] .page-viewer .grid-tools > .scale-type-btn:hover {
  background: #2563eb !important;
  border-color: #2563eb !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .page-viewer .grid-tools > .scale-type-btn:focus-visible {
  outline: none !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25) !important;
}

html[data-theme='dark'] .page-viewer .equipment-grid {
  background: #0f172a !important;
  border-color: #334155 !important;
}

html[data-theme='dark'] .page-viewer .scale-controls {
  background: #0f172a !important;
  border-color: #334155 !important;
}

html[data-theme='dark'] .page-viewer .scale-controls input[type="range"] {
  background: transparent !important;
  border: none !important;
  border-radius: 999px !important;
  height: 18px !important;
  padding: 0 !important;
}

html[data-theme='dark'] .page-viewer .scale-controls input[type="range"]::-webkit-slider-runnable-track {
  height: 6px !important;
  border: none !important;
  border-radius: 999px !important;
  background: linear-gradient(90deg, #3b82f6 0%, #334155 100%) !important;
}

html[data-theme='dark'] .page-viewer .scale-controls input[type="range"]::-webkit-slider-thumb {
  background: #1e293b !important;
  border: 2px solid #60a5fa !important;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.35) !important;
}

html[data-theme='dark'] .page-viewer .scale-controls input[type="range"]::-moz-range-track {
  height: 6px !important;
  border: none !important;
  border-radius: 999px !important;
  background: linear-gradient(90deg, #3b82f6 0%, #334155 100%) !important;
}

html[data-theme='dark'] .page-viewer .scale-controls input[type="range"]::-moz-range-thumb {
  background: #1e293b !important;
  border: 2px solid #60a5fa !important;
}

html[data-theme='dark'] .page-viewer .grid-cell {
  background: #1e293b !important;
  border-color: #334155 !important;
}

html[data-theme='dark'] .page-viewer .grid-cell.empty {
  background: #0f172a !important;
  border-color: #334155 !important;
}

html[data-theme='dark'] .page-viewer .grid-cell.occupied.working {
  background: linear-gradient(135deg, rgba(22, 163, 74, 0.18), rgba(74, 222, 128, 0.16)) !important;
  border-color: rgba(74, 222, 128, 0.4) !important;
}

html[data-theme='dark'] .page-viewer .grid-cell.occupied.broken {
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.16), rgba(248, 113, 113, 0.14)) !important;
  border-color: rgba(248, 113, 113, 0.4) !important;
}

html[data-theme='dark'] .page-viewer .equipment-label {
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .page-viewer .modal-content {
  background: #111827 !important;
  border: 1px solid #334155 !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .page-viewer .modal-title {
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .page-viewer .modal-subtitle {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .page-viewer .modal-equipment-info {
  background: #0f172a !important;
  border: 1px solid #334155 !important;
}

html[data-theme='dark'] .page-viewer .modal-equipment-details h3,
html[data-theme='dark'] .page-viewer .modal-equipment-details > div > h3 {
  color: #f8fafc !important;
}

html[data-theme='dark'] .page-viewer .specs-entry-btn {
  background: linear-gradient(135deg, #1e3a8a, #1d4ed8) !important;
  border-color: #60a5fa !important;
  color: #eff6ff !important;
}

html[data-theme='dark'] .page-viewer .specs-entry-btn:hover {
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.28) !important;
}

html[data-theme='dark'] .page-viewer .specs-entry-chip {
  background: rgba(15, 23, 42, 0.92) !important;
  border-color: #334155 !important;
  box-shadow: 0 10px 18px rgba(2, 6, 23, 0.22) !important;
}

html[data-theme='dark'] .page-viewer .specs-entry-chip-text {
  color: #94a3b8 !important;
}

html[data-theme='dark'] .page-viewer .specs-entry-chip-dot {
  background: #64748b !important;
}

html[data-theme='dark'] .page-viewer .specs-entry-chip.is-partial {
  background: rgba(30, 64, 175, 0.22) !important;
  border-color: rgba(96, 165, 250, 0.42) !important;
}

html[data-theme='dark'] .page-viewer .specs-entry-chip.is-partial .specs-entry-chip-dot {
  background: #60a5fa !important;
}

html[data-theme='dark'] .page-viewer .specs-entry-chip.is-complete {
  background: rgba(20, 83, 45, 0.34) !important;
  border-color: rgba(74, 222, 128, 0.5) !important;
}

html[data-theme='dark'] .page-viewer .specs-entry-chip.is-complete .specs-entry-chip-dot {
  background: #4ade80 !important;
}

html[data-theme='dark'] .page-viewer .specs-entry-chip.is-empty {
  background: rgba(30, 41, 59, 0.88) !important;
  border-color: #475569 !important;
}

html[data-theme='dark'] .page-viewer .hw-section-title {
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .page-viewer .hw-files-section {
  border-top: 1px solid #334155 !important;
}

html[data-theme='dark'] .page-viewer .modal-close-upper button {
  background: #0f172a !important;
  border: 1px solid #334155 !important;
}

html[data-theme='dark'] .page-viewer .modal-close-upper button:hover {
  background: #1e293b !important;
}

html[data-theme='dark'] .page-viewer .cancel-btn {
  background: #1e293b !important;
  color: #cbd5e1 !important;
  border: 1px solid #475569 !important;
}

html[data-theme='dark'] .page-viewer .cancel-btn:hover {
  background: #334155 !important;
  color: #e2e8f0 !important;
}

html[data-theme='dark'] .page-viewer .warning-box {
  background: linear-gradient(135deg, rgba(127, 29, 29, 0.34), rgba(153, 27, 27, 0.22)) !important;
  border-color: rgba(248, 113, 113, 0.58) !important;
}

html[data-theme='dark'] .page-viewer .warning-box p {
  color: #fecaca !important;
}

html[data-theme='dark'] .page-viewer .warning-box svg {
  color: #f87171 !important;
}

html[data-theme='dark'] .login-title,
html[data-theme='dark'] .login-label,
html[data-theme='dark'] .login-signup-link,
html[data-theme='dark'] .divider span,
html[data-theme='dark'] .close svg,
html[data-theme='dark'] .input-icon,
html[data-theme='dark'] .toggle-password {
  color: var(--text-primary) !important;
  stroke: var(--text-primary) !important;
}

html[data-theme='dark'] .divider::before {
  background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.32), transparent) !important;
}

html[data-theme='dark'] .divider span {
  background: rgba(15, 23, 42, 0.85) !important;
  border: 1px solid #334155 !important;
  color: #cbd5e1 !important;
}

html[data-theme='dark'] .close {
  background: rgba(15, 23, 42, 0.7) !important;
  border-color: var(--border) !important;
}

html[data-theme='dark'],
html[data-theme='dark'] body,
html[data-theme='dark'] #app {
  background: #0b1220 !important;
}

html[data-theme='dark'] body {
  overflow-x: hidden;
}

html[data-theme='dark'] .page-viewer {
  width: 100%;
  max-width: 100vw;
  min-width: 0;
  background: #0b1220 !important;
  background-image: none !important;
  border: 0 !important;
  outline: 0 !important;
  box-shadow: none !important;
  overflow-x: clip;
}

.pt-1 {
  padding-top: 1rem !important;
}
</style>
