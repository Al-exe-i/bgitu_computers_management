<script>
import NotificationTypeIcon from "@/components/Layout/NotificationTypeIcon.vue";
import {useNotificationsStore} from "@/stores/notifications.js";

export default {
  name: "NotificationsModal",
  components: {
    NotificationTypeIcon,
  },
  computed: {
    notificationsStore()
    {
      return useNotificationsStore()
    }
  },
  methods: {
    getTitle(type)
    {
      const titles = {
        success: 'Успешно',
        info: 'Информация',
        warning: 'Внимание',
        error: 'Ошибка'
      };
      return titles[type]
    },
    closeNotification(id)
    {
      this.notificationsStore.remove(id)
    },
    getProgressStyle(notif)
    {
      const progress = Number.isFinite(notif.progress) ? Math.min(100, Math.max(0, notif.progress)) : 100
      const duration = Number.isFinite(notif.duration) ? Math.max(0, notif.duration) : 5000

      return {
        strokeDasharray: `${progress} 100`,
        transitionDuration: `${duration}ms`
      }
    }
  }
}
</script>

<template>
  <div class="notifications-container">
    <transition-group name="notification">
      <div
          v-for="notif in notificationsStore.notifications"
          :key="notif.id"
          class="notification"
          :class="notif.type"
      >
        <div class="notification-icon">
          <NotificationTypeIcon :type="notif.type" />
        </div>
        <div class="notification-content">
          <div class="notification-title">{{ notif.title || getTitle(notif.type) }}</div>
          <div class="notification-message">{{ notif.text }}</div>
        </div>
        <button class="notification-close" @click="closeNotification(notif.id)">✕</button>

        <svg
            v-if="notif.duration > 0"
            class="notification-progress-ring"
            aria-hidden="true"
        >
          <rect
              class="notification-progress-track"
              x="0"
              y="0"
              width="100%"
              height="100%"
              rx="16"
              ry="16"
              pathLength="100"
          />
          <rect
              class="notification-progress-value"
              :class="`is-${notif.type}`"
              x="0"
              y="0"
              width="100%"
              height="100%"
              rx="16"
              ry="16"
              pathLength="100"
              :style="getProgressStyle(notif)"
          />
        </svg>
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Roboto&display=swap');

* {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.notifications-container {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 5000;
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 420px;
}

.notification {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: flex-start;
  gap: 16px;
  min-width: 340px;
  position: relative;
  overflow: hidden;
}

.notification-enter-active {
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.notification-leave-active {
  transition: all 0.4s cubic-bezier(0.6, -0.28, 0.735, 0.045);
}

.notification-enter-from {
  transform: translateX(480px) scale(0.9);
  opacity: 0;
}

.notification-leave-to {
  transform: translateX(480px) scale(0.8);
  opacity: 0;
}

.notification-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  flex-shrink: 0;
  font-size: 24px;
  position: relative;
  animation: iconPulse 2s ease-in-out infinite;
  z-index: 2;
}

.notification-icon svg {
  width: 24px;
  height: 24px;
}

@keyframes iconPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.notification.success .notification-icon {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
}

.notification.info .notification-icon {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4);
}

.notification.warning .notification-icon {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
  box-shadow: 0 8px 20px rgba(245, 158, 11, 0.4);
}

.notification.error .notification-icon {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
  box-shadow: 0 8px 20px rgba(239, 68, 68, 0.4);
}

.notification-content {
  flex: 1;
  padding-top: 4px;
  z-index: 2;
}

.notification-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 6px;
  color: #1f2937;
  letter-spacing: -0.01em;
}

.notification-message {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.5;
}

.notification-close {
  background: rgba(107, 114, 128, 0.1);
  border: none;
  color: #6b7280;
  cursor: pointer;
  font-size: 20px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  transition: all 0.2s ease;
  flex-shrink: 0;
  z-index: 2;
}

.notification-close:hover {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  transform: rotate(90deg);
}

.notification-progress-ring {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
  pointer-events: none;
  z-index: 1;
}

.notification-progress-track,
.notification-progress-value {
  fill: none;
  stroke-width: 3;
  vector-effect: non-scaling-stroke;
}

.notification-progress-track {
  stroke: rgba(148, 163, 184, 0.22);
}

.notification-progress-value {
  stroke: #3b82f6;
  transition-property: stroke-dasharray;
  transition-timing-function: linear;
}

.notification-progress-value.is-success {
  stroke: #10b981;
}

.notification-progress-value.is-info {
  stroke: #3b82f6;
}

.notification-progress-value.is-warning {
  stroke: #f59e0b;
}

.notification-progress-value.is-error {
  stroke: #ef4444;
}

:global(html[data-theme='dark'] .notification) {
  background:
      radial-gradient(circle at 18% 0%, rgba(59, 130, 246, 0.16), transparent 36%),
      rgba(15, 23, 42, 0.96) !important;
  border: 1px solid rgba(51, 65, 85, 0.86) !important;
  box-shadow:
      0 24px 70px rgba(2, 6, 23, 0.54),
      inset 0 1px 0 rgba(148, 163, 184, 0.08) !important;
}

:global(html[data-theme='dark'] .notification-title) {
  color: #e2e8f0 !important;
}

:global(html[data-theme='dark'] .notification-message) {
  color: #94a3b8 !important;
}

:global(html[data-theme='dark'] .notification-close) {
  background: rgba(30, 41, 59, 0.86) !important;
  color: #94a3b8 !important;
}

:global(html[data-theme='dark'] .notification-close:hover) {
  background: rgba(248, 113, 113, 0.16) !important;
  color: #fca5a5 !important;
}

:global(html[data-theme='dark'] .notification-progress-track) {
  stroke: rgba(71, 85, 105, 0.64) !important;
}

@media (max-width: 768px) {
  .notifications-container {
    top: 16px;
    right: 16px;
    max-width: calc(100vw - 32px);
  }

  .notification {
    min-width: 300px;
  }

  .notification-enter-from,
  .notification-leave-to {
    transform: translateX(calc(100vw + 20px)) scale(0.9);
  }
}

@media (max-width: 480px) {
  .notification {
    min-width: 280px;
    padding: 16px;
  }

  .notification-icon {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }

  .notification-icon svg {
    width: 21px;
    height: 21px;
  }
}
</style>
