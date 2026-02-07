<script>
import api from "@/services/api";
import { useAuthStore } from "@/stores/auth";
import { useNotificationsStore } from "@/stores/notifications";
import noAvatar from '@/assets/user_no_icon.svg';

export default {
  name: "ManageUsers",
  data() {
    return {
      users: [],
      loading: true,

      showModal: false,
      createLoading: false,
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

    // Проверка на суперпользователя
    isSuperuser() {
      return this.authStore.user?.is_superuser === true;
    }
  },
  methods: {
    async fetchUsers() {
      this.loading = true;
      try
      {
        const res = await api.get('/users/all');
        this.users = res.data;
      }
      catch (e) {
        this.notify.error("Ошибка загрузки пользователей");
      }
      finally
      {
        this.loading = false;
      }
    },

    openCreateModal() {
      this.createForm = {
        email: '',
        name: '',
        password: '',
        role: 2
      };
      this.showModal = true;
    },

    closeModal() {
      this.showModal = false;
    },

    async createUser() {
      this.createLoading = true;
      try {
        // Формируем payload. Имена полей должны совпадать с UserCreate в Pydantic
        const payload = {
          email: this.createForm.email,
          password: this.createForm.password,
          role: this.createForm.role,
          // Отправляем имя только если заполнено
          ...(this.createForm.name && { name: this.createForm.name })
        };

        await api.post('/users/', payload);

        this.notify.success(`Пользователь ${payload.email} создан`);
        this.closeModal();
        await this.fetchUsers(); // Обновляем список
      }
      catch (error)
      {
        const msg = error.response?.data?.detail || "Не удалось создать пользователя";
        this.notify.error(msg);
      }
      finally {
        this.createLoading = false;
      }
    },

    getUserAvatar(user)
    {
      if (user.photo) return `${import.meta.env.VITE_API_BASE_URL}/admin/files/avatars/${user.photo}`;
      return noAvatar;
    },

    getRoleName(user)
    {
      const role = user?.role;
      if(user?.is_superuser) return 'SU';
      if (role === 1) return 'Админ';
      if (role === 2) return 'Преподаватель';
      return 'Пользователь';
    },

    getRoleClass(user) {
      const role = user?.role;
      if(user?.is_superuser) return 'badge-su';
      if (role === 1) return 'badge-admin';
      if (role === 2) return 'badge-user';
      return 'badge-user';
    },

    async changeRole(user) {
      if (user.id === this.authStore.user.id)
      {
        this.notify.error('Нельзя изменить свою роль');
        return;
      }

      const newRole = user.role === 1 ? 2 : 1;
      try
      {
        const response = await api.patch(`/users/${user.id}`, {"role": newRole});
        const localUser = this.users.find(u => u.id === user.id);
        if (localUser) localUser.role = newRole;
        this.notify.success(`Роль пользователя ${user.email} изменена`);
      }
      catch (e)
      {
        this.notify.error('Ошибка изменения роли');
      }
    },

    async deleteUser(user) {
      if (!confirm(`Удалить пользователя ${user.email}?`)) return;

      try {
        await api.delete(`/users/${user.id}`);
        this.users = this.users.filter(u => u.id !== user.id);
        this.notify.success('Пользователь удален');
      } catch (e) {
        this.notify.error('Ошибка удаления');
      }
    }
  },

  mounted() {
    this.fetchUsers();
  }
};
</script>

<template>
  <div class="card">
    <div class="card-header">
      <h2>Пользователи системы</h2>
      <!-- Кнопка добавления -->
      <button class="btn-primary" @click="openCreateModal">
        <span>
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 1024 1024"><path fill="currentColor" d="M678.3 642.4c24.2-13 51.9-20.4 81.4-20.4h.1c3 0 4.4-3.6 2.2-5.6a371.67 371.67 0 0 0-103.7-65.8c-.4-.2-.8-.3-1.2-.5C719.2 505 759.6 431.7 759.6 349c0-137-110.8-248-247.5-248S264.7 212 264.7 349c0 82.7 40.4 156 102.6 201.1c-.4.2-.8.3-1.2.5c-44.7 18.9-84.8 46-119.3 80.6a373.42 373.42 0 0 0-80.4 119.5A373.6 373.6 0 0 0 137 888.8a8 8 0 0 0 8 8.2h59.9c4.3 0 7.9-3.5 8-7.8c2-77.2 32.9-149.5 87.6-204.3C357 628.2 432.2 597 512.2 597c56.7 0 111.1 15.7 158 45.1a8.1 8.1 0 0 0 8.1.3M512.2 521c-45.8 0-88.9-17.9-121.4-50.4A171.2 171.2 0 0 1 340.5 349c0-45.9 17.9-89.1 50.3-121.6S466.3 177 512.2 177s88.9 17.9 121.4 50.4A171.2 171.2 0 0 1 683.9 349c0 45.9-17.9 89.1-50.3 121.6C601.1 503.1 558 521 512.2 521M880 759h-84v-84c0-4.4-3.6-8-8-8h-56c-4.4 0-8 3.6-8 8v84h-84c-4.4 0-8 3.6-8 8v56c0 4.4 3.6 8 8 8h84v84c0 4.4 3.6 8 8 8h56c4.4 0 8-3.6 8-8v-84h84c4.4 0 8-3.6 8-8v-56c0-4.4-3.6-8-8-8"/></svg>
        </span> Добавить
      </button>
    </div>

    <!-- Таблица -->
    <div class="table-wrapper">
      <table class="data-table">
        <thead>
        <tr>
          <th>Пользователь</th>
          <th>Роль</th>
          <th>Telegram ID</th>
          <th v-if="isSuperuser">Действия</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="user in users" :key="user.id">
          <!-- Юзер + Аватар -->
          <td>
            <div class="user-cell">
              <img class="avatar-small" :src="getUserAvatar(user)">
              <div class="user-info">
                <span class="user-email">{{ user.email }}</span>
                <span class="user-name" v-if="user.name">{{ user.name }}</span>
              </div>
            </div>
          </td>

          <!-- Роль -->
          <td>
            <div class="role-td">
              <span class="badge" :class="getRoleClass(user)">
              {{ getRoleName(user) }}
            </span>
              <span class="role-control" v-if="!user?.is_superuser && authStore?.user?.is_superuser">
              <svg @click="changeRole(user)" v-if="user.role === 1" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><title>Понизить</title><path fill="#dc2626" d="M12 17.308L6.692 12l.708-.708l4.1 4.1V5.5h1v9.892l4.1-4.1l.708.708z"/></svg>
              <svg @click="changeRole(user)" v-if="user.role === 2" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><title>Повысить</title><path fill="#10b981" d="M11.5 17.308V7.415l-4.1 4.1l-.708-.707L12 5.5l5.308 5.308l-.708.707l-4.1-4.1v9.893z"/></svg>
            </span>
            </div>
          </td>

          <!-- TG ID -->
          <td>
            {{ user.telegram_id || `Нет` }}
          </td>

          <!-- Действия (Только Superuser) -->
          <td v-if="isSuperuser">
            <button
                class="btn-icon delete"
                title="Удалить"
                :disabled="user.id === authStore.user.id"
                @click="deleteUser(user)"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
          </td>
        </tr>
        </tbody>
      </table>

      <div v-if="loading" class="loading-state">Загрузка...</div>
    </div>

    <!-- МОДАЛКА ДОБАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯ -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <h3>Новый пользователь</h3>

        <form @submit.prevent="createUser">

          <!-- Email -->
          <div class="form-group">
            <label>Email (Логин) <span class="required">*</span></label>
            <input
                type="text"
                v-model="createForm.email"
                class="form-input"
                required
                placeholder="user@example.com"
            >
          </div>

          <!-- Имя -->
          <div class="form-group">
            <label>Имя</label>
            <input
                type="text"
                v-model="createForm.name"
                class="form-input"
                placeholder="Иван Иванов"
            >
          </div>

          <!-- Роль -->
          <div class="form-group">
            <label>Роль</label>
            <select v-model="createForm.role" class="form-select">
              <option :value="2">Преподаватель</option>
              <option :value="1">Администратор</option>
            </select>
          </div>

          <!-- Пароль -->
          <div class="form-group">
            <label>Пароль <span class="required">*</span></label>
            <input
                type="password"
                v-model="createForm.password"
                class="form-input"
                required
                minlength="4"
                placeholder="••••••"
            >
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="closeModal">Отмена</button>
            <button type="submit" class="btn-primary" :disabled="createLoading">
              {{ createLoading ? 'Создание...' : 'Создать' }}
            </button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<style scoped>
.card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.card-header h2 { font-size: 18px; color: #0f172a; margin: 0; }

/* Таблица */
.table-wrapper { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; min-width: 600px; }

.data-table th {
  text-align: left;
  padding: 12px 10px;
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  border-bottom: 1px solid #e2e8f0;
}

.data-table td {
  padding: 12px 10px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
  font-size: 14px;
}

.role-td {
  display: inline-flex;
  align-items: center;
}

.role-control {
  display: flex;
  margin-left: 1rem;
}

.role-td .role-control:hover {
  cursor: pointer;
  transform: scale(1.05);
}

/* User Cell */
.user-cell { display: flex; align-items: center; gap: 10px; }
.avatar-small { width: 32px; height: 32px; border-radius: 50%; object-fit: cover; background: #e2e8f0; }
.user-info { display: flex; flex-direction: column; }
.user-email { font-weight: 500; }
.user-name { font-size: 12px; color: #94a3b8; }

/* Badges */
.badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

.badge-su {
  background: #fee2e2;
  color: #dc2626;
}

.badge-admin {
  background: #e0f2fe;
  color: #0284c7;
}

.badge-user {
  background: #f1f5f9;
  color: #64748b;
}

/* Buttons */
.btn-primary {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
}

.btn-secondary:hover {
  background: #e2e8f0;
}

.btn-icon { background: none; border: none; cursor: pointer; padding: 5px; color: #94a3b8; transition: color 0.2s; }
.btn-icon:hover { color: #3b82f6; }
.btn-icon.delete:hover { color: #ef4444; }
.btn-icon:disabled { opacity: 0.3; cursor: not-allowed; }

.loading-state { padding: 20px; text-align: center; color: #94a3b8; }

/* СТИЛИ МОДАЛКИ */
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex; justify-content: center; align-items: center;
  z-index: 100;
}
.modal-content {
  background: white; padding: 25px; border-radius: 12px; width: 400px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
}
.modal-content h3 { margin-top: 0; margin-bottom: 20px; font-size: 18px; color: #0f172a; }

.form-group { margin-bottom: 15px; display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 13px; font-weight: 500; color: #64748b; }
.required { color: #ef4444; }

.form-input {
  padding: 10px; border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
}
.form-input:focus {
  border-color: #3b82f6;
  outline: none;
}

.form-select {
  background-image: url("data:image/svg+xml,%3Csvg width='12' height='8' viewBox='0 0 12 8' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%236b7280' stroke-width='2' fill='none'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
  padding: 10px; border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
}

.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 25px; }

.loading-state { padding: 20px; text-align: center; color: #94a3b8; }
</style>
