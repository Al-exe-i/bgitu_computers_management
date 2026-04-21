<script>
import api from "@/services/api";
import { useNotificationsStore } from "@/stores/notifications";
import {useAuthStore} from "@/stores/auth.js";

export default {
  name: "SecuritySettings",

  data() {
    return {
      activeTab: 'password', // 'password' или 'sessions'

      // состояние загрузки
      loadingPassword: false,
      loadingSessions: false,
      loadingAction: false, // Для кнопок выхода

      form: {
        current_password: '',
        new_password: '',
        confirm_password: ''
      },
      showPassword: {
        current: false,
        new: false,
        confirm: false
      },

      // Данные сессий с API
      sessions: [],
      showSessionConfirmModal: false,
      pendingSessionAction: null
    };
  },

  computed: {
    notify() {
      return useNotificationsStore();
    },

    passwordsMatch() {
      return this.form.new_password === this.form.confirm_password;
    },

    isFormValid() {
      return (
          this.form.current_password.length > 0 &&
          this.form.new_password.length >= 4 &&
          this.passwordsMatch
      );
    },

    passwordStrength() {
      const pwd = this.form.new_password || '';

      if (!pwd) {
        return {
          score: 0,
          percent: 0,
          level: 'empty',
          label: 'Введите пароль'
        };
      }

      let score = 0;

      // Баллы за длину (ключевой фактор надежности)
      if (pwd.length >= 8) score += 1;
      if (pwd.length >= 12) score += 1; // Бонус за большую длину
      if (pwd.length >= 16) score += 1; // Супер-пароль

      // Баллы за разнообразие символов
      if (/[a-z]/.test(pwd)) score += 1;
      if (/[A-Z]/.test(pwd)) score += 1;
      if (/\d/.test(pwd)) score += 1;
      if (/[^\w\s]/.test(pwd)) score += 1; // Спецсимволы

      // Ограничение для коротких паролей (Hard Cap)
      // Пароль меньше 6 символов — всегда "Очень слабый", независимо от набора символов.
      if (pwd.length < 6) {
        score = Math.min(score, 1);
      }
      // Пароль от 6 до 8 символов может быть максимум "Слабый" (score 2)
      else if (pwd.length < 8) {
        score = Math.min(score, 2);
      }

      // Максимально возможный score теперь = 6 (3 за длину + 3 за символы, но 4 за символы возможны, если длина мала, но мы ограничили это выше)
      // Реальный максимум для расчета процентов возьмем 5 или 6.
      const percent = Math.min((score / 6) * 100, 100);

      if (score <= 1) return { score, percent, level: 'weak', label: 'Очень слабый' };
      if (score === 2) return { score, percent, level: 'fair', label: 'Слабый' };
      if (score === 3) return { score, percent, level: 'medium', label: 'Средний' };
      if (score === 4) return { score, percent, level: 'good', label: 'Надежный' };

      return { score, percent, level: 'strong', label: 'Сильный' };
    },
    // Отображаем только активные сессии, сортируя так, чтобы текущая была первой
    activeSessions() {
      return this.sessions
          .filter(s => s.is_active)
          .sort((a, b) => (b.is_current ? 1 : 0) - (a.is_current ? 1 : 0));
    },

    authStore() {
      return useAuthStore();
    },

    sectionTitle() {
      return this.activeTab === 'password' ? 'Изменение пароля' : 'Управление сессиями'
    },

    sectionSubTitle() {
      return this.activeTab === 'password' ? 'Измените пароль учётной записи' : 'Управляйте активными сессиями вашей учётной записи'
    },

    sessionConfirmTitle() {
      if (!this.pendingSessionAction) return '';
      return this.pendingSessionAction.type === 'all'
          ? 'Завершить все сеансы'
          : 'Завершить сеанс';
    },

    sessionConfirmDescription() {
      if (!this.pendingSessionAction) return '';

      if (this.pendingSessionAction.type === 'all') {
        return 'Будет выполнен выход на всех устройствах, включая текущее. Для продолжения потребуется снова войти в систему.';
      }

      return 'Сеанс будет немедленно завершён на выбранном устройстве. Если он ещё активен, доступ к аккаунту будет потерян.';
    },

    sessionConfirmActionLabel() {
      if (!this.pendingSessionAction) return 'Подтвердить';
      return this.pendingSessionAction.type === 'all'
          ? 'Завершить все'
          : 'Завершить сеанс';
    },

    sessionConfirmMetaRows() {
      if (!this.pendingSessionAction) return [];

      if (this.pendingSessionAction.type === 'all') {
        return [
          {
            label: 'Активные устройства',
            value: `${this.activeSessions.length}`
          },
          {
            label: 'Дополнительно',
            value: 'Текущий вход тоже будет завершён'
          }
        ];
      }

      const session = this.pendingSessionAction.session;

      return [
        {
          label: 'Устройство',
          value: this.parseUserAgent(session.user_agent).device
        },
        {
          label: 'IP',
          value: session.ip || 'Неизвестно'
        },
        {
          label: 'Начат',
          value: this.formatDate(session.created_at)
        }
      ];
    }
  },

  watch: {
    // Автоматически загружаем сессии при переходе на вкладку
    activeTab(newTab) {
      if (newTab === 'sessions' && this.sessions.length === 0) {
        this.fetchSessions();
      }
    }
  },

  methods: {
    togglePasswordVisibility(field) {
      this.showPassword[field] = !this.showPassword[field];
    },

    // Управление паролем
    async handleChangePassword() {
      if (!this.isFormValid) return;
      this.loadingPassword = true;

      try {
        await api.post('/users/me/password', {
          current_password: this.form.current_password,
          new_password: this.form.new_password
        });

        this.notify.success('Пароль успешно изменен');

        this.form.current_password = '';
        this.form.new_password = '';
        this.form.confirm_password = '';
        this.showPassword = { current: false, new: false, confirm: false };

      } catch (error) {
        const msg = error.response?.data?.detail || 'Не удалось изменить пароль';
        this.notify.error(msg);
      } finally {
        this.loadingPassword = false;
      }
    },

    // Управление сессиями
    async fetchSessions() {
      this.loadingSessions = true;
      try {
        const res = await api.get('/sessions');
        this.sessions = res.data;
      } catch (error) {
        const msg = error.response?.data?.detail || 'Не удалось загрузить список сессий';
        this.notify.error(msg);
      } finally {
        this.loadingSessions = false;
      }
    },

    requestLogoutSession(session) {
      if (this.loadingAction || !session?.sid) return;

      this.pendingSessionAction = {
        type: 'single',
        sid: session.sid,
        session
      };
      this.showSessionConfirmModal = true;
    },

    requestLogoutAll() {
      if (this.loadingAction || this.activeSessions.length <= 1) return;

      this.pendingSessionAction = {
        type: 'all'
      };
      this.showSessionConfirmModal = true;
    },

    closeSessionConfirmModal({ force = false } = {}) {
      if (this.loadingAction && !force) return;

      this.showSessionConfirmModal = false;
      this.pendingSessionAction = null;
    },

    async confirmSessionAction() {
      if (!this.pendingSessionAction) return;

      const actionType = this.pendingSessionAction.type;
      const sessionSid = this.pendingSessionAction.sid;
      let shouldCloseModal = false;

      this.loadingAction = true;

      try {
        if (actionType === 'all') {
          shouldCloseModal = true;
          await this.authStore.logout(true);
          return;
        }

        await api.delete(`/sessions/${sessionSid}`);
        this.notify.success('Сеанс успешно завершен');
        this.sessions = this.sessions.filter(s => s.sid !== sessionSid);
        shouldCloseModal = true;
      } catch (error) {
        const msg = actionType === 'all'
            ? error.response?.data?.detail || 'Ошибка при выходе из устройств'
            : error.response?.data?.detail || 'Ошибка при завершении сеанса';
        this.notify.error(msg);
      } finally {
        this.loadingAction = false;

        if (shouldCloseModal) {
          this.closeSessionConfirmModal({ force: true });
        }
      }
    },

    switchTab(tabName) {
      this.activeTab = tabName;
    },

    // Утилиты форматирования
    formatDate(dateString) {
      if (!dateString) return '—';
      const d = new Date(dateString);
      return new Intl.DateTimeFormat('ru-RU', {
        day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
      }).format(d);
    },

    parseUserAgent(uaString) {
      if (!uaString) return { device: 'Неизвестное устройство', type: 'desktop' };

      const ua = uaString.toLowerCase();
      let type = 'desktop';
      let browser = 'Неизвестный браузер';
      let os = 'неизвестной ОС';

      // Определение типа устройства
      if (/mobile|android|iphone|ipad|phone/i.test(ua)) type = 'mobile';

      // Браузер
      if (ua.includes('firefox')) browser = 'Firefox';
      else if (ua.includes('edg')) browser = 'Edge';
      else if (ua.includes('opr') || ua.includes('opera')) browser = 'Opera';
      else if (ua.includes('chrome')) browser = 'Chrome';
      else if (ua.includes('safari')) browser = 'Safari';

      // ОС
      if (ua.includes('win')) os = 'Windows';
      else if (ua.includes('mac')) os = 'macOS';
      else if (ua.includes('android')) os = 'Android';
      else if (ua.includes('iphone') || ua.includes('ipad')) os = 'iOS';
      else if (ua.includes('linux')) os = 'Linux';

      return { device: `${browser} на ${os}`, type };
    }
  }
};
</script>

<template>
  <div class="security-settings-root">
    <div class="security-card security-settings-card">
      <div class="card-header">
        <h2 class="section-title">{{ sectionTitle }}</h2>
        <p class="section-subtitle">{{ sectionSubTitle }}</p>
      </div>

      <!-- Вкладки навигации -->
          <div class="tabs-container">
        <div class="icon-tabs security-tabs" role="tablist" aria-label="Разделы безопасности">
          <button
              type="button"
              class="icon-tab security-tab"
              :class="{ active: activeTab === 'password' }"
              role="tab"
              :aria-selected="activeTab === 'password'"
              title="Смена пароля"
              @click="switchTab('password')"
          >
            <span class="tab-icon-wrapper">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
              </svg>
            </span>
            <span class="security-tab-label">Смена пароля</span>
          </button>
          <button
              type="button"
              class="icon-tab security-tab"
              :class="{ active: activeTab === 'sessions' }"
              role="tab"
              :aria-selected="activeTab === 'sessions'"
              title="Активные сессии"
              @click="switchTab('sessions')"
          >
            <span class="tab-icon-wrapper">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                <line x1="8" y1="21" x2="16" y2="21"></line>
                <line x1="12" y1="17" x2="12" y2="21"></line>
              </svg>
            </span>
            <span class="security-tab-label">Активные сессии</span>
          </button>
        </div>
      </div>

      <!-- Вкладка 1 смена пароля -->
      <transition name="fade" mode="out-in">
        <div v-if="activeTab === 'password'" class="tab-content" key="password">
          <div class="alert-box warning">
            <svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
            <div class="alert-text">
              Рекомендуем использовать сложный пароль, содержащий буквы, цифры и спецсимволы.
            </div>
          </div>

          <form @submit.prevent="handleChangePassword" class="password-form">
            <div class="form-group">
              <label>Текущий пароль</label>
              <div class="input-wrapper">
                <input
                    :type="showPassword.current ? 'text' : 'password'"
                    v-model="form.current_password"
                    class="form-input"
                    required
                    placeholder="Введите текущий пароль"
                >
                <button type="button" class="eye-btn" @click="togglePasswordVisibility('current')">
                  <svg v-if="!showPassword.current" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
                </button>
              </div>
            </div>

          <div class="form-group">
            <label>Новый пароль</label>
            <div class="input-wrapper">
              <input
                  :type="showPassword.new ? 'text' : 'password'"
                  v-model="form.new_password"
                  class="form-input"
                  required
                  placeholder="Минимум 6 символов"
                  minlength="6"
              >
              <button type="button" class="eye-btn" @click="togglePasswordVisibility('new')">
                <svg v-if="!showPassword.new" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
              </button>
            </div>
            <div v-if="form.new_password" class="password-strength" :class="`is-${passwordStrength.level}`">
              <div class="password-strength-head">
                <span class="password-strength-title">Сложность пароля</span>
                <span class="password-strength-label">{{ passwordStrength.label }}</span>
              </div>
              <div class="password-strength-track">
                <div class="password-strength-fill" :style="{ width: `${passwordStrength.percent}%` }"></div>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label>Подтвердите новый пароль</label>
            <div class="input-wrapper">
              <input
                  :type="showPassword.confirm ? 'text' : 'password'"
                  v-model="form.confirm_password"
                  class="form-input"
                  :class="{ 'error': !passwordsMatch && form.confirm_password }"
                  required
                  placeholder="Повторите пароль"
              >
              <button type="button" class="eye-btn" @click="togglePasswordVisibility('confirm')">
                <svg v-if="!showPassword.confirm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
              </button>
            </div>
            <span v-if="!passwordsMatch && form.confirm_password" class="error-text">
              Пароли не совпадают
            </span>
          </div>

            <button type="submit" class="btn btn-primary" :disabled="loadingPassword || !isFormValid">
              <span v-if="loadingPassword" class="spinner"></span>
              {{ loadingPassword ? 'Обновление...' : 'Обновить пароль' }}
            </button>
          </form>
        </div>

        <!-- Вкладка 2: управление сессиями -->
        <div v-else-if="activeTab === 'sessions'" class="tab-content" key="sessions">

        <div v-if="loadingSessions" class="loading-state">
          <div class="spinner-large"></div>
          <p>Загрузка списка устройств...</p>
        </div>

        <template v-else>
          <div class="alert-box info">
            <svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
            <div class="alert-text">
              Здесь отображаются устройства, с которых в данный момент выполнен вход в ваш аккаунт.
            </div>
          </div>

          <div class="sessions-toolbar">
            <div class="sessions-stat-chip">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                <line x1="8" y1="21" x2="16" y2="21"></line>
                <line x1="12" y1="17" x2="12" y2="21"></line>
              </svg>
              <span>{{ activeSessions.length }} активных</span>
            </div>
            <div v-if="activeSessions.length > 1" class="sessions-stat-chip muted">
              <svg xmlns="http://www.w3.org/2000/svg" width="320" height="512" viewBox="0 0 320 512"><path fill="currentColor" d="M143 256.3L7 120.3c-9.4-9.4-9.4-24.6 0-33.9l22.6-22.6c9.4-9.4 24.6-9.4 33.9 0l96.4 96.4l96.4-96.4c9.4-9.4 24.6-9.4 33.9 0L313 86.3c9.4 9.4 9.4 24.6 0 33.9l-136 136c-9.4 9.5-24.6 9.5-34 .1m34 192l136-136c9.4-9.4 9.4-24.6 0-33.9l-22.6-22.6c-9.4-9.4-24.6-9.4-33.9 0L160 352.1l-96.4-96.4c-9.4-9.4-24.6-9.4-33.9 0L7 278.3c-9.4 9.4-9.4 24.6 0 33.9l136 136c9.4 9.5 24.6 9.5 34 .1"/></svg>
              <span>{{ activeSessions.length - 1 }} можно завершить</span>
            </div>
          </div>

          <div v-if="activeSessions.length" class="sessions-list">
            <div v-for="session in activeSessions" :key="session.sid" class="session-item" :class="{ 'is-current': session.is_current }">

              <div class="session-icon">
                <svg v-if="parseUserAgent(session.user_agent).type === 'desktop'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect><line x1="12" y1="18" x2="12.01" y2="18"></line></svg>
              </div>

              <div class="session-info">
                <div class="session-device">
                  {{ parseUserAgent(session.user_agent).device }}
                  <span v-if="session.is_current" class="badge-current">Текущий сеанс</span>
                </div>
                <div class="session-details">
                  <span>IP: {{ session.ip || 'Неизвестно' }}</span>
                  <span class="dot-separator">•</span>
                  <span>Начат: {{ formatDate(session.created_at) }}</span>
                </div>
              </div>

              <button
                  v-if="!session.is_current"
                  class="logout-link"
                  @click="requestLogoutSession(session)"
                  :disabled="loadingAction"
                  title="Завершить этот сеанс"
              >
                Завершить
              </button>
            </div>
          </div>

          <div v-else class="sessions-empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
              <path d="M8 21h8"></path>
              <path d="M12 17v4"></path>
            </svg>
            <div>
              <strong>Активные сеансы не найдены</strong>
              <span>Список обновится после следующего входа в систему.</span>
            </div>
          </div>

          <div class="actions-footer">
            <button class="btn btn-danger session-danger-btn" @click="requestLogoutAll" :disabled="loadingAction || activeSessions.length <= 1">
              <span v-if="loadingAction" class="spinner"></span>
              {{ loadingAction ? 'Обработка...' : 'Завершить все сеансы' }}
            </button>
          </div>
        </template>
        </div>
      </transition>
    </div>

    <Teleport to="body">
      <transition name="fade">
        <div
            v-if="showSessionConfirmModal"
            class="session-confirm-overlay"
            @click.self="closeSessionConfirmModal"
        >
          <div class="session-confirm-card" role="dialog" aria-modal="true" :aria-label="sessionConfirmTitle">
            <button
                type="button"
                class="session-confirm-close"
                @click="closeSessionConfirmModal"
                :disabled="loadingAction"
                aria-label="Закрыть окно подтверждения"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" d="M6 6l12 12M18 6L6 18"/>
              </svg>
            </button>

          <div class="session-confirm-icon">
            <svg v-if="pendingSessionAction?.type === 'all'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="4" width="18" height="12" rx="2"></rect>
              <path d="M7 20h10"></path>
              <path d="M12 16v4"></path>
              <path d="M16 10l3 3l-3 3"></path>
              <path d="M10 16H7a2 2 0 0 1-2-2V9"></path>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="4" width="18" height="12" rx="2"></rect>
              <path d="M7 20h10"></path>
              <path d="M12 16v4"></path>
              <path d="M14 10l3 3l-3 3"></path>
              <path d="M11 13H6"></path>
            </svg>
          </div>

          <div class="session-confirm-body">
            <h3 class="session-confirm-title">{{ sessionConfirmTitle }}</h3>
            <p class="session-confirm-text">{{ sessionConfirmDescription }}</p>

            <div class="session-confirm-meta">
              <div
                  v-for="row in sessionConfirmMetaRows"
                  :key="row.label"
                  class="session-confirm-meta-item"
              >
                <span class="session-confirm-meta-label">{{ row.label }}</span>
                <strong class="session-confirm-meta-value">{{ row.value }}</strong>
              </div>
            </div>
          </div>

            <div class="session-confirm-actions">
              <button
                  type="button"
                  class="session-confirm-btn is-cancel"
                  @click="closeSessionConfirmModal"
                  :disabled="loadingAction"
              >
                Отмена
              </button>
              <button
                  type="button"
                  class="session-confirm-btn is-danger"
                  @click="confirmSessionAction"
                  :disabled="loadingAction"
              >
                <span v-if="loadingAction" class="spinner"></span>
                {{ loadingAction ? 'Обработка...' : sessionConfirmActionLabel }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<style scoped>
.security-settings-root {
  width: 100%;
}

.security-settings-card {
  --security-card-bg: #ffffff;
  --security-card-border: rgba(226, 232, 240, 0.9);
  --security-shadow:
      0 28px 60px rgba(15, 23, 42, 0.06),
      0 6px 18px rgba(15, 23, 42, 0.04);
  --security-soft-surface: #f8fafc;
  --security-soft-border: #e2e8f0;
  --security-chip-bg: rgba(241, 245, 249, 0.95);
  --security-chip-text: #475569;
  --security-tab-bg: #f1f5f9;
  --security-tab-hover: #e2e8f0;
  --security-tab-active: #ffffff;
  --security-tab-active-text: #2563eb;
  --security-session-bg:
      radial-gradient(circle at top right, rgba(59, 130, 246, 0.08), transparent 32%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.98));
  --security-session-border: rgba(226, 232, 240, 0.92);
  --security-session-hover-border: #cbd5e1;
  --security-session-current-bg:
      radial-gradient(circle at top right, rgba(34, 197, 94, 0.12), transparent 32%),
      linear-gradient(180deg, rgba(240, 253, 244, 0.98), rgba(236, 253, 245, 0.98));
  --security-session-current-border: rgba(134, 239, 172, 0.7);
  --security-session-icon-bg: #eff6ff;
  --security-session-icon-color: #2563eb;
  --security-session-current-icon-bg: #dcfce7;
  --security-session-current-icon-color: #16a34a;
  --security-danger-soft-bg: #fff1f2;
  --security-danger-soft-border: #fecdd3;
  --security-danger-soft-text: #be123c;
  --security-overlay: rgba(15, 23, 42, 0.34);
  --security-modal-bg:
      radial-gradient(circle at top right, rgba(59, 130, 246, 0.14), transparent 34%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.98));
  --security-modal-border: rgba(226, 232, 240, 0.94);
  --security-modal-shadow:
      0 32px 72px rgba(15, 23, 42, 0.18),
      0 12px 24px rgba(15, 23, 42, 0.08);
  --security-modal-icon-bg: linear-gradient(135deg, rgba(239, 68, 68, 0.14), rgba(249, 115, 22, 0.12));
  --security-modal-icon-color: #b91c1c;
}

.security-card {
  background: var(--security-card-bg);
  padding: 32px;
  border-radius: 16px;
  border: 1px solid var(--security-card-border);
  box-shadow: var(--security-shadow);
  width: 100%;
  box-sizing: border-box;
  font-family: system-ui, -apple-system, sans-serif;
  color: #0f172a;
}

.card-header {
  margin-bottom: 24px;
}

.section-title {
  margin: 0 0 6px 0;
  font-size: 20px;
  font-weight: 600;
}

.section-subtitle {
  margin: 0;
  font-size: 14px;
  color: #64748b;
}

.tabs-container {
  margin-bottom: 28px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.security-tabs {
  display: inline-flex;
  gap: 8px;
  background: var(--security-tab-bg);
  border: 1px solid var(--security-soft-border);
  padding: 4px;
  border-radius: 10px;
}

.security-tab {
  background: transparent;
  border: none;
  padding: 0 14px;
  min-height: 40px;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.security-tab .tab-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.security-tab .tab-icon-wrapper :deep(svg) {
  width: 18px;
  height: 18px;
  display: block;
}

.security-tab:hover:not(.active) {
  background: var(--security-tab-hover);
  color: #334155;
}

.security-tab.active {
  background: var(--security-tab-active);
  color: var(--security-tab-active-text);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.security-tab:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.35);
}

.alert-box {
  display: flex;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 10px;
  margin-bottom: 24px;
  font-size: 14px;
  line-height: 1.5;
  align-items: flex-start;
}

.alert-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  margin-top: 1px;
}

.alert-box.warning {
  background: #fffbeb;
  border: 1px solid #fef3c7;
  color: #b45309;
}

.alert-box.info {
  background: #f0f9ff;
  border: 1px solid #e0f2fe;
  color: #0369a1;
}

.password-form {
  display: grid;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.form-input {
  width: 100%;
  padding: 10px 40px 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  color: #0f172a;
  background: #ffffff;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.form-input::placeholder {
  color: #94a3b8;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.form-input.error {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15);
}

.error-text {
  font-size: 12px;
  color: #ef4444;
  margin-top: 2px;
}

.password-strength {
  margin-top: 10px;
}

.password-strength-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}

.password-strength-title,
.password-strength-label {
  font-size: 12px;
  font-weight: 600;
}

.password-strength-title {
  color: #64748b;
}

.password-strength-label {
  color: #64748b;
}

.password-strength-track {
  width: 100%;
  height: 8px;
  border-radius: 999px;
  background: #e2e8f0;
  overflow: hidden;
}

.password-strength-fill {
  height: 100%;
  width: 0;
  border-radius: inherit;
  background: #94a3b8;
  transition: width 0.25s ease, background-color 0.25s ease;
}

.password-strength.is-weak .password-strength-fill {
  background: #ef4444;
}

.password-strength.is-weak .password-strength-label {
  color: #b91c1c;
}

.password-strength.is-fair .password-strength-fill {
  background: #f97316;
}

.password-strength.is-fair .password-strength-label {
  color: #c2410c;
}

.password-strength.is-medium .password-strength-fill {
  background: #f59e0b;
}

.password-strength.is-medium .password-strength-label {
  color: #b45309;
}

.password-strength.is-good .password-strength-fill {
  background: #3b82f6;
}

.password-strength.is-good .password-strength-label {
  color: #1d4ed8;
}

.password-strength.is-strong .password-strength-fill {
  background: #22c55e;
}

.password-strength.is-strong .password-strength-label {
  color: #15803d;
}

.eye-btn {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  padding: 0;
  color: #94a3b8;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: color 0.2s;
}

.eye-btn:hover {
  color: #475569;
}

.eye-btn svg {
  width: 18px;
  height: 18px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  width: fit-content;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #94a3b8;
  cursor: not-allowed;
  opacity: 0.8;
}

.btn-danger {
  background: #fee2e2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.btn-danger:hover:not(:disabled) {
  background: #fecaca;
}

.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sessions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.sessions-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 18px;
}

.sessions-stat-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 999px;
  background: var(--security-chip-bg);
  border: 1px solid var(--security-soft-border);
  color: var(--security-chip-text);
  font-size: 12px;
  font-weight: 600;
}

.sessions-stat-chip svg {
  width: 15px;
  height: 15px;
}

.sessions-stat-chip.muted {
  color: #64748b;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border: 1px solid var(--security-session-border);
  border-radius: 16px;
  background: var(--security-session-bg);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.04);
  transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}

.session-item:hover {
  border-color: var(--security-session-hover-border);
  transform: translateY(-1px);
  box-shadow: 0 18px 28px rgba(15, 23, 42, 0.08);
}

.session-item.is-current {
  border-color: var(--security-session-current-border);
  background: var(--security-session-current-bg);
}

.session-icon {
  width: 40px;
  height: 40px;
  background: var(--security-session-icon-bg);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--security-session-icon-color);
  margin-right: 16px;
  flex-shrink: 0;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.55);
}

.session-item.is-current .session-icon {
  background: var(--security-session-current-icon-bg);
  color: var(--security-session-current-icon-color);
}

.session-icon svg {
  width: 20px;
  height: 20px;
}

.session-info {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.session-device {
  font-weight: 600;
  font-size: 14px;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.session-details {
  font-size: 12px;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 6px;
}

.dot-separator {
  font-size: 10px;
  color: #cbd5e1;
}

.badge-current {
  background: linear-gradient(135deg, #16a34a, #22c55e);
  color: #ffffff;
  font-size: 11px;
  padding: 3px 9px;
  border-radius: 999px;
  font-weight: 600;
  box-shadow: 0 10px 18px rgba(22, 163, 74, 0.18);
}

.logout-link {
  background: var(--security-danger-soft-bg);
  border: 1px solid var(--security-danger-soft-border);
  color: var(--security-danger-soft-text);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 10px 14px;
  border-radius: 999px;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.logout-link:hover:not(:disabled) {
  background: #ffe4e6;
  border-color: #fda4af;
  color: #9f1239;
}

.logout-link:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sessions-empty-state {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  margin-bottom: 24px;
  border-radius: 16px;
  border: 1px dashed var(--security-soft-border);
  background: var(--security-soft-surface);
  color: #64748b;
}

.sessions-empty-state svg {
  width: 22px;
  height: 22px;
  color: #94a3b8;
  flex-shrink: 0;
}

.sessions-empty-state div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sessions-empty-state strong {
  color: #0f172a;
  font-size: 14px;
}

.sessions-empty-state span {
  font-size: 13px;
}

.actions-footer {
  border-top: 1px solid #e2e8f0;
  padding-top: 24px;
}

.session-danger-btn {
  background: linear-gradient(135deg, #fee2e2, #ffe4e6);
  border: 1px solid #fecaca;
  color: #b91c1c;
  box-shadow: 0 12px 26px rgba(248, 113, 113, 0.12);
}

.session-danger-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #fecaca, #fda4af);
  border-color: #fca5a5;
}

.session-confirm-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.34);
  backdrop-filter: blur(10px);
}

.session-confirm-card {
  position: relative;
  width: min(100%, 520px);
  padding: 28px;
  border-radius: 24px;
  border: 1px solid rgba(226, 232, 240, 0.94);
  background:
      radial-gradient(circle at top right, rgba(59, 130, 246, 0.14), transparent 34%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.98));
  box-shadow:
      0 32px 72px rgba(15, 23, 42, 0.18),
      0 12px 24px rgba(15, 23, 42, 0.08);
  color: #0f172a;
}

.session-confirm-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 1px solid #e2e8f0;
  background: rgba(255, 255, 255, 0.7);
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.session-confirm-close:hover:not(:disabled) {
  background: #ffffff;
  color: #0f172a;
}

.session-confirm-close svg {
  width: 16px;
  height: 16px;
}

.session-confirm-icon {
  width: 58px;
  height: 58px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.14), rgba(249, 115, 22, 0.12));
  color: #b91c1c;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.45);
}

.session-confirm-icon svg {
  width: 28px;
  height: 28px;
}

.session-confirm-body {
  margin-top: 18px;
}

.session-confirm-title {
  margin: 0 0 10px;
  font-size: 22px;
  font-weight: 700;
  line-height: 1.2;
  color: #0f172a;
}

.session-confirm-text {
  margin: 0;
  color: #475569;
  font-size: 14px;
  line-height: 1.6;
}

.session-confirm-meta {
  display: grid;
  gap: 10px;
  margin-top: 20px;
}

.session-confirm-meta-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.94);
  border: 1px solid #e2e8f0;
}

.session-confirm-meta-label {
  color: #64748b;
  font-size: 13px;
}

.session-confirm-meta-value {
  color: #0f172a;
  font-size: 13px;
  font-weight: 600;
  text-align: right;
}

.session-confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.session-confirm-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-width: 148px;
  min-height: 44px;
  padding: 10px 18px;
  border-radius: 14px;
  border: 1px solid transparent;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.session-confirm-btn.is-cancel {
  background: #f8fafc;
  border-color: var(--security-soft-border);
  color: #334155;
}

.session-confirm-btn.is-cancel:hover:not(:disabled) {
  background: #f1f5f9;
}

.session-confirm-btn.is-danger {
  background: linear-gradient(135deg, #dc2626, #e11d48);
  border-color: rgba(225, 29, 72, 0.24);
  color: #ffffff;
  box-shadow: 0 16px 28px rgba(225, 29, 72, 0.22);
}

.session-confirm-btn.is-danger:hover:not(:disabled) {
  background: linear-gradient(135deg, #ef4444, #e11d48);
}

.session-confirm-btn:disabled,
.session-confirm-close:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 0.8s linear infinite;
}

.btn-danger .spinner {
  border-top-color: #dc2626;
  border-color: rgba(220, 38, 38, 0.2);
}

.spinner-large {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(59, 130, 246, 0.2);
  border-radius: 50%;
  border-top-color: #3b82f6;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0;
  color: #64748b;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}


@media (max-width: 768px) {
  .security-tab-label {
    display: none;
  }
}

@media (max-width: 480px) {
  .security-card {
    padding: 20px;
  }

  .sessions-toolbar {
    gap: 8px;
  }

  .sessions-stat-chip {
    width: 100%;
    justify-content: center;
  }

  .session-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .logout-link {
    align-self: flex-start;
    padding: 9px 12px;
    margin-top: 4px;
  }

  .session-confirm-overlay {
    padding: 16px;
  }

  .session-confirm-card {
    padding: 22px 18px 18px;
    border-radius: 20px;
  }

  .session-confirm-meta-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .session-confirm-meta-value {
    text-align: left;
  }

  .session-confirm-actions {
    flex-direction: column-reverse;
  }

  .session-confirm-btn {
    width: 100%;
  }
}

:global(html[data-theme='dark']) .security-settings-card {
  --security-card-bg:
      radial-gradient(circle at top right, rgba(59, 130, 246, 0.12), transparent 30%),
      linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(17, 24, 39, 0.98));
  --security-card-border: #334155;
  --security-shadow:
      0 28px 64px rgba(2, 6, 23, 0.34),
      inset 0 1px 0 rgba(255, 255, 255, 0.04);
  --security-soft-surface: rgba(15, 23, 42, 0.7);
  --security-soft-border: #334155;
  --security-chip-bg: rgba(15, 23, 42, 0.82);
  --security-chip-text: #cbd5e1;
  --security-tab-bg: rgba(15, 23, 42, 0.92);
  --security-tab-hover: rgba(51, 65, 85, 0.74);
  --security-tab-active: linear-gradient(180deg, rgba(30, 41, 59, 0.98), rgba(17, 24, 39, 0.98));
  --security-tab-active-text: #bfdbfe;
  --security-session-bg:
      radial-gradient(circle at top right, rgba(56, 189, 248, 0.1), transparent 32%),
      linear-gradient(180deg, rgba(15, 23, 42, 0.88), rgba(17, 24, 39, 0.92));
  --security-session-border: rgba(51, 65, 85, 0.95);
  --security-session-hover-border: #475569;
  --security-session-current-bg:
      radial-gradient(circle at top right, rgba(34, 197, 94, 0.12), transparent 30%),
      linear-gradient(180deg, rgba(6, 78, 59, 0.28), rgba(15, 23, 42, 0.92));
  --security-session-current-border: rgba(34, 197, 94, 0.34);
  --security-session-icon-bg: rgba(30, 41, 59, 0.9);
  --security-session-icon-color: #93c5fd;
  --security-session-current-icon-bg: rgba(6, 78, 59, 0.72);
  --security-session-current-icon-color: #86efac;
  --security-danger-soft-bg: rgba(127, 29, 29, 0.24);
  --security-danger-soft-border: rgba(248, 113, 113, 0.22);
  --security-danger-soft-text: #fda4af;
  --security-overlay: rgba(2, 6, 23, 0.62);
  --security-modal-bg:
      radial-gradient(circle at top right, rgba(14, 165, 233, 0.12), transparent 32%),
      linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(17, 24, 39, 0.98));
  --security-modal-border: #334155;
  --security-modal-shadow:
      0 34px 72px rgba(2, 6, 23, 0.48),
      inset 0 1px 0 rgba(255, 255, 255, 0.04);
  --security-modal-icon-bg: linear-gradient(135deg, rgba(127, 29, 29, 0.42), rgba(30, 41, 59, 0.94));
  --security-modal-icon-color: #fecaca;
}

:global(html[data-theme='dark']) .security-settings-card .sessions-empty-state strong,
:global(html[data-theme='dark']) .session-confirm-title,
:global(html[data-theme='dark']) .session-confirm-meta-value {
  color: #f8fafc;
}

:global(html[data-theme='dark']) .security-settings-card .sessions-empty-state,
:global(html[data-theme='dark']) .session-confirm-meta-item {
  background: rgba(15, 23, 42, 0.76);
  border-color: #334155;
}

:global(html[data-theme='dark']) .security-settings-card .sessions-stat-chip.muted,
:global(html[data-theme='dark']) .security-settings-card .sessions-empty-state,
:global(html[data-theme='dark']) .session-confirm-text,
:global(html[data-theme='dark']) .session-confirm-meta-label {
  color: #94a3b8;
}

:global(html[data-theme='dark']) .session-confirm-close {
  background: rgba(15, 23, 42, 0.82);
  border-color: #334155;
  color: #94a3b8;
}

:global(html[data-theme='dark']) .session-confirm-close:hover:not(:disabled) {
  background: rgba(30, 41, 59, 0.96);
  color: #f8fafc;
}

:global(html[data-theme='dark']) .session-confirm-btn.is-cancel {
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.88));
  border-color: #334155;
  color: #cbd5e1;
}

:global(html[data-theme='dark']) .session-confirm-btn.is-cancel:hover:not(:disabled) {
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.96), rgba(51, 65, 85, 0.94));
  border-color: #475569;
  color: #f8fafc;
}

:global(html[data-theme='dark']) .security-settings-card .session-danger-btn {
  background: linear-gradient(135deg, rgba(127, 29, 29, 0.82), rgba(190, 24, 93, 0.82));
  border-color: rgba(244, 63, 94, 0.22);
  color: #fff1f2;
  box-shadow: 0 16px 30px rgba(127, 29, 29, 0.26);
}

:global(html[data-theme='dark']) .security-settings-card .session-danger-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(153, 27, 27, 0.92), rgba(225, 29, 72, 0.88));
  border-color: rgba(251, 113, 133, 0.28);
}
</style>
