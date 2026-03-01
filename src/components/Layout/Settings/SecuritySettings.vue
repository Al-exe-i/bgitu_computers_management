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
      sessions: []
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

    async handleLogoutSession(sid) {
      if (!confirm('Завершить этот сеанс?')) return;
      this.loadingAction = true;

      try {
        await api.delete(`/sessions/${sid}`);
        this.notify.success('Сеанс успешно завершен');
        // Удаляем из локального списка или перезапрашиваем
        this.sessions = this.sessions.filter(s => s.sid !== sid);
      } catch (error) {
        const msg = error.response?.data?.detail || 'Ошибка при завершении сеанса';
        this.notify.error(msg);
      } finally {
        this.loadingAction = false;
      }
    },

    async handleLogoutAll() {
      if (!confirm('Вы уверены, что хотите выйти на всех устройствах?')) return;
      this.loadingAction = true;

      try {
        await this.authStore.logout(true)
      } catch (error) {
        const msg = error.response?.data?.detail || 'Ошибка при выходе из устройств';
        this.notify.error(msg);
      } finally {
        this.loadingAction = false;
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
  <div class="security-card">
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

          <div class="sessions-list">
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
                  <span>Начата: {{ formatDate(session.created_at) }} UTC</span>
                </div>
              </div>

              <button
                  v-if="!session.is_current"
                  class="logout-link"
                  @click="handleLogoutSession(session.sid)"
                  :disabled="loadingAction"
                  title="Завершить этот сеанс"
              >
                Завершить
              </button>
            </div>
          </div>

          <div class="actions-footer">
            <button class="btn btn-danger" @click="handleLogoutAll" :disabled="loadingAction || activeSessions.length <= 1">
              <span v-if="loadingAction" class="spinner"></span>
              {{ loadingAction ? 'Обработка...' : 'Завершить все сеансы' }}
            </button>
          </div>
        </template>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.security-card {
  background: #ffffff;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.03);
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
  background: #f1f5f9;
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
  background: #e2e8f0;
  color: #334155;
}

.security-tab.active {
  background: #ffffff;
  color: #3b82f6;
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

.session-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #ffffff;
  transition: border-color 0.2s;
}

.session-item:hover {
  border-color: #cbd5e1;
}

.session-item.is-current {
  border-color: #bbf7d0;
  background: #f0fdf4;
}

.session-icon {
  width: 40px;
  height: 40px;
  background: #f1f5f9;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  margin-right: 16px;
  flex-shrink: 0;
}

.session-item.is-current .session-icon {
  background: #dcfce7;
  color: #16a34a;
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
  background: #22c55e;
  color: #ffffff;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
}

.logout-link {
  background: none;
  border: none;
  color: #64748b;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.2s;
}

.logout-link:hover:not(:disabled) {
  color: #ef4444;
  background: #fee2e2;
}

.logout-link:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.actions-footer {
  border-top: 1px solid #e2e8f0;
  padding-top: 24px;
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

  .session-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .logout-link {
    align-self: flex-start;
    padding: 0;
    margin-top: 4px;
    background: transparent !important;
  }
}
</style>
