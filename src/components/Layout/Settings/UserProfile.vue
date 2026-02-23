<script>
import { useAuthStore } from "@/stores/auth";
import { useNotificationsStore } from "@/stores/notifications";
import api from "@/services/api";

export default {
  name: "UserProfile",

  data() {
    return {
      // Крутится ли спиннер на кнопке сохранения
      isSaving: false,
      // Крутится ли спиннер на самой аватарке
      isAvatarUploading: false,

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
      // Если мы выходим из аккаунта, юзера уже может не быть, страхуемся от ошибок
      if (this.authStore.isLoggingOut || !this.authStore.user?.email) return '';

      // Берем первые две буквы от email и делаем их большими (например, ADmin -> AD)
      return this.authStore.user.email.substring(0, 2).toUpperCase();
    },

    // Эта вычисляемая штука проверяет, поменял ли пользователь что-то в форме
    // Мы используем её, чтобы заблокировать кнопку "Сохранить", если изменений нет
    hasChanges() {
      const user = this.authStore.user;
      if (!user) return false;

      const currentName = user.name || '';
      const currentSurname = user.surname || '';

      return this.form.name !== currentName || this.form.surname !== currentSurname;
    }
  },

  watch: {
    // Внимательно следим за данными пользователя в сторе.
    // Это нужно на случай, если при открытии страницы юзер еще не загрузился с бэкенда.
    // Как только данные появятся, мы сразу подставим их в форму.
    'authStore.user': {
      immediate: true, // Срабатывает сразу при создании компонента
      handler(newUser) {
        if (newUser) {
          this.form.email = newUser.email || '';
          this.form.name = newUser.name || '';
          this.form.surname = newUser.surname || '';
        }
      }
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
      // Имитируем клик по скрытому инпуту файла, когда юзер жмет на кружочек с аватаркой
      this.$refs.avatarInput.click();
    },

    async handleAvatarUpload(event) {
      const file = event.target.files[0];
      if (!file) return; // Если юзер открыл окно выбора файла и нажал "Отмена"

      this.isAvatarUploading = true;
      const formData = new FormData();
      formData.append('file', file);

      try {
        const userId = this.authStore.user.id;

        // Отправляем фотку на сервер
        await api.post(`/users/${userId}/photo`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        // Просим стор стянуть свежие данные пользователя (чтобы аватарка обновилась везде)
        await this.authStore.fetchUser();
        this.notify.success('Фотография успешно обновлена');
      } catch (e) {
        this.notify.error('Не удалось загрузить фотографию');
      } finally {
        this.isAvatarUploading = false;
        // Очищаем инпут, чтобы можно было загрузить тот же файл еще раз, если потребуется
        event.target.value = '';
      }
    },

    async saveProfile() {
      // Двойная защита: если ничего не изменилось, просто не даем отправить запрос
      if (!this.hasChanges) return;

      this.isSaving = true;
      try {
        const userId = this.authStore.user.id;

        const payload = {
          name: this.form.name,
          surname: this.form.surname,
        };

        // Отправляем изменения патчем (обновляем только то, что передали)
        await api.patch(`/users/${userId}`, payload);

        // Обновляем стор, чтобы новое имя загорелось в хедере и других местах
        await this.authStore.fetchUser();
        this.notify.success('Профиль успешно сохранен');
      } catch (e) {
        const errorMsg = e.response?.data?.detail || 'Не удалось сохранить изменения';
        this.notify.error(errorMsg);
        console.error('Ошибка сохранения профиля:', e);
      } finally {
        this.isSaving = false;
      }
    },

    async handleDeleteAvatar() {
      if (!confirm('Вы уверены, что хотите удалить фото профиля?')) return;

      try {
        const userId = this.authStore.user.id;
        await api.delete(`/users/${userId}/photo`);
        await this.authStore.fetchUser();
        this.notify.info('Фотография удалена');
      } catch (e) {
        this.notify.error('Произошла ошибка при удалении фото');
      }
    }
  }
};
</script>

<template>
  <div class="profile-card">
    <div class="card-header">
      <h2 class="section-title">Личная информация</h2>
      <p class="section-subtitle">Управляйте своими личными данными и фотографией профиля.</p>
    </div>

    <!-- Верхний блок с аватаркой и почтой -->
    <div class="profile-header">

      <div class="avatar-container">
        <!-- Сам кружок с фоткой (кликабельный) -->
        <div class="avatar-wrapper" @click="triggerAvatarUpload" :class="{ 'is-loading': isAvatarUploading }">

          <img v-if="userPhoto" :src="userPhoto" alt="Avatar" class="avatar-img">
          <div v-else class="avatar-placeholder">{{ userInitials }}</div>

          <!-- Темная плашка с иконкой фотика при наведении -->
          <div class="avatar-overlay">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>
          </div>

          <!-- Спиннер, который крутится, пока фотка летит на бэкенд -->
          <div v-if="isAvatarUploading" class="avatar-loading-overlay">
            <span class="spinner"></span>
          </div>
        </div>

        <!-- Кнопка удаления фотки (показываем только если фотка вообще есть) -->
        <button
            v-if="userPhoto && !isAvatarUploading"
            class="delete-avatar-btn"
            @click.stop="handleDeleteAvatar"
            title="Удалить фото"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      </div>

      <div class="profile-meta">
        <h3 class="user-email">{{ authStore.user?.email || 'Загрузка...' }}</h3>
        <span class="role-badge">{{ getRoleName(authStore.user?.role) }}</span>
      </div>

      <!-- Скрытый инпут, через который мы забираем файл из системы -->
      <input type="file" ref="avatarInput" accept="image/png, image/jpeg, image/webp" hidden @change="handleAvatarUpload">
    </div>

    <!-- Форма редактирования -->
    <form @submit.prevent="saveProfile" class="profile-form">

      <!-- Логин вынесли на всю ширину, так как его нельзя менять -->
      <div class="form-group full-width">
        <label>Email (Логин)</label>
        <div class="input-with-icon">
          <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
          <input type="email" v-model="form.email" disabled class="form-input disabled" title="Email нельзя изменить">
        </div>
      </div>

      <!-- Сетка в две колонки для имени и фамилии -->
      <div class="form-row">
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
        <!-- Кнопка выключается, если идет сохранение или если пользователь ничего не поменял -->
        <button type="submit" class="btn-save" :disabled="isSaving || !hasChanges">
          <span v-if="isSaving" class="spinner button-spinner"></span>
          {{ isSaving ? 'Сохранение...' : 'Сохранить изменения' }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped>
/* --- Базовая карточка --- */
.profile-card {
  background: #ffffff;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.03);
  width: 100%;
  box-sizing: border-box;
  font-family: system-ui, -apple-system, sans-serif;
  color: #0f172a;
}

.card-header { margin-bottom: 28px; }
.section-title { margin: 0 0 6px 0; font-size: 20px; font-weight: 600; }
.section-subtitle { margin: 0; font-size: 14px; color: #64748b; }

/* --- Блок с аватаром и инфой --- */
.profile-header {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 32px;
  padding-bottom: 32px;
  border-bottom: 1px solid #f1f5f9;
}

.avatar-container {
  position: relative;
  width: 88px;
  height: 88px;
  flex-shrink: 0;
}

.avatar-wrapper {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  overflow: hidden;
  position: relative;
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
  border: 3px solid #ffffff;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.avatar-wrapper:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0,0,0,0.1);
}

.avatar-wrapper.is-loading {
  pointer-events: none;
  opacity: 0.8;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  font-size: 28px;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 1px;
}

/* Плашка, которая выезжает при наведении на фотку */
.avatar-overlay {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  transition: opacity 0.2s ease;
}
.avatar-overlay svg { width: 28px; height: 28px; }
.avatar-wrapper:hover .avatar-overlay { opacity: 1; }

/* Затемнение и спиннер на момент загрузки фотки */
.avatar-loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}

/* Маленькая красная кнопка для удаления фотки */
.delete-avatar-btn {
  position: absolute;
  bottom: 0;
  right: -4px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  color: #ef4444;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: all 0.2s ease;
  z-index: 10;
  padding: 0;
}
.delete-avatar-btn svg { width: 14px; height: 14px; }
.delete-avatar-btn:hover {
  background-color: #fee2e2;
  border-color: #fecaca;
  color: #dc2626;
  transform: scale(1.1);
}

.profile-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-start;
}
.user-email { margin: 0; font-size: 18px; font-weight: 600; color: #0f172a; word-break: break-all; }
.role-badge {
  background: #eff6ff; color: #2563eb;
  padding: 4px 10px; border-radius: 6px;
  font-size: 12px; font-weight: 600;
  display: inline-block;
}

/* --- Форма --- */
.profile-form { display: flex; flex-direction: column; gap: 20px; }

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.form-group { display: flex; flex-direction: column; gap: 8px; }
.form-group label { font-size: 13px; font-weight: 600; color: #475569; }

.input-with-icon { position: relative; display: flex; align-items: center; }
.input-icon {
  position: absolute; left: 12px;
  width: 16px; height: 16px; color: #94a3b8;
}

.form-input {
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

.input-with-icon .form-input { padding-left: 36px; }

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.form-input.disabled {
  background: #f8fafc; color: #64748b;
  border-color: #e2e8f0; cursor: not-allowed;
}

/* --- Кнопка Сохранить --- */
.form-actions { margin-top: 12px; }

.btn-save {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  background: #0f172a; color: white; border: none;
  padding: 12px 24px; border-radius: 8px; font-size: 14px; font-weight: 500;
  cursor: pointer; transition: all 0.2s ease;
}
.btn-save:hover:not(:disabled) { background: #334155; transform: translateY(-1px); }
.btn-save:active:not(:disabled) { transform: translateY(0); }
.btn-save:disabled { background: #94a3b8; cursor: not-allowed; opacity: 0.8; }

/* --- Крутилка-спиннер --- */
.spinner {
  width: 24px; height: 24px;
  border: 3px solid rgba(59, 130, 246, 0.3);
  border-radius: 50%;
  border-top-color: #3b82f6;
  animation: spin 0.8s linear infinite;
}
.button-spinner {
  width: 16px; height: 16px; border-width: 2px;
  border-color: rgba(255, 255, 255, 0.3); border-top-color: white;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* --- Адаптив --- */
@media (max-width: 480px) {
  .profile-card { padding: 24px; }
  .form-row { grid-template-columns: 1fr; gap: 20px; }
  .profile-header { flex-direction: column; text-align: center; gap: 16px; align-items: center; }
  .profile-meta { align-items: center; }
  .btn-save { width: 100%; }
}
</style>
