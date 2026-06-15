<script>
import api from "@/services/api";
import { useAuthStore } from "@/stores/auth";
import { useNotificationsStore } from "@/stores/notifications";
import {
  RU_EMAIL_ERROR_MESSAGE,
  isRuEmail,
  isValidEmail,
  mapInviteApiError,
} from "@/utils/invites.js";
import noAvatar from '@/assets/user_no_icon.svg';

export default {
  name: "ManageUsers",

  data() {
    return {
      users: [],
      // Общая загрузка страницы
      loading: true,

      // Сюда складываем ID юзеров, над которыми прямо сейчас идет операция (смена роли, удаление).
      // Это нужно, чтобы крутить спиннер только на нужной строке.
      processingIds: [],

      // Состояние модалки
      showModal: false,
      createLoading: false,
      showPassword: false,

      createForm: {
        email: '',
        name: '',
        password: '',
        role: 1
      }
    };
  },

  computed: {
    authStore() { return useAuthStore(); },
    notify() { return useNotificationsStore(); },

    isSuperuser() {
      return this.authStore.user?.is_superuser === true;
    }
  },

  methods: {
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
      if (e.key === 'Escape') this.closeModal();
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

      return mapInviteApiError(error, 'Не удалось создать пользователя');
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
      if (user.photo) return `${import.meta.env.VITE_API_BASE_URL}/admin/files/avatars/${user.photo}`;
      return noAvatar;
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
    // Чистим за собой слушатели, если юзер ушел со страницы при открытой модалке
    document.removeEventListener('keydown', this.handleEscape);
    document.body.style.overflow = '';
  }
};
</script>

<template>
  <div class="card">
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
          <th>Роль</th>
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
            <div class="user-cell">
              <img class="avatar-small" :src="getUserAvatar(user)" alt="Аватар">
              <div class="user-info">
                <span class="user-email">{{ user.email }}</span>
                <span class="user-name text-muted" v-if="user.name">{{ user.name }}</span>
              </div>
            </div>
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
            <button class="close-btn" @click="closeModal" title="Закрыть">✕</button>
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
    </Teleport>

  </div>
</template>

<style scoped>
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

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  color: #94a3b8;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: 0.2s;
}

.close-btn:hover {
  background: #f1f5f9;
  color: #0f172a;
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
</style>
