<script>
import { useAuthStore } from "@/stores/auth";
import { useNotificationsStore } from "@/stores/notifications";
import api from "@/services/api";

export default {
  name: "UserProfile",
  data() {
    return {
      loading: false,
      form: {
        email: '',
        name: '',
        surname: ''
      }
    };
  },
  computed: {
    authStore() {
      return useAuthStore();
    },

    notify() {
      return useNotificationsStore();
    },

    userPhoto() {
      return this.authStore.user?.photo;
    },

    userInitials() {
      if(!this.authStore.isLoggingOut)
      {
        const email = this.authStore.user?.email;
        return email.substring(0, 2).toUpperCase();
      }
    }
  },
  mounted() {
    // Заполняем форму данными из стора при загрузке
    if (this.authStore.user) {
      this.form.email = this.authStore.user.email;
      this.form.name = this.authStore.user.name || '';
      this.form.surname = this.authStore.user.surname || '';
    }
  },
  methods: {
    getRoleName(role) {
      if (this.authStore.user?.is_superuser) return 'Суперпользователь';
      if (role === 1) return 'Администратор';
      if (role === 2) return 'Преподаватель';
      return 'Пользователь';
    },

    triggerAvatarUpload() {
      this.$refs.avatarInput.click();
    },

    async handleAvatarUpload(event) {
      const file = event.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('file', file);

      try
      {
        const userId = this.authStore.user.id;

        await api.post(`/users/${userId}/photo`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        await this.authStore.fetchUser();
        this.notify.success('Фотография обновлена');
      } catch (e)
      {
        this.notify.error('Не удалось загрузить фото');
      }
    },

    async saveProfile() {
      this.loading = true;
      try {
        const userId = this.authStore.user.id;

        // Формируем payload только из текстовых полей
        const payload = {
          name: this.form.name,
          surname: this.form.surname,
        };

        await api.patch(`/users/${userId}`, payload);

        // Обновляем данные в сторе, чтобы имя обновилось в интерфейсе
        await this.authStore.fetchUser();

        this.notify.success('Профиль сохранен');
      }
      catch (e)
      {
        this.notify.error('Ошибка сохранения');
        console.error(e.response?.data?.detail || 'Неизвестная ошибка');
      }
      finally
      {
        this.loading = false;
      }
    },

    async handleDeleteAvatar() {
      try
      {
        const userId = this.authStore.user.id;

        await api.delete(`/users/${userId}/photo`);

        await this.authStore.fetchUser();

        this.notify.info('Фото удалено');
      }
      catch (e)
      {
        this.notify.error('Ошибка при удалении фото');
      }
    }
  }
};
</script>

<template>
  <div class="profile-card">
    <h2 class="section-title">Личная информация</h2>

    <div class="profile-header">
      <!-- Обертка аватара -->
      <div class="avatar-container">

        <!-- аватар (клик открывает загрузку) -->
        <div class="avatar-wrapper" @click="triggerAvatarUpload">
          <img v-if="userPhoto" :src="userPhoto" alt="Avatar" class="avatar-img">
          <div v-else class="avatar-placeholder">{{ userInitials }}</div>

          <!-- Оверлей загрузки -->
          <div class="avatar-overlay">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>
          </div>
        </div>

        <button
            v-if="userPhoto"
            class="delete-avatar-btn"
            @click.stop="handleDeleteAvatar"
            title="Удалить фото"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>

      </div>

      <div class="profile-meta">
        <h3>{{ authStore.user?.email }}</h3>
        <p class="role-badge">{{ getRoleName(authStore.user?.role) }}</p>
      </div>

      <input type="file" ref="avatarInput" accept="image/*" hidden @change="handleAvatarUpload">
    </div>

    <form @submit.prevent="saveProfile" class="profile-form">
      <div class="form-grid">
        <div class="form-group">
          <label>Email (Логин)</label>
          <input type="email" v-model="form.email" disabled class="form-input disabled" title="Email нельзя изменить">
        </div>

        <div class="form-group">
          <label>Имя</label>
          <input type="text" v-model="form.name" class="form-input" placeholder="Введите имя">
        </div>

        <div class="form-group">
          <label>Фамилия</label>
          <input type="text" v-model="form.surname" class="form-input" placeholder="Введите фамилию">
        </div>
      </div>

      <div class="form-actions">
        <button type="submit" class="save-btn" :disabled="loading">
          {{ loading ? 'Сохранение...' : 'Сохранить изменения' }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.profile-card {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.section-title {
  font-size: 18px;
  margin-bottom: 24px;
  color: #0f172a;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
  padding-bottom: 30px;
  border-bottom: 1px solid #e2e8f0;
}

.avatar-container {
  position: relative;
  width: 80px;
  height: 80px;
}

.avatar-wrapper {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  position: relative;
  cursor: pointer;
  overflow: hidden;
  background: #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid white;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.delete-avatar-btn {
  position: absolute;
  bottom: 0;
  right: -5px;

  width: 28px;
  height: 28px;
  border-radius: 50%;

  background-color: white;
  border: 1px solid #e2e8f0;
  color: #ef4444;

  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;

  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: all 0.2s ease;
  z-index: 10;
}

.delete-avatar-btn:hover {
  background-color: #fee2e2;
  border-color: #fecaca;
  transform: scale(1.1);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  font-size: 24px;
  font-weight: bold;
  color: #475569;
}

.avatar-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  transition: opacity 0.2s;
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}

.profile-meta h3 {
  margin: 0 0 5px 0;
  font-size: 18px;
}

.role-badge {
  display: inline-block;
  background: #e0f2fe;
  color: #0284c7;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  margin: 0;
}

.form-grid {
  display: grid;
  gap: 20px;
  max-width: 500px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
}

.form-input {
  padding: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
}
.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}
.form-input.disabled {
  background: #f1f5f9;
  color: #94a3b8;
  cursor: not-allowed;
}

.form-actions {
  margin-top: 30px;
}

.save-btn {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}
.save-btn:hover { background: #2563eb; }
.save-btn:disabled { background: #94a3b8; cursor: not-allowed; }
</style>
