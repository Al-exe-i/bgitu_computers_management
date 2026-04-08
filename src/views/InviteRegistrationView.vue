<script>
import router from "@/router/index.js";
import api from "@/services/api.js";
import { useNotificationsStore } from "@/stores/notifications.js";
import {
  formatInviteDate,
  getInviteReasonText,
  getInviteRoleLabel,
  isValidEmail
} from "@/utils/invites.js";

const INVITE_PREVIEW_ENDPOINT = "/auth/invite/preview";
const INVITE_REGISTER_ENDPOINT = "/auth/invite/register";

export default {
  name: "InviteRegistrationView",

  data() {
    return {
      previewLoading: false,
      previewData: null,
      previewError: null,

      registering: false,

      showPassword: {
        main: false,
        repeat: false,
      },

      form: {
        name: '',
        surname: '',
        email: '',
        password: '',
        repeatPassword: '',
      }
    };
  },

  computed: {
    notify() {
      return useNotificationsStore();
    },

    inviteToken() {
      return String(this.$route.query.invite ?? this.$route.query.token ?? '').trim();
    },

    isInviteValid() {
      return this.previewData?.valid === true;
    },

    passwordsMatch() {
      return this.form.password === this.form.repeatPassword;
    },

    inviteRoleLabel() {
      return getInviteRoleLabel(this.previewData?.target_role);
    },

    expiresAtLabel() {
      return formatInviteDate(this.previewData?.expires_at);
    },

    inviteErrorText() {
      if (!this.inviteToken) {
        return 'В ссылке отсутствует invite token. Попросите администратора отправить приглашение заново.';
      }

      if (this.previewData?.reason) {
        return getInviteReasonText(this.previewData.reason);
      }

      return this.previewError || 'Не удалось проверить приглашение.';
    },

    isEmailReadonly() {
      return Boolean(this.previewData?.target_email);
    },

    passwordStrength() {
      const pwd = this.form.password || '';

      if (!pwd) {
        return {
          score: 0,
          percent: 0,
          level: 'empty',
          label: 'Введите пароль'
        };
      }

      let score = 0;

      if (pwd.length >= 8) score += 1;
      if (pwd.length >= 12) score += 1;
      if (pwd.length >= 16) score += 1;

      if (/[a-z]/.test(pwd)) score += 1;
      if (/[A-Z]/.test(pwd)) score += 1;
      if (/\d/.test(pwd)) score += 1;
      if (/[^\w\s]/.test(pwd)) score += 1;

      if (pwd.length < 6) {
        score = Math.min(score, 1);
      } else if (pwd.length < 8) {
        score = Math.min(score, 2);
      }

      const percent = Math.min((score / 6) * 100, 100);

      if (score <= 1) return { score, percent, level: 'weak', label: 'Очень слабый' };
      if (score === 2) return { score, percent, level: 'fair', label: 'Слабый' };
      if (score === 3) return { score, percent, level: 'medium', label: 'Средний' };
      if (score === 4) return { score, percent, level: 'good', label: 'Надежный' };

      return { score, percent, level: 'strong', label: 'Сильный' };
    }
  },

  methods: {
    togglePasswordVisibility(field) {
      this.showPassword[field] = !this.showPassword[field];
    },

    async loadInvitePreview() {
      this.previewError = null;
      this.previewData = null;

      if (!this.inviteToken) {
        return;
      }

      this.previewLoading = true;

      try {
        const response = await api.post(INVITE_PREVIEW_ENDPOINT, {
          token: this.inviteToken,
        });

        this.previewData = response.data;

        if (this.previewData?.target_email) {
          this.form.email = this.previewData.target_email;
        }
      } catch (error) {
        this.previewError = error.response?.data?.detail || 'Не удалось проверить invite-ссылку';
      } finally {
        this.previewLoading = false;
      }
    },

    validateForm() {
      if (!this.form.name.trim()) {
        this.notify.warning('Введите имя');
        return false;
      }

      if (!this.form.surname.trim()) {
        this.notify.warning('Введите фамилию');
        return false;
      }

      if (!isValidEmail(this.form.email)) {
        this.notify.warning('Введите корректный email');
        return false;
      }

      if (!this.form.password || this.form.password.length < 6) {
        this.notify.warning('Пароль должен быть не короче 6 символов');
        return false;
      }

      if (!this.passwordsMatch) {
        this.notify.warning('Пароли не совпадают');
        return false;
      }

      return true;
    },

    async registerByInvite() {
      if (!this.isInviteValid || !this.validateForm()) return;

      this.registering = true;

      try {
        await api.post(INVITE_REGISTER_ENDPOINT, {
          token: this.inviteToken,
          name: this.form.name.trim(),
          surname: this.form.surname.trim(),
          email: this.isEmailReadonly ? this.previewData.target_email : this.form.email.trim(),
          password: this.form.password,
        });

        this.notify.success('Аккаунт создан. Теперь войдите в систему.');
        await router.push({ name: 'Home', query: { login: '1' } });
      } catch (error) {
        const message = error.response?.data?.detail || 'Не удалось завершить регистрацию по приглашению';
        this.notify.error(message);
      } finally {
        this.registering = false;
      }
    },
  },

  watch: {
    inviteToken: {
      immediate: true,
      handler() {
        this.loadInvitePreview();
      }
    }
  }
};
</script>

<template>
  <div class="invite-register-page">
    <div class="invite-register-shell">
      <section class="invite-register-card">
        <div class="invite-register-head">
          <div class="invite-register-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path d="M7.5 6.5C7.5 8.981 9.519 11 12 11s4.5-2.019 4.5-4.5S14.481 2 12 2S7.5 4.019 7.5 6.5zM20 21h1v-1c0-3.859-3.141-7-7-7h-4c-3.86 0-7 3.141-7 7v1h17z" fill="currentColor"/></svg>
          </div>
          <div>
            <p class="invite-register-kicker">Регистрация по приглашению</p>
            <h1>Создание аккаунта</h1>
            <p class="invite-register-subtitle">Подтвердите данные приглашения и завершите регистрацию в системе.</p>
          </div>
        </div>

        <div v-if="previewLoading" class="invite-state-box">
          <div class="spinner-large"></div>
          <p>Проверяем invite-ссылку...</p>
        </div>

        <div v-else-if="!isInviteValid" class="invite-error-box">
          <div class="invite-error-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M12 8v5"></path>
              <path d="M12 16h.01"></path>
            </svg>
          </div>
          <h2>Приглашение недоступно</h2>
          <p>{{ inviteErrorText }}</p>
          <button class="btn btn-secondary" @click="$router.push({ name: 'Home' })">На главную</button>
        </div>

        <template v-else>
          <div class="invite-preview-grid">
            <div class="preview-pill">
              <span>Роль</span>
              <strong>{{ inviteRoleLabel }}</strong>
            </div>
            <div class="preview-pill">
              <span>Email</span>
              <strong>{{ previewData.target_email || form.email || 'Будет указан при регистрации' }}</strong>
            </div>
            <div class="preview-pill">
              <span>Действует до</span>
              <strong>{{ expiresAtLabel }}</strong>
            </div>
          </div>

          <form class="invite-form" @submit.prevent="registerByInvite">
            <div class="form-row two-columns">
              <div class="form-group">
                <label for="invite-name">Имя</label>
                <input id="invite-name" v-model.trim="form.name" type="text" class="form-input" placeholder="Иван" required>
              </div>

              <div class="form-group">
                <label for="invite-surname">Фамилия</label>
                <input id="invite-surname" v-model.trim="form.surname" type="text" class="form-input" placeholder="Иванов" required>
              </div>
            </div>

            <div class="form-group">
              <label for="invite-email">Email</label>
              <input
                id="invite-email"
                v-model.trim="form.email"
                type="email"
                class="form-input"
                :readonly="isEmailReadonly"
                :class="{ readonly: isEmailReadonly }"
                placeholder="teacher@example.com"
                required
              >
            </div>

            <div class="form-row two-columns">
              <div class="form-group">
                <label for="invite-password">Пароль</label>
                <div class="input-wrapper">
                  <input
                    id="invite-password"
                    v-model="form.password"
                    :type="showPassword.main ? 'text' : 'password'"
                    class="form-input"
                    placeholder="Минимум 6 символов"
                    minlength="6"
                    required
                  >
                  <button type="button" class="eye-btn" @click="togglePasswordVisibility('main')">
                    <svg v-if="!showPassword.main" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                      <line x1="1" y1="1" x2="23" y2="23"></line>
                    </svg>
                  </button>
                </div>
                <div v-if="form.password" class="password-strength" :class="`is-${passwordStrength.level}`">
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
                <label for="invite-password-repeat">Повторите пароль</label>
                <div class="input-wrapper">
                  <input
                    id="invite-password-repeat"
                    v-model="form.repeatPassword"
                    :type="showPassword.repeat ? 'text' : 'password'"
                    class="form-input"
                    :class="{ error: !passwordsMatch && form.repeatPassword }"
                    placeholder="Повторите пароль"
                    required
                  >
                  <button type="button" class="eye-btn" @click="togglePasswordVisibility('repeat')">
                    <svg v-if="!showPassword.repeat" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                      <line x1="1" y1="1" x2="23" y2="23"></line>
                    </svg>
                  </button>
                </div>
                <span v-if="!passwordsMatch && form.repeatPassword" class="error-text">
                  Пароли не совпадают
                </span>
              </div>
            </div>

            <div class="invite-actions">
              <button type="button" class="btn btn-secondary" @click="$router.push({ name: 'Home' })">Отмена</button>
              <button type="submit" class="btn btn-primary" :disabled="registering">
                <span v-if="registering" class="spinner-small spinner-white"></span>
                {{ registering ? 'Создаём аккаунт...' : 'Завершить регистрацию' }}
              </button>
            </div>
          </form>
        </template>
      </section>
    </div>
  </div>
</template>

<style scoped>
.invite-register-page {
  min-height: calc(100vh - 140px);
  padding: 40px 20px 56px;
}

.invite-register-shell {
  max-width: 820px;
  margin: 0 auto;
}

.invite-register-card {
  background:
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.12), transparent 28%),
    radial-gradient(circle at bottom left, rgba(20, 184, 166, 0.08), transparent 26%),
    var(--surface);
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 28px;
  box-shadow: var(--shadow-elev);
}

.invite-register-head {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
}

.invite-register-icon {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 16px 30px rgba(37, 99, 235, 0.24);
}

.invite-register-icon svg {
  width: 26px;
  height: 26px;
}

.invite-register-kicker {
  margin: 0 0 8px;
  color: #2563eb;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.invite-register-head h1 {
  margin: 0 0 6px;
  font-size: 30px;
  line-height: 1.15;
  color: var(--text-primary);
}

.invite-register-subtitle {
  margin: 0;
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.55;
}

.invite-preview-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.preview-pill {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 16px;
  background: var(--surface-soft);
  border: 1px solid var(--border);
}

.preview-pill span {
  color: var(--text-secondary);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.preview-pill strong {
  color: var(--text-primary);
  font-size: 15px;
  line-height: 1.4;
  word-break: break-word;
}

.invite-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row.two-columns {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.input-wrapper {
  position: relative;
}

.form-input {
  width: 100%;
  height: 46px;
  padding: 0 14px;
  border-radius: 14px;
  border: 1px solid var(--input-border);
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 14px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  box-sizing: border-box;
}

.input-wrapper .form-input {
  padding-right: 46px;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.14);
}

.form-input.readonly {
  background: rgba(148, 163, 184, 0.08);
  color: var(--text-secondary);
}

.form-input.error {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.14);
}

.eye-btn {
  position: absolute;
  top: 50%;
  right: 12px;
  transform: translateY(-50%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  transition: color 0.2s ease;
}

.eye-btn:hover {
  color: #475569;
}

.eye-btn svg {
  width: 18px;
  height: 18px;
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
  color: var(--text-secondary);
}

.password-strength-label {
  color: var(--text-secondary);
}

.password-strength-track {
  width: 100%;
  height: 8px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.2);
  overflow: hidden;
}

.password-strength-fill {
  width: 0;
  height: 100%;
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

.error-text {
  font-size: 12px;
  color: #dc2626;
}

.invite-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 44px;
  padding: 0 18px;
  border-radius: 12px;
  border: 1px solid transparent;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease, border-color 0.18s ease;
}

.btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #ffffff;
  box-shadow: 0 12px 26px rgba(37, 99, 235, 0.2);
}

.btn-secondary {
  background: var(--surface-soft);
  color: var(--text-primary);
  border-color: var(--border);
}

.invite-state-box,
.invite-error-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 14px;
  padding: 36px 20px;
  border-radius: 20px;
  background: var(--surface-soft);
  border: 1px solid var(--border);
}

.invite-error-box {
  background:
    radial-gradient(circle at top right, rgba(239, 68, 68, 0.1), transparent 30%),
    var(--surface-soft);
}

.invite-error-box h2 {
  margin: 0;
  color: var(--text-primary);
}

.invite-error-box p,
.invite-state-box p {
  margin: 0;
  color: var(--text-secondary);
  max-width: 520px;
  line-height: 1.55;
}

.invite-error-icon {
  width: 56px;
  height: 56px;
  border-radius: 18px;
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.invite-error-icon svg {
  width: 28px;
  height: 28px;
}

.spinner-small,
.spinner-large {
  border-radius: 999px;
  border-style: solid;
  border-color: rgba(148, 163, 184, 0.24);
  border-top-color: currentColor;
  animation: spin 0.8s linear infinite;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border-width: 2px;
}

.spinner-large {
  width: 34px;
  height: 34px;
  border-width: 3px;
  color: #2563eb;
}

.spinner-white {
  border-color: rgba(255, 255, 255, 0.3);
  border-top-color: #ffffff;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 760px) {
  .invite-register-card {
    padding: 22px;
    border-radius: 20px;
  }

  .invite-register-head {
    flex-direction: column;
  }

  .invite-register-head h1 {
    font-size: 26px;
  }

  .invite-preview-grid,
  .form-row.two-columns {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .invite-register-page {
    padding: 24px 14px 40px;
  }

  .invite-register-card {
    padding: 18px;
  }

  .invite-actions {
    flex-direction: column;
  }

  .invite-actions .btn {
    width: 100%;
  }
}
</style>
