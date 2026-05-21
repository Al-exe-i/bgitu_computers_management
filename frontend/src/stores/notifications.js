import { defineStore } from 'pinia'

export const useNotificationsStore = defineStore('notifications', {
    state: () => ({
        notifications: [],
        nextId: 0,
        maxNotifications: 4,
    }),

    actions: {
        add({ text, type = 'info', timeout = 5000 })
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
    },
})