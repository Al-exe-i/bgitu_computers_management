import { defineStore } from 'pinia'

export const useNotificationsStore = defineStore('notifications', {
    state: () => ({
        notifications: [],
        nextId: 0,
        maxNotifications: 4,
    }),

    actions: {
        add({ text, title = null, type = 'info', timeout = 5000 })
        {
            // Удаляем самое старое уведомление, если их слишком много
            if (this.notifications.length >= this.maxNotifications)
            {
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
                if (notif)
                {
                    notif.progress = 0
                }
            }, 50)

            notification.progressTimerId = progressTimerId

            // Удаляем уведомление через timeout
            if (timeout > 0)
            {
                timerId = setTimeout(() => {
                    this.remove(id)
                }, timeout)
                notification.timerId = timerId
            }
        },

        remove(id)
        {
            const index = this.notifications.findIndex(n => n.id === id)
            if (index !== -1)
            {
                const notification = this.notifications[index]

                // Очищаем все таймеры
                if (notification.timerId)
                {
                    clearTimeout(notification.timerId)
                }
                if (notification.progressTimerId) {
                    clearTimeout(notification.progressTimerId)
                }

                this.notifications.splice(index, 1)
            }
        },

        removeOldest()
        {
            if (this.notifications.length > 0) {
                const oldest = this.notifications[0]
                this.remove(oldest.id)
            }
        },

        clearAll()
        {
            this.notifications.forEach(n => {
                if (n.timerId) clearTimeout(n.timerId)
                if (n.progressTimerId) clearTimeout(n.progressTimerId)
            })
            this.notifications = []
        },

        success(text, timeout = 5000)
        {
            this.add({ text, type: 'success', timeout })
        },

        info(text, timeout = 5000)
        {
            this.add({ text, type: 'info', timeout })
        },

        error(text, timeout = 5000)
        {
            this.add({ text, type: 'error', timeout })
        },

        warning(text, timeout = 5000)
        {
            this.add({ text, type: 'warning', timeout })
        },

        realtime(notification, timeout = 7000)
        {
            const eventType = notification?.event_type;
            const title = notification?.title || null;
            const text = notification?.message || '\u041f\u043e\u043b\u0443\u0447\u0435\u043d\u043e \u043d\u043e\u0432\u043e\u0435 \u0443\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u0435';
            const typeByEvent = {
                audience_changed: 'info',
                hardware_fault: 'warning',
                hardware_recovered: 'success',
                auth_security: 'warning',
            };

            this.add({
                title,
                text,
                type: typeByEvent[eventType] || 'info',
                timeout,
            });
        },
    },
})
