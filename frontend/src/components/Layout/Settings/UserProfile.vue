<script>
import { useAuthStore } from "@/stores/auth";
import { useNotificationsStore } from "@/stores/notifications";
import api from "@/services/api";
import RealtimeNotificationsSection from "@/components/Layout/Settings/RealtimeNotificationsSection.vue";

export default {
  name: "UserProfile",

  components: {
    RealtimeNotificationsSection
  },

  data() {
    return {
      activeSection: "profile",
      notificationsSectionMounted: false,
      isSaving: false,
      isAvatarUploading: false,
      form: {
        email: "",
        name: "",
        surname: ""
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
      if (this.authStore.isLoggingOut || !this.authStore.user?.email) return "";
      return this.authStore.user.email.substring(0, 2).toUpperCase();
    },

    hasChanges() {
      const user = this.authStore.user;
      if (!user) return false;

      const currentName = user.name || "";
      const currentSurname = user.surname || "";

      return this.form.name !== currentName || this.form.surname !== currentSurname;
    },

    activeSectionTitle() {
      return this.activeSection === "notifications" ? "Уведомления" : "Личная информация";
    },

    activeSectionSubtitle() {
      return this.activeSection === "notifications"
        ? "Настройте realtime-подписки на события системы."
        : "Управляйте своими личными данными и фотографией профиля.";
    }
  },

  watch: {
    "authStore.user": {
      immediate: true,
      handler(newUser) {
        if (!newUser) return;

        this.form.email = newUser.email || "";
        this.form.name = newUser.name || "";
        this.form.surname = newUser.surname || "";
      }
    },

    "$route.query.section": {
      immediate: true,
      handler(section) {
        if (section === "notifications") {
          this.switchSection("notifications");
        }
      }
    }
  },

  methods: {
    getRoleName(role) {
      if (this.authStore.user?.is_superuser) return "Суперпользователь";
      if (role === 1) return "Администратор";
      if (role === 2) return "Преподаватель";
      return "Пользователь";
    },

    switchSection(section) {
      this.activeSection = section;

      if (section === "notifications") {
        this.notificationsSectionMounted = true;
      }
    },

    triggerAvatarUpload() {
      this.$refs.avatarInput.click();
    },

    async handleAvatarUpload(event) {
      const file = event.target.files[0];
      if (!file) return;

      this.isAvatarUploading = true;
      const formData = new FormData();
      formData.append("file", file);

      try {
        const userId = this.authStore.user.id;

        await api.post(`/users/${userId}/photo`, formData, {
          headers: { "Content-Type": "multipart/form-data" }
        });

        await this.authStore.fetchUser();
        this.notify.success("Фотография успешно обновлена");
      } catch (error) {
        this.notify.error("Не удалось загрузить фотографию");
      } finally {
        this.isAvatarUploading = false;
        event.target.value = "";
      }
    },

    async saveProfile() {
      if (!this.hasChanges) return;

      this.isSaving = true;

      try {
        const userId = this.authStore.user.id;

        await api.patch(`/users/${userId}`, {
          name: this.form.name,
          surname: this.form.surname
        });

        await this.authStore.fetchUser();
        this.notify.success("Профиль успешно сохранён");
      } catch (error) {
        const errorMessage = error.response?.data?.detail || "Не удалось сохранить изменения";
        this.notify.error(errorMessage);
        console.error("Ошибка сохранения профиля:", error);
      } finally {
        this.isSaving = false;
      }
    },

    async handleDeleteAvatar() {
      if (!confirm("Вы уверены, что хотите удалить фото профиля?")) return;

      try {
        const userId = this.authStore.user.id;
        await api.delete(`/users/${userId}/photo`);
        await this.authStore.fetchUser();
        this.notify.info("Фотография удалена");
      } catch (error) {
        this.notify.error("Произошла ошибка при удалении фото");
      }
    }
  }
};
</script>

<template>
  <div class="profile-card">
    <div class="card-header">
      <div class="card-heading">
        <h2 class="section-title">{{ activeSectionTitle }}</h2>
      </div>

      <div class="profile-section-switch" role="tablist" aria-label="Разделы профиля">
        <span
          class="profile-section-indicator"
          :class="{ 'is-notifications': activeSection === 'notifications' }"
          aria-hidden="true"
        ></span>

        <button
          type="button"
          class="profile-section-btn"
          :class="{ active: activeSection === 'profile' }"
          :aria-selected="activeSection === 'profile'"
          aria-controls="profile-section-panel"
          role="tab"
          @click="switchSection('profile')"
        >
          <span class="profile-section-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21a8 8 0 0 0-16 0"></path>
              <circle cx="12" cy="8" r="4"></circle>
            </svg>
          </span>
          <span>Профиль</span>
        </button>

        <button
          type="button"
          class="profile-section-btn"
          :class="{ active: activeSection === 'notifications' }"
          :aria-selected="activeSection === 'notifications'"
          aria-controls="notifications-section-panel"
          role="tab"
          @click="switchSection('notifications')"
        >
          <span class="profile-section-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 8a6 6 0 0 0-12 0c0 7-3 8-3 8h18s-3-1-3-8"></path>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
            </svg>
          </span>
          <span>Уведомления</span>
        </button>
      </div>

      <p class="section-subtitle card-subtitle">{{ activeSectionSubtitle }}</p>
    </div>

    <div class="profile-content-stage">
      <transition name="profile-panel-shift">
        <section
          v-show="activeSection === 'profile'"
          id="profile-section-panel"
          class="profile-panel"
          role="tabpanel"
        >
          <div class="profile-header">
            <div class="avatar-container">
              <div
                class="avatar-wrapper"
                :class="{ 'is-loading': isAvatarUploading }"
                @click="triggerAvatarUpload"
              >
                <img v-if="userPhoto" :src="userPhoto" alt="Avatar" class="avatar-img">
                <div v-else class="avatar-placeholder">{{ userInitials }}</div>

                <div class="avatar-overlay">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                    <circle cx="12" cy="13" r="4"></circle>
                  </svg>
                </div>

                <div v-if="isAvatarUploading" class="avatar-loading-overlay">
                  <span class="spinner"></span>
                </div>
              </div>

              <button
                v-if="userPhoto && !isAvatarUploading"
                class="delete-avatar-btn"
                title="Удалить фото"
                @click.stop="handleDeleteAvatar"
              >
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </div>

            <div class="profile-meta">
              <h3 class="user-email">{{ authStore.user?.email || "Загрузка..." }}</h3>
              <span class="role-badge">{{ getRoleName(authStore.user?.role) }}</span>
            </div>

            <input
              ref="avatarInput"
              type="file"
              accept="image/png, image/jpeg, image/webp"
              hidden
              @change="handleAvatarUpload"
            >
          </div>

          <form class="profile-form" @submit.prevent="saveProfile">
            <div class="form-group full-width">
              <label>Email (логин)</label>
              <div class="input-with-icon">
                <svg
                  class="input-icon"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                </svg>
                <input
                  v-model="form.email"
                  type="email"
                  class="form-input disabled"
                  disabled
                  title="Email нельзя изменить"
                >
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Имя</label>
                <input
                  v-model="form.name"
                  type="text"
                  class="form-input"
                  placeholder="Введите имя"
                >
              </div>

              <div class="form-group">
                <label>Фамилия</label>
                <input
                  v-model="form.surname"
                  type="text"
                  class="form-input"
                  placeholder="Введите фамилию"
                >
              </div>
            </div>

            <div class="form-actions">
              <button type="submit" class="btn-save" :disabled="isSaving || !hasChanges">
                <span v-if="isSaving" class="spinner button-spinner"></span>
                {{ isSaving ? "Сохранение..." : "Сохранить изменения" }}
              </button>
            </div>
          </form>
        </section>
      </transition>

      <transition name="profile-panel-shift">
        <section
          v-if="notificationsSectionMounted"
          v-show="activeSection === 'notifications'"
          id="notifications-section-panel"
          class="profile-panel"
          role="tabpanel"
        >
          <RealtimeNotificationsSection :show-header="false" />
        </section>
      </transition>
    </div>
  </div>
</template>

<style scoped>
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

.card-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px 18px;
  margin-bottom: 28px;
}

.card-heading {
  min-width: 0;
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
  line-height: 1.5;
}

.card-subtitle {
  grid-column: 1 / -1;
  max-width: 760px;
}

.profile-section-switch {
  position: relative;
  justify-self: end;
  display: grid;
  grid-template-columns: repeat(2, minmax(118px, 1fr));
  align-items: center;
  gap: 4px;
  padding: 4px;
  border-radius: 18px;
  background:
    radial-gradient(circle at 10% 0%, rgba(59, 130, 246, 0.12), transparent 34%),
    linear-gradient(180deg, #f8fafc, #eef4fb);
  border: 1px solid rgba(203, 213, 225, 0.82);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.88),
    0 12px 28px rgba(15, 23, 42, 0.06);
  isolation: isolate;
  overflow: hidden;
}

.profile-section-indicator {
  position: absolute;
  top: 4px;
  bottom: 4px;
  left: 4px;
  width: calc((100% - 8px) / 2);
  border-radius: 14px;
  background:
    linear-gradient(135deg, #1e293b 0%, #2563eb 58%, #0ea5e9 100%);
  box-shadow:
    0 12px 24px rgba(37, 99, 235, 0.26),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  transform: translateX(0);
  transition:
    transform 0.38s cubic-bezier(0.22, 1, 0.36, 1),
    background 0.24s ease,
    box-shadow 0.24s ease;
  z-index: 0;
}

.profile-section-indicator.is-notifications {
  transform: translateX(100%);
}

.profile-section-btn {
  position: relative;
  z-index: 1;
  min-height: 42px;
  padding: 0 15px;
  border: none;
  border-radius: 14px;
  background: transparent;
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  white-space: nowrap;
  transition:
    color 0.22s ease,
    transform 0.22s ease;
}

.profile-section-icon {
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: currentColor;
}

.profile-section-icon svg {
  width: 100%;
  height: 100%;
}

.profile-section-btn:hover {
  color: #334155;
  transform: translateY(-1px);
}

.profile-section-btn.active {
  color: #ffffff;
}

.profile-section-btn.active:hover {
  color: #ffffff;
}

.profile-content-stage {
  display: grid;
  min-width: 0;
}

.profile-panel-shift-enter-active,
.profile-panel-shift-leave-active {
  transition:
    opacity 0.22s ease,
    transform 0.22s ease;
}

.profile-panel-shift-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.profile-panel-shift-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.profile-panel {
  grid-area: 1 / 1;
  min-width: 0;
}

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
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 3px solid #ffffff;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.avatar-wrapper:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
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

.avatar-overlay svg {
  width: 28px;
  height: 28px;
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}

.avatar-loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}

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
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
  z-index: 10;
  padding: 0;
}

.delete-avatar-btn svg {
  width: 14px;
  height: 14px;
}

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

.user-email {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  word-break: break-all;
}

.role-badge {
  background: #eff6ff;
  color: #2563eb;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  display: inline-block;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
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

.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 12px;
  width: 16px;
  height: 16px;
  color: #94a3b8;
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

.input-with-icon .form-input {
  padding-left: 36px;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.form-input.disabled {
  background: #f8fafc;
  color: #64748b;
  border-color: #e2e8f0;
  cursor: not-allowed;
}

.form-actions {
  margin-top: 12px;
}

.btn-save {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: #0f172a;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-save:hover:not(:disabled) {
  background: #334155;
  transform: translateY(-1px);
}

.btn-save:active:not(:disabled) {
  transform: translateY(0);
}

.btn-save:disabled {
  background: #94a3b8;
  cursor: not-allowed;
  opacity: 0.8;
}

:global(html[data-theme='dark'] .profile-card) {
  background: rgba(15, 23, 42, 0.96) !important;
  border: 1px solid #334155 !important;
  color: #e2e8f0 !important;
  box-shadow: 0 24px 54px rgba(2, 6, 23, 0.34) !important;
}

:global(html[data-theme='dark'] .profile-card .section-title) {
  color: #f8fafc !important;
}

:global(html[data-theme='dark'] .profile-card .section-subtitle),
:global(html[data-theme='dark'] .profile-card .card-subtitle) {
  color: #94a3b8 !important;
}

:global(html[data-theme='dark'] .profile-card .btn-save:not(:disabled)) {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  border: 1px solid #2563eb;
  color: #e2e8f0;
  box-shadow: 0 8px 18px rgba(37, 99, 235, 0.3);
}

:global(html[data-theme='dark'] .profile-card .btn-save:hover:not(:disabled)) {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  border-color: #3b82f6;
}

:global(html[data-theme='dark'] .profile-card .btn-save:disabled) {
  background: #334155;
  border: 1px solid #475569;
  color: #94a3b8;
  box-shadow: none;
}

:global(html[data-theme='dark'] .profile-card .profile-section-switch) {
  background:
    radial-gradient(circle at 10% 0%, rgba(14, 165, 233, 0.12), transparent 34%),
    linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(2, 6, 23, 0.94));
  border-color: rgba(51, 65, 85, 0.9);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 16px 32px rgba(2, 6, 23, 0.28);
}

:global(html[data-theme='dark'] .profile-card .profile-section-indicator) {
  background:
    linear-gradient(135deg, #1d4ed8 0%, #2563eb 58%, #0891b2 100%);
  box-shadow:
    0 14px 26px rgba(37, 99, 235, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

:global(html[data-theme='dark'] .profile-card .profile-section-btn) {
  color: #94a3b8;
}

:global(html[data-theme='dark'] .profile-card .profile-section-btn:hover) {
  color: #cbd5e1;
}

:global(html[data-theme='dark'] .profile-card .profile-section-btn.active) {
  color: #f8fafc;
}

:global(html[data-theme='dark'] .profile-card .profile-section-btn.active:hover) {
  color: #f8fafc;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(59, 130, 246, 0.3);
  border-radius: 50%;
  border-top-color: #3b82f6;
  animation: spin 0.8s linear infinite;
}

.button-spinner {
  width: 16px;
  height: 16px;
  border-width: 2px;
  border-color: rgba(255, 255, 255, 0.3);
  border-top-color: white;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 480px) {
  .profile-card {
    padding: 20px;
  }

  .card-header {
    grid-template-columns: 1fr;
    align-items: stretch;
    gap: 14px;
    margin-bottom: 22px;
  }

  .profile-section-switch {
    width: 100%;
    justify-self: stretch;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    padding: 3px;
    border-radius: 16px;
  }

  .profile-section-indicator {
    top: 3px;
    bottom: 3px;
    left: 3px;
    width: calc((100% - 6px) / 2);
    border-radius: 13px;
  }

  .profile-section-btn {
    min-height: 38px;
    padding: 0 8px;
    gap: 6px;
    font-size: 12px;
    border-radius: 13px;
  }

  .profile-section-icon {
    width: 16px;
    height: 16px;
  }

  .section-subtitle {
    font-size: 13px;
  }

  .form-row {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .profile-header {
    flex-direction: column;
    text-align: center;
    gap: 16px;
    align-items: center;
  }

  .profile-meta {
    align-items: center;
  }

  .btn-save {
    width: 100%;
  }
}
</style>
