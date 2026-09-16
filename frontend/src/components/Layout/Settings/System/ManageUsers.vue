<script>
import api from "@/services/api";
import ModalCloseButton from '@/components/Common/ModalCloseButton.vue';
import EntityInfoModal from '@/components/Common/EntityInfoModal.vue';
import PasswordEyeButton from '@/components/Common/PasswordEyeButton.vue';
import PasswordStrength from '@/components/Common/PasswordStrength.vue';
import RoleHelp from './RoleHelp.vue';
import { useAuthStore } from "@/stores/auth";
import { useNotificationsStore } from "@/stores/notifications";
import { getApiUrl } from "@/config/api.js";
import {
  RU_EMAIL_ERROR_MESSAGE,
  isRuEmail,
  isValidEmail,
  mapUserApiError,
} from "@/utils/users.js";
import noAvatar from '@/assets/user_no_icon.svg';

export default {
  name: "ManageUsers",
  components: { ModalCloseButton, EntityInfoModal, PasswordEyeButton, PasswordStrength, RoleHelp },

  data() {
    return {
      users: [],
      detailsUser: null,
      // Общая загрузка страницы
      loading: true,

      // Сюда складываем ID юзеров, над которыми прямо сейчас идет операция (смена роли, удаление).
      // Это нужно, чтобы крутить спиннер только на нужной строке.
      processingIds: [],

      // Состояние модалки
      showModal: false,
      createLoading: false,
      showPassword: false,
      passwordTarget: null,
      passwordLoading: false,
      passwordVisible: false,
      passwordError: '',
      passwordForm: { password: '', repeat: '' },
      passwordReturnFocus: null,
      passwordPreviousOverflow: '',

      createForm: {
        email: '',
        name: '',
        password: '',
        role: 1
      }
    };
  },

  computed: {
    userInfoFields() {
      return [
        { key: 'email', label: 'Email' }, { key: 'name', label: 'Имя' },
        { key: 'surname', label: 'Фамилия' }, { key: 'role', label: 'Роль', format: user => this.getRoleName(user) },
        { key: 'reg_date', label: 'Дата регистрации', format: user => user.reg_date ? new Date(user.reg_date).toLocaleString('ru-RU') : '' },
      ];
    },
    authStore() { return useAuthStore(); },
    notify() { return useNotificationsStore(); },

    isSuperuser() {
      return this.authStore.user?.is_superuser === true;
    }
  },

  methods: {
    openUserDetails(user) {
      if (this.authStore.user?.role !== 1 && user.id !== this.authStore.user?.id) return;
      this.detailsUser = user;
    },
    canResetPassword(user) {
      return this.isSuperuser && !user.is_superuser && user.id !== this.authStore.user?.id;
    },
    openPasswordModal(user) {
      if (!this.canResetPassword(user) || this.processingIds.includes(user.id)) return;
      this.passwordForm = { password: '', repeat: '' };
      this.passwordError = '';
      this.passwordVisible = false;
      this.passwordReturnFocus = document.activeElement;
      this.passwordPreviousOverflow = document.body.style.overflow;
      this.passwordTarget = user;
      document.addEventListener('keydown', this.handleEscape);
      document.body.style.overflow = 'hidden';
      this.$nextTick(() => this.$refs.resetPasswordInput?.focus({ preventScroll: true }));
    },
    closePasswordModal() {
      if (this.passwordLoading) return;
      this.passwordTarget = null;
      this.passwordForm = { password: '', repeat: '' };
      this.passwordVisible = false;
      this.passwordError = '';
      document.removeEventListener('keydown', this.handleEscape);
      document.body.style.overflow = this.passwordPreviousOverflow;
      this.passwordReturnFocus?.focus({ preventScroll: true });
      this.passwordReturnFocus = null;
    },
    async resetPassword() {
      if (this.passwordLoading || !this.passwordTarget || !this.canResetPassword(this.passwordTarget)) return;
      const { password, repeat } = this.passwordForm;
      if (password.length < 6 || password.length > 128) {
        this.passwordError = 'Пароль должен содержать от 6 до 128 символов';
        return;
      }
      if (password !== repeat) {
        this.passwordError = 'Пароли не совпадают';
        return;
      }
      this.passwordLoading = true;
      this.passwordError = '';
      const target = this.passwordTarget;
      let saved = false;
      try {
        await api.post(`/users/${target.id}/password`, { new_password: password });
        if (this.passwordTarget !== target) return;
        saved = true;
        this.notify.success('Пароль изменён. Сессии пользователя завершены.');
      } catch (error) {
        if (this.passwordTarget !== target) return;
        const status = error.response?.status;
        this.passwordError = status === 403 ? 'Недостаточно прав для смены пароля'
          : status === 404 ? 'Пользователь больше не существует'
          : status === 422 ? 'Проверьте пароль: от 6 до 128 символов'
          : 'Не удалось подтвердить смену пароля. Попробуйте ещё раз.';
      } finally {
        this.passwordLoading = false;
      }
      if (saved) this.closePasswordModal();
    },
    async fetchUsers() {
      this.loading = true;
      try {
        const res = await api.get('/users/all');
        this.users = res.data;
      } catch (e) {
        this.notify.error("Ошибка загрузки пользователей");
      } finally {
        this.loading = false;
      }
    },

    openCreateModal() {
      // Сбрасываем форму перед открытием
      this.createForm = {
        email: '',
        name: '',
        password: '',
        role: 2
      };
      this.showPassword = false;
      this.showModal = true;

      // Вешаем слушатель на Escape, чтобы удобно закрывать модалку
      document.addEventListener('keydown', this.handleEscape);
      document.body.style.overflow = 'hidden'; // Блокируем скролл страницы под модалкой
    },

    closeModal() {
      this.showModal = false;
      document.removeEventListener('keydown', this.handleEscape);
      document.body.style.overflow = '';
    },

    handleEscape(e) {
      if (this.passwordTarget && e.key === 'Tab') {
        const controls = [...this.$refs.passwordDialog.querySelectorAll('button:not(:disabled), input:not(:disabled)')];
        const first = controls[0];
        const last = controls.at(-1);
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last?.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first?.focus(); }
        return;
      }
      if (e.key !== 'Escape') return;
      if (this.passwordTarget) this.closePasswordModal();
      else this.closeModal();
    },

    togglePassword() {
      this.showPassword = !this.showPassword;
    },

    validateCreateUserForm() {
      const email = this.createForm.email.trim();

      if (!isValidEmail(email)) {
        this.notify.warning('Введите корректный email');
        return false;
      }

      if (!isRuEmail(email)) {
        this.notify.warning(RU_EMAIL_ERROR_MESSAGE);
        return false;
      }

      if (!this.createForm.password || this.createForm.password.length < 6) {
        this.notify.warning('Пароль должен быть не короче 6 символов');
        return false;
      }

      return true;
    },

    getCreateUserErrorMessage(error) {
      const status = error?.response?.status ?? error?.status;

      if (status === 409) {
        return 'Пользователь с таким Email уже существует';
      }

      return mapUserApiError(error, 'Не удалось создать пользователя');
    },

    async createUser() {
      if (!this.validateCreateUserForm()) return;

      this.createLoading = true;

      try {
        const email = this.createForm.email.trim();
        const name = this.createForm.name.trim();
        const payload = {
          email,
          password: this.createForm.password,
          role: this.createForm.role,
          ...(name && { name })
        };

        await api.post('/users', payload);

        this.notify.success(`Пользователь ${payload.email} успешно создан`);
        this.closeModal();
        await this.fetchUsers(); // Обновляем список, чтобы увидеть нового юзера
      } catch (error) {
        this.notify.error(this.getCreateUserErrorMessage(error));
      } finally {
        this.createLoading = false;
      }
    },

    getUserAvatar(user) {
      if (user.photo) {
        const apiBaseUrl = String(getApiUrl()).replace(/\/+$/, '');
        const version = encodeURIComponent(user.photo);
        return `${apiBaseUrl}/users/${user.id}/photo?v=${version}`;
      }

      return noAvatar;
    },

    handleAvatarError(event) {
      const image = event.currentTarget;
      if (!image) return;

      const fallbackUrl = new URL(noAvatar, window.location.href).href;
      if (image.src !== fallbackUrl) {
        image.src = noAvatar;
      }
    },

    getRoleName(user) {
      if (user?.is_superuser) return 'Superuser';
      if (user?.role === 1) return 'Администратор';
      if (user?.role === 2) return 'Преподаватель';
      return 'Пользователь';
    },

    getRoleClass(user) {
      if (user?.is_superuser) return 'badge-su';
      if (user?.role === 1) return 'badge-admin';
      if (user?.role === 2) return 'badge-teacher';
      return 'badge-user';
    },

    async changeRole(user) {
      if (user.id === this.authStore.user.id) {
        this.notify.error('Нельзя изменить собственную роль');
        return;
      }

      const newRole = user.role === 1 ? 2 : 1;

      // Блокируем кнопки этой строки
      this.processingIds.push(user.id);

      try {
        await api.patch(`/users/${user.id}`, { role: newRole });

        // Меняем роль локально, чтобы не дергать весь список юзеров с бэка
        const localUser = this.users.find(u => u.id === user.id);
        if (localUser) localUser.role = newRole;

        this.notify.success(`Роль для ${user.email} обновлена`);
      } catch (e) {
        this.notify.error('Ошибка изменения роли');
      } finally {
        // Разблокируем строку
        this.processingIds = this.processingIds.filter(id => id !== user.id);
      }
    },

    async deleteUser(user) {
      if (!confirm(`Вы действительно хотите удалить пользователя ${user.email}? Это действие необратимо.`)) return;

      this.processingIds.push(user.id);

      try {
        await api.delete(`/users/${user.id}`);
        this.users = this.users.filter(u => u.id !== user.id);
        this.notify.success('Пользователь удален из системы');
      } catch (e) {
        this.notify.error('Ошибка при удалении пользователя');
      } finally {
        this.processingIds = this.processingIds.filter(id => id !== user.id);
      }
    }
  },

  mounted() {
    this.fetchUsers();
  },

  beforeUnmount() {
    this.passwordTarget = null;
    this.passwordReturnFocus = null;
    this.passwordForm = { password: '', repeat: '' };
    // Чистим за собой слушатели, если юзер ушел со страницы при открытой модалке
    document.removeEventListener('keydown', this.handleEscape);
    document.body.style.overflow = '';
  }
};
</script>

<template>
  <div class="card">
    <EntityInfoModal v-if="detailsUser" kind="user" :avatar-src="detailsUser.photo ? getUserAvatar(detailsUser) : ''" :title="'Пользователь'" :endpoint="`/users/${detailsUser.id}`" :fields="userInfoFields" @close="detailsUser = null" />
    <div class="card-header">
      <div>
        <h2 class="section-title">Пользователи системы</h2>
        <p class="section-subtitle">Управление пользователями системы</p>
      </div>

      <button class="btn btn-primary" @click="openCreateModal">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
          <circle cx="9" cy="7" r="4"></circle>
          <line x1="19" y1="8" x2="19" y2="14"></line>
          <line x1="22" y1="11" x2="16" y2="11"></line>
        </svg>
        Добавить
      </button>
    </div>

    <!-- Таблица -->
    <div class="table-wrapper">
      <table class="data-table">
        <thead>
        <tr>
          <th>Пользователь</th>
          <th>Роль<RoleHelp /></th>
          <th v-if="isSuperuser" class="text-right">Действия</th>
        </tr>
        </thead>

        <tbody>
        <!-- Состояние загрузки (крутится по центру) -->
        <tr v-if="loading">
          <td :colspan="isSuperuser ? 3 : 2" class="text-center py-8">
            <div class="spinner-large mx-auto"></div>
            <p class="text-muted mt-2">Загрузка списка...</p>
          </td>
        </tr>

        <!-- Если список пуст -->
        <tr v-else-if="users.length === 0">
          <td :colspan="isSuperuser ? 4 : 3" class="text-center py-8">
            <p class="text-muted">Пользователи не найдены.</p>
          </td>
        </tr>

        <!-- Данные -->
        <tr v-else v-for="user in users" :key="user.id" class="table-row">

          <td>
            <button type="button" class="user-cell user-details-trigger" :aria-label="`О пользователе ${user.email}`" @click="openUserDetails(user)">
              <img
                  class="avatar-small"
                  :src="getUserAvatar(user)"
                  alt="Аватар"
                  @error="handleAvatarError"
              >
              <div class="user-info">
                <span class="user-email">{{ user.email }}</span>
                <span class="user-name text-muted" v-if="user.name">{{ user.name }}</span>
              </div>
            </button>
          </td>

          <td>
            <div class="role-cell">
                <span class="badge" :class="getRoleClass(user)">
                  {{ getRoleName(user) }}
                </span>

              <!-- Кнопки смены роли (только для админа, но не для себя и не для супера) -->
              <div
                  v-if="!user.is_superuser && authStore.user?.is_superuser && user.id !== authStore.user?.id"
                  class="role-actions"
              >
                <span v-if="processingIds.includes(user.id)" class="spinner-small text-muted"></span>
                <template v-else>
                  <button class="role-btn btn-down" v-if="user.role === 1" @click="changeRole(user)" title="Понизить до преподавателя">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"></polyline></svg>
                  </button>
                  <button class="role-btn btn-up" v-if="user.role === 2" @click="changeRole(user)" title="Повысить до администратора">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="18 15 12 9 6 15"></polyline></svg>
                  </button>
                </template>
              </div>
            </div>
          </td>

          <td v-if="isSuperuser" class="text-right">
            <button v-if="canResetPassword(user)" class="action-btn password-reset-btn"
                type="button" title="Изменить пароль" aria-label="Изменить пароль"
                :disabled="processingIds.includes(user.id)" @click="openPasswordModal(user)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <circle cx="8" cy="9" r="5"/><path d="m12 13 8 8m-3-3 3-3m-6 0 3-3"/>
              </svg>
            </button>
            <button
                class="action-btn delete"
                title="Удалить пользователя"
                :disabled="user.id === authStore.user.id || processingIds.includes(user.id)"
                @click="deleteUser(user)"
            >
              <span v-if="processingIds.includes(user.id)" class="spinner-small text-danger"></span>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
            </button>
          </td>
        </tr>
        </tbody>
      </table>
    </div>

    <!-- Модалка добавления (с Vue transition) -->
    <Teleport to="body">
    <transition name="modal">
      <div v-if="showModal" class="modal-overlay system-users-modal-overlay" @click.self="closeModal">
        <div class="modal-content system-users-modal-content">

          <div class="modal-header">
            <h3>Создать пользователя</h3>
            <ModalCloseButton @click="closeModal" />
          </div>

          <form @submit.prevent="createUser" class="modal-body">

            <div class="form-group">
              <label>Email (Логин) <span class="required">*</span></label>
              <input type="email" v-model="createForm.email" class="form-input" required placeholder="user@example.ru">
            </div>

            <div class="form-group">
              <label>Имя и фамилия</label>
              <input type="text" v-model="createForm.name" class="form-input" placeholder="Иван Иванов">
            </div>

            <div class="form-group">
              <label>Права доступа</label>
              <select v-model="createForm.role" class="form-select">
                <option :value="2">Преподаватель (Ограниченные права)</option>
                <option :value="1">Администратор (Расширенные права)</option>
              </select>
            </div>

            <div class="form-group">
              <label>Пароль <span class="required">*</span></label>
              <div class="input-wrapper">
                <input
                    :type="showPassword ? 'text' : 'password'"
                    v-model="createForm.password"
                    class="form-input"
                    required
                    minlength="6"
                    placeholder="Минимум 6 символов"
                >
                <button type="button" class="eye-btn" @click="togglePassword" title="Показать/Скрыть пароль">
                  <svg v-if="!showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
                </button>
              </div>
              <PasswordStrength :value="createForm.password" />
            </div>

            <div class="modal-actions">
              <button
                type="button"
                class="btn btn-secondary modal-action-btn modal-action-btn-cancel"
                @click="closeModal"
                :disabled="createLoading"
              >
                Отмена
              </button>
              <button
                type="submit"
                class="btn btn-primary modal-action-btn modal-action-btn-submit"
                :disabled="createLoading"
              >
                <span v-if="createLoading" class="spinner-small spinner-white"></span>
                {{ createLoading ? 'Создание...' : 'Создать аккаунт' }}
              </button>
            </div>

          </form>
        </div>
      </div>
    </transition>
    <transition name="modal">
      <div v-if="passwordTarget" class="modal-overlay password-reset-overlay" @click.self="closePasswordModal">
        <div ref="passwordDialog" class="modal-content password-reset-modal" role="dialog" aria-modal="true" aria-labelledby="reset-password-title" aria-describedby="reset-password-note" :aria-busy="passwordLoading">
          <div class="modal-header password-reset-header">
            <ModalCloseButton :disabled="passwordLoading" @click="closePasswordModal" />
            <span class="password-reset-symbol" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="10" width="14" height="11" rx="3"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3"/></svg></span>
            <div class="password-reset-identity"><h3 id="reset-password-title">Изменить пароль</h3><p class="password-reset-target">{{ passwordTarget.email }}</p></div>
          </div>
          <form class="modal-body" @submit.prevent="resetPassword">
            <p id="reset-password-note" class="password-reset-note">После сохранения все сеансы пользователя завершатся. Для входа потребуется новый пароль.</p>
            <div class="form-group">
              <label for="reset-password">Новый пароль</label>
              <div class="input-wrapper password-input-wrapper"><input id="reset-password" ref="resetPasswordInput" v-model="passwordForm.password"
                  :type="passwordVisible ? 'text' : 'password'" class="form-input" required minlength="6" maxlength="128"
                  autocomplete="new-password" :disabled="passwordLoading" :aria-describedby="passwordError ? 'reset-password-error' : undefined" :aria-invalid="!!passwordError">
                <PasswordEyeButton :visible="passwordVisible" @toggle="passwordVisible = !passwordVisible" />
              </div>
              <PasswordStrength :value="passwordForm.password" />
            </div>
            <div class="form-group">
              <label for="reset-password-repeat">Повторите пароль</label>
              <div class="input-wrapper password-input-wrapper"><input id="reset-password-repeat" v-model="passwordForm.repeat" :type="passwordVisible ? 'text' : 'password'"
                  class="form-input" required minlength="6" maxlength="128" autocomplete="new-password" :disabled="passwordLoading">
                <PasswordEyeButton :visible="passwordVisible" @toggle="passwordVisible = !passwordVisible" />
              </div>
            </div>
            <p v-if="passwordError" id="reset-password-error" class="password-reset-error" role="alert">{{ passwordError }}</p>
            <div class="modal-actions">
              <button type="button" class="btn btn-secondary modal-action-btn modal-action-btn-cancel" :disabled="passwordLoading" @click="closePasswordModal">Отмена</button>
              <button type="submit" class="btn btn-primary modal-action-btn modal-action-btn-submit" :disabled="passwordLoading">{{ passwordLoading ? 'Сохранение...' : 'Изменить пароль' }}</button>
            </div>
          </form>
        </div>
      </div>
    </transition>
    </Teleport>

  </div>
</template>

<style scoped>
.user-details-trigger { width: 100%; border: 0; background: transparent; font: inherit; color: inherit; text-align: left; padding: 4px 0; cursor: pointer; border-radius: 6px; }
.user-details-trigger:focus-visible { outline: 2px solid #3b82f6; outline-offset: 4px; }
.password-input-wrapper .form-input { padding-right: 46px; }
@media (hover: hover) { .user-details-trigger:hover .user-email { text-decoration: underline; text-underline-offset: 3px; } }
.password-reset-error { color: #b91c1c; font-size: 14px; line-height: 1.5; }
.action-btn.password-reset-btn { margin-right: 8px; color: #475569; }
html[data-theme='dark'] .password-reset-error { color: #fca5a5; }
html[data-theme='dark'] .action-btn.password-reset-btn { color: #cbd5e1; }
@media (hover: hover) {
  .action-btn.password-reset-btn:hover:not(:disabled) { background: #e2e8f0; }
  html[data-theme='dark'] .action-btn.password-reset-btn:hover:not(:disabled) { background: #334155; }
}
/* --- Базовая структура --- */
.card {
  background: #ffffff;
  padding: 24px;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
  font-family: system-ui, -apple-system, sans-serif;
  color: #0f172a;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.section-title {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
}

.section-subtitle {
  margin: 0;
  font-size: 14px;
  color: #64748b;
}

/* --- Утилиты --- */
.text-muted {
  color: #64748b;
}

.text-danger {
  color: #ef4444;
}

.text-right {
  text-align: right;
}

.text-center {
  text-align: center;
}

.py-8 {
  padding-top: 2rem !important;
  padding-bottom: 2rem !important;
}

.mx-auto {
  margin-left: auto;
  margin-right: auto;
}

.font-mono {
  font-family: ui-monospace, monospace;
  font-size: 13px;
  color: #94a3b8;
}

/* --- Таблица --- */
.table-wrapper {
  overflow-x: auto;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 650px;
  text-align: left;
}

.data-table th {
  padding: 14px 16px;
  background: #f8fafc;
  color: #475569;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  border-bottom: 2px solid #e2e8f0;
}

.data-table td {
  padding: 14px 16px;
  border-bottom: 1px solid #e2e8f0;
  font-size: 14px;
  vertical-align: middle;
}

.table-row {
  transition: background-color 0.15s ease;
}

.table-row:hover {
  background-color: #f1f5f9;
}

.table-row:last-child td {
  border-bottom: none;
}

/* --- Ячейка пользователя --- */
.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar-small {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  background: #e2e8f0;
  border: 1px solid #e2e8f0;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-email {
  font-weight: 500;
  color: #0f172a;
}

.user-name {
  font-size: 12px;
}

/* --- Ячейка роли --- */
.role-cell {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.badge {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.badge-su {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fee2e2;
}

.badge-admin {
  background: #e0f2fe;
  color: #0284c7;
  border: 1px solid #bae6fd;
}

.badge-teacher {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}

.badge-user {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;
}

.role-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
}

.role-btn {
  background: none;
  border: none;
  padding: 4px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.role-btn svg {
  width: 16px;
  height: 16px;
}

.role-btn.btn-down {
  color: #f59e0b;
}

.role-btn.btn-down:hover {
  background: #fef3c7;
  color: #d97706;
}

.role-btn.btn-up {
  color: #10b981;
}

.role-btn.btn-up:hover {
  background: #d1fae5;
  color: #059669;
}

/* --- Кнопки действий --- */
.action-btn {
  background: none;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #94a3b8;
  transition: all 0.2s ease;
  float: right;
}

.action-btn svg {
  width: 18px;
  height: 18px;
}

.action-btn.delete:hover:not(:disabled) {
  background: #fee2e2;
  color: #ef4444;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* --- Общие кнопки --- */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn svg {
  width: 18px;
  height: 18px;
}

.btn-primary {
  background: #0f172a;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #334155;
  transform: translateY(-1px);
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;
}

.btn-secondary:hover:not(:disabled) {
  background: #e2e8f0;
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

/* --- Модальное окно --- */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 440px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.modal-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}

.required {
  color: #ef4444;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.form-input,
.form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  color: #0f172a;
  background: #ffffff;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.input-wrapper .form-input {
  padding-right: 40px;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.form-select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg width='12' height='8' viewBox='0 0 12 8' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1.5L6 6.5L11 1.5' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
  padding-right: 36px;
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

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 28px;
}

.modal-action-btn {
  min-width: 148px;
}

/* --- Спиннеры --- */
.spinner-large {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(59, 130, 246, 0.2);
  border-radius: 50%;
  border-top-color: #3b82f6;
  animation: spin 0.8s linear infinite;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(148, 163, 184, 0.3);
  border-radius: 50%;
  border-top-color: currentColor;
  animation: spin 0.8s linear infinite;
}

.spinner-white {
  border-color: rgba(255, 255, 255, 0.3);
  border-top-color: white;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* --- Анимации Vue --- */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-content {
  animation: modal-slide-in 0.3s ease-out;
}

.modal-leave-active .modal-content {
  animation: modal-slide-in 0.3s ease-out reverse;
}

@keyframes modal-slide-in {
  from {
    transform: translateY(20px) scale(0.95);
    opacity: 0;
  }
  to {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}
.password-reset-overlay { padding: 20px; background: rgb(9 17 32 / .54); backdrop-filter: blur(6px); }
.password-reset-modal {
  --reset-ink: #172033; --reset-muted: #637187; --reset-tint: #f1f6fd;
  --reset-emblem: #e5efff; --reset-accent: #285bd4; --reset-border: #e3e8ef; --reset-input: #f8fafc;
  max-width: 480px; max-height: calc(100dvh - 40px); border: 0; border-radius: 24px;
  overflow: hidden; color: var(--reset-ink); box-shadow: 0 24px 80px rgb(9 17 32 / .22);
}
html[data-theme='dark'] .password-reset-modal {
  --reset-ink: #e2e8f0; --reset-muted: #9eafc5; --reset-tint: #152136;
  --reset-emblem: #203657; --reset-accent: #86b0ff; --reset-border: #28364b; --reset-input: #0d1625;
  border: 0 !important;
}
.password-reset-modal .password-reset-header { position: relative; flex-shrink: 0; justify-content: flex-start; gap: 16px; padding: 30px 54px 26px 28px; border: 0; background: var(--reset-tint) !important; }
.password-reset-header .modal-round-close { position: absolute; top: 14px; right: 14px; }
.password-reset-symbol { display: grid; place-items: center; flex: 0 0 52px; height: 52px; border-radius: 16px; color: var(--reset-accent); background: var(--reset-emblem); }
.password-reset-symbol svg { width: 28px; height: 28px; }
.password-reset-identity { min-width: 0; }
.password-reset-header h3 { font-size: 23px; line-height: 1.2; letter-spacing: -.025em; font-weight: 600; }
.password-reset-target { margin: 7px 0 0; color: var(--reset-muted); font-size: 13px; font-weight: 400; line-height: 1.4; overflow-wrap: anywhere; }
.password-reset-modal .modal-body { padding: 24px 28px; min-height: 0; overflow-y: auto; overscroll-behavior: contain; scrollbar-width: thin; }
.password-reset-modal .password-reset-note { color: var(--reset-muted); margin: 0 0 22px; font-size: 13px; line-height: 1.55; }
.password-reset-modal .form-group { gap: 8px; margin-bottom: 20px; }
.password-reset-modal .form-group label { color: var(--reset-muted); font-size: 13px; }
.password-reset-modal .form-input { min-height: 44px; background: var(--reset-input); border-radius: 10px; color: var(--reset-ink); font-size: 15px; transition: border-color 150ms ease; }
.password-reset-modal .form-input:focus { outline: none; border-color: var(--reset-accent); box-shadow: inset 0 0 0 1px var(--reset-accent); }
html[data-theme='dark'] .password-reset-modal .form-input:focus { border-color: var(--reset-accent) !important; }
.password-reset-modal .modal-actions { padding-top: 20px; margin-top: 24px; border-top: 1px solid var(--reset-border); gap: 8px; }
.password-reset-modal .modal-action-btn { width: auto; min-width: 0; min-height: 40px; border-radius: 10px; padding: 10px 16px; font-size: 13px; transition: background-color 150ms ease; }
.password-reset-modal .btn-secondary { color: var(--reset-ink); background: transparent; border: 1px solid var(--reset-border); }
.password-reset-modal .btn-primary { background: #285bd4; color: #fff; }
.password-reset-modal .btn:disabled { opacity: .55; cursor: default; }
.password-reset-modal .btn:focus-visible { outline: 2px solid var(--reset-accent); outline-offset: 3px; }
@media (hover: hover) {
  .password-reset-modal .btn-primary:hover:not(:disabled) { background: #204ebd; transform: none; }
  .password-reset-modal .btn-secondary:hover:not(:disabled) { background: var(--reset-tint); transform: none; }
}
@media (max-width: 480px) {
  .password-reset-overlay { padding: 12px; }
  .password-reset-modal { max-height: calc(100dvh - 24px); border-radius: 18px; }
  .password-reset-modal .password-reset-header { padding: 26px 50px 22px 22px; gap: 12px; }
  .password-reset-symbol { flex-basis: 42px; height: 42px; border-radius: 12px; }
  .password-reset-header h3 { font-size: 21px; }
  .password-reset-modal .modal-body { padding: 22px; }
  .password-reset-modal .form-input { font-size: 16px; }
  .password-reset-modal .modal-action-btn { min-height: 44px; }
  .password-reset-modal .btn-primary { flex: 1; }
}
@media (prefers-reduced-motion: reduce) {
  .password-reset-overlay, .password-reset-overlay .password-reset-modal { animation: none; transition: none; }
}
@media (prefers-reduced-transparency: reduce) { .password-reset-overlay { backdrop-filter: none; } }
</style>
