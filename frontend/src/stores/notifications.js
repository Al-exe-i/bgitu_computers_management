import { defineStore } from 'pinia'

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

        clearRealtimeHistory()
        {
            this.realtimeHistory = []
            this.unreadCount = 0
        },

        markAllRealtimeRead()
        {
            this.unreadCount = 0
            this.realtimeHistory = this.realtimeHistory.map(notification => ({
                ...notification,
                read: true,
            }))
        },

        toggleSound()
        {
            this.soundEnabled = !this.soundEnabled

            if (typeof window !== 'undefined') {
                window.localStorage.setItem(
                    'bgitu-notification-sound',
                    this.soundEnabled ? 'on' : 'off'
                )
            }
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

        addRealtimeHistoryItem({ title, text, type, eventType, payload })
        {
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

        getRealtimeFallbackTitle(type)
        {
            const titles = {
                success: 'Восстановление',
                info: 'Информация',
                warning: 'Внимание',
                error: 'Ошибка',
            }

            return titles[type] || 'Уведомление'
        },

        async playRealtimeSound(type = 'info')
        {
            if (!this.soundEnabled || typeof window === 'undefined') return

            const AudioContext = window.AudioContext || window.webkitAudioContext
            if (!AudioContext) return

            try {
                const context = new AudioContext()
                if (context.state === 'suspended') {
                    await context.resume()
                }

                const now = context.currentTime
                const baseFrequency = {
                    success: 660,
                    info: 520,
                    warning: 440,
                    error: 330,
                }[type] || 520

                const gain = context.createGain()
                gain.gain.setValueAtTime(0.0001, now)
                gain.gain.exponentialRampToValueAtTime(0.075, now + 0.025)
                gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.42)
                gain.connect(context.destination)

                const first = context.createOscillator()
                const second = context.createOscillator()

                first.type = 'sine'
                second.type = 'triangle'
                first.frequency.setValueAtTime(baseFrequency, now)
                first.frequency.exponentialRampToValueAtTime(baseFrequency * 1.18, now + 0.18)
                second.frequency.setValueAtTime(baseFrequency * 1.5, now + 0.03)
                second.frequency.exponentialRampToValueAtTime(baseFrequency * 1.72, now + 0.24)

                first.connect(gain)
                second.connect(gain)
                first.start(now)
                second.start(now + 0.035)
                first.stop(now + 0.36)
                second.stop(now + 0.42)

                window.setTimeout(() => context.close().catch(() => {}), 520)
            } catch (error) {
                // Браузер может запретить звук до первого действия пользователя.
            }
        },
    },
})
