import { defineStore } from 'pinia'
import notificationSound from '@/assets/sounds/ding.mp3'

const NOTIFICATION_SOUNDS = {
    info: notificationSound,
    success: notificationSound,
    warning: notificationSound,
    error: notificationSound,
}

const NOTIFICATION_SOUND_VOLUME = 0.45

export const useNotificationsStore = defineStore('notifications', {
    state: () => ({
        notifications: [],
        realtimeHistory: [],
        nextId: 0,
        nextHistoryId: 0,
        maxNotifications: 4,
        maxHistory: 30,
        unreadCount: 0,
        soundEnabled: typeof window !== 'undefined'
            ? window.localStorage.getItem('bgitu-notification-sound') !== 'off'
            : true,
    }),

    actions: {
        add({ text, title = null, type = 'info', timeout = 5000 }) {
            // Удаляем самое старое уведомление, если их слишком много
            if (this.notifications.length >= this.maxNotifications) {
                this.removeOldest()
            }

            const id = this.nextId++
            let timerId = null
            let progressTimerId = null

            const notification = {
                id,
                title,
                text,
                type,
                timerId,
                progressTimerId,
                progress: 100,
                duration: timeout
            }

            this.notifications.push(notification)

            // Запускаем анимацию progress bar
            progressTimerId = setTimeout(() => {
                const notif = this.notifications.find(n => n.id === id)
                if (notif) {
                    notif.progress = 0
                }
            }, 50)

            notification.progressTimerId = progressTimerId

            // Удаляем уведомление через timeout
            if (timeout > 0) {
                timerId = setTimeout(() => {
                    this.remove(id)
                }, timeout)
                notification.timerId = timerId
            }
        },

        remove(id) {
            const index = this.notifications.findIndex(n => n.id === id)
            if (index !== -1) {
                const notification = this.notifications[index]

                // Очищаем все таймеры
                if (notification.timerId) {
                    clearTimeout(notification.timerId)
                }
                if (notification.progressTimerId) {
                    clearTimeout(notification.progressTimerId)
                }

                this.notifications.splice(index, 1)
            }
        },

        removeOldest() {
            if (this.notifications.length > 0) {
                const oldest = this.notifications[0]
                this.remove(oldest.id)
            }
        },

        clearAll() {
            this.notifications.forEach(n => {
                if (n.timerId) clearTimeout(n.timerId)
                if (n.progressTimerId) clearTimeout(n.progressTimerId)
            })
            this.notifications = []
        },

        clearRealtimeHistory() {
            this.realtimeHistory = []
            this.unreadCount = 0
        },

        markAllRealtimeRead() {
            this.unreadCount = 0
            this.realtimeHistory = this.realtimeHistory.map(notification => ({
                ...notification,
                read: true,
            }))
        },

        toggleSound() {
            this.soundEnabled = !this.soundEnabled

            if (typeof window !== 'undefined') {
                window.localStorage.setItem(
                    'bgitu-notification-sound',
                    this.soundEnabled ? 'on' : 'off'
                )
            }
        },

        success(text, timeout = 5000) {
            this.add({ text, type: 'success', timeout })
        },

        info(text, timeout = 5000) {
            this.add({ text, type: 'info', timeout })
        },

        error(text, timeout = 5000) {
            this.add({ text, type: 'error', timeout })
        },

        warning(text, timeout = 5000) {
            this.add({ text, type: 'warning', timeout })
        },

        realtime(notification, timeout = 7000) {
            const eventType = notification?.event_type;
            const title = notification?.title || null;
            const text = notification?.message || 'Получено новое уведомление';
            const typeByEvent = {
                audience_changed: 'info',
                hardware_fault: 'warning',
                hardware_recovered: 'success',
                auth_security: 'warning',
            };
            const type = typeByEvent[eventType] || 'info';

            this.addRealtimeHistoryItem({
                title,
                text,
                type,
                eventType,
                payload: notification,
            });

            this.playRealtimeSound(type);

            this.add({
                title,
                text,
                type,
                timeout,
            });
        },

        addRealtimeHistoryItem({ title, text, type, eventType, payload }) {
            const historyItem = {
                id: payload?.notification_id || `local-${this.nextHistoryId++}`,
                title: title || this.getRealtimeFallbackTitle(type),
                text,
                type,
                eventType,
                payload: payload || {},
                receivedAt: new Date().toISOString(),
                read: false,
            }

            this.realtimeHistory = [
                historyItem,
                ...this.realtimeHistory.filter(item => item.id !== historyItem.id),
            ].slice(0, this.maxHistory)
            this.unreadCount = Math.min(this.unreadCount + 1, this.maxHistory)
        },

        getRealtimeFallbackTitle(type) {
            const titles = {
                success: 'Восстановление',
                info: 'Информация',
                warning: 'Внимание',
                error: 'Ошибка',
            }

            return titles[type] || 'Уведомление'
        },

        async playRealtimeSound(type = 'info') {
            if (!this.soundEnabled || typeof window === 'undefined') return

            const soundUrl = NOTIFICATION_SOUNDS[type] || NOTIFICATION_SOUNDS.info

            try {
                const audio = new Audio(soundUrl)
                audio.volume = NOTIFICATION_SOUND_VOLUME
                audio.preload = 'auto'
                await audio.play()
            } catch (error) {
                // Браузер может запретить звук до первого действия пользователя.
            }
        },
    },
})
