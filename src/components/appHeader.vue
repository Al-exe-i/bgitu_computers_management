<script>
import { useAuthStore } from '@/stores/auth'
import router from "@/router/index.js";

export default {
  name: 'appHeader',
  data() {
    return {
      isDropdownOpen: false
    }
  },

  computed: {
    authStore()
    {
      return useAuthStore()
    },
    // Данные пользователя
    userName()
    {
      const user = this.authStore.user
      if (!user) return 'Гость'
      return user.name || user.email.split('@')[0] || 'Пользователь'
    },
    userFullName()
    {
      const user = this.authStore.user
      if (!user) return ''
      return `${user.name || ''} ${user.surname || ''}`.trim() || user.email
    },
    userEmail()
    {
      return this.authStore.user?.email || ''
    },
    userAvatar()
    {
      // Если есть фото — используем его, иначе placeholder
      return this.authStore.user?.photo || 'https://placehold.co/40x40'
    },
    userAvatarLarge() {
      return this.authStore.user?.photo || 'https://placehold.co/120x120'
    }
  },

  methods: {
    openLoginModal()
    {
      this.$emit('open-login') // или вызови метод, который открывает твою модалку
    },
    handleLogout()
    {
      this.authStore.logout()
      this.isDropdownOpen = false
      router.push('/')
    },
    toggleDropdown()
    {
      this.isDropdownOpen = !this.isDropdownOpen
    },
    // Закрываем дропдаун при клике вне его
    handleClickOutside(event)
    {
      if (!event.target.closest('.profile-dropdown'))
      {
        this.isDropdownOpen = false
      }
    },
    handleHomeClick()
    {
      router.push('/')
    },
    handleOfficeClick(officeNumber)
    {
      router.push({
        name: 'Office',
        params: { officeNumber: officeNumber }
      })
    }
  },
  mounted() {
    document.addEventListener('click', this.handleClickOutside)
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleClickOutside)
  }
}
</script>

<template>
  <header>
    <div class="header-container">
      <!-- Логотип -->
      <div @click="handleHomeClick" class="logo-container">
        <div class="logo">
          <img src="../assets/logo_IT.png">
        </div>
        <h1 class="app-title">Computers management</h1>
      </div>

      <!-- Переключение между этажами -->
      <div class="floor-switch">
      <!-- Добавить класс active, чтобы был выбран корпус-->
        <button @click="handleOfficeClick(1)" id="floor1Btn" class="floor-btn">1 корпус</button>
        <button @click="handleOfficeClick(2)" id="floor2Btn" class="floor-btn">2 корпус</button>
      </div>

      <!-- Профиль или кнопка авторизации -->
      <div class="auth-container">
        <!-- Если авторизованы -->
        <div v-if="authStore.isAuthenticated" class="profile-dropdown" id="profileSection">
          <div class="profile-trigger" @click="toggleDropdown">
            <img
                :src="userAvatar"
                alt="Профиль"
                class="profile-img"
            >
            <span class="profile-name" id="userName">{{ userName }}</span>
          </div>
          <div v-show="isDropdownOpen" class="profile-dropdown-content">
            <div class="profile-dropdown-content-inner">
              <img
                  :src="userAvatarLarge"
                  alt="Профиль"
                  class="profile-avatar-large"
              >
              <h3 class="profile-fullname" id="userFullName">{{ userFullName }}</h3>
              <p class="profile-email" id="userEmail">{{ userEmail }}</p>
            </div>
            <div class="border-t pt-3">
              <button @click="handleLogout" id="logoutBtn" class="logout-btn">
                Выйти
              </button>
            </div>
          </div>
        </div>

        <!-- Если не авторизованы -->
        <button
            v-else
            @click="openLoginModal"
            id="loginBtn"
            class="login-btn"
        >
          Войти
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
header {
  background: white;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  position: sticky;
  top: 0;
  z-index: 40;
}

.header-container
{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
}

.logo-container {
  display: flex;
  align-items: center;
  flex: 1;
}

.logo-container:hover
{
  cursor: pointer;
}

.logo {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
}

.logo img
{
  width: 100%;
  height: 100%;
}

.app-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.floor-btn {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.3s ease;
}

.floor-btn.active {
  background: #3b82f6;
  color: white;
}

.floor-btn:not(.active) {
  background: #f3f4f6;
  color: #4b5563;
}

.floor-btn:not(.active):hover {
  background: #e5e7eb;
}

.floor-switch
{
  display: flex;
  gap: 8px;
  justify-content: center;
  flex: 1;
}

.auth-container {
  display: flex;
  align-items: center;
  flex: 1;
}

.login-btn {
  background: #3b82f6;
  color: white;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: background 0.3s ease;
  margin-left: auto;
}

.login-btn:hover {
  background: #2563eb;
}

.profile-dropdown
{
  position: relative;
  margin-left: auto;
}

.profile-trigger {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.profile-img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid #dbeafe;
}

.profile-name {
  margin-left: 8px;
  font-weight: 500;
  color: #1f2937;
}

.profile-dropdown-content
{
  position: absolute;
  right: 0;
  top: 60px;
  background: white;
  min-width: 200px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.15);
  border-radius: 10px;
  padding: 15px;
  z-index: 100;
  animation: fadeIn 0.3s;
}

.profile-dropdown-content-inner
{
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 1rem;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.profile-avatar-large {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  border: 4px solid #dbeafe;
  margin-bottom: 12px;
}

.profile-fullname {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  text-align: center;
  margin-bottom: 4px;
}

.profile-email {
  font-size: 14px;
  color: #6b7280;
  text-align: center;
  margin-bottom: 16px;
}

.logout-btn {
  width: 100%;
  background: #ef4444;
  color: white;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: background 0.3s ease;
}

.logout-btn:hover {
  background: #dc2626;
}

@media (max-width: 768px)
{
  .app-title
  {
    display: none;
  }

  .floor-switch
  {
    margin-right: 0;
  }
}
</style>