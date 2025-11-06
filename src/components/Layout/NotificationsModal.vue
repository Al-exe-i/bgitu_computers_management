<script>
import {useNotificationsStore} from "@/stores/notifications.js";

export default {
  name: "NotificationsModal",
  computed: {
    notificationsStore()
    {
      return useNotificationsStore()
    }
  },
  methods: {
    getIcon(type)
    {
      const icons = {
        'success': '✓',
        'info': 'ⓘ',
        'warning': '⚠',
        'error': '✗'
      };
      return icons[type] || 'ⓘ'
    },
    getTitle(type)
    {
      const titles = {
        'success': 'Успешно',
        'info': 'Информация',
        'warning': 'Внимание',
        'error': 'Ошибка'
      };
      return titles[type]
    },
    closeNotification(id)
    {
      this.notificationsStore.remove(id)
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
        <div class="notification-icon">{{ getIcon(notif.type) }}</div>
        <div class="notification-content">
          <div class="notification-title">{{ getTitle(notif.type) }}</div>
          <div class="notification-message">{{ notif.text }}</div>
        </div>
        <button class="notification-close" @click="closeNotification(notif.id)">✕</button>
        <div
            class="notification-progress"
            :style="{
            width: notif.progress + '%',
            transitionDuration: notif.duration + 'ms'
          }"
        ></div>
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Roboto&display=swap');
*{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.notifications-container {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 1000;
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
  box-shadow: 0 20px 60px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.1);
  display: flex;
  align-items: flex-start;
  gap: 16px;
  min-width: 340px;
  position: relative;
  overflow: hidden;
}

.notification::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, currentColor, transparent);
  opacity: 0.6;
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

.notification.success::before {
  color: #10b981;
}

.notification.info::before {
  color: #3b82f6;
}

.notification.warning::before {
  color: #f59e0b;
}

.notification.error::before {
  color: #ef4444;
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
}

.notification-close:hover {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  transform: rotate(90deg);
}

.notification-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: currentColor;
  opacity: 0.3;
  transition: width linear;
}

.notification.success .notification-progress {
  color: #10b981;
}

.notification.info .notification-progress {
  color: #3b82f6;
}

.notification.warning .notification-progress {
  color: #f59e0b;
}

.notification.error .notification-progress {
  color: #ef4444;
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

  .notification-enter-from, .notification-leave-to {
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
}
</style>