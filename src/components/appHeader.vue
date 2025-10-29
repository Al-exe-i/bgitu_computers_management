<script>
import { useAuthStore } from '@/stores/auth'
import router from "@/router/index.js";

export default {
  name: 'appHeader',
  data() {
    return {
      isDropdownOpen: false,
      officeOneActive: false,
      officeTwoActive: false,
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
      return this.authStore.user?.photo || `/src/assets/User_no_icon.svg`
    },
    userAvatarLarge() {
      return this.authStore.user?.photo || `/src/assets/User_no_icon.svg`
    }
  },

  methods: {
    openLoginModal()
    {
      this.$emit('open-login')
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
    },
    handleOfficeActive(officeNumber)
    {
      if(officeNumber)
      {
        if(officeNumber === 1)
        {
          this.officeOneActive = true
          this.officeTwoActive = false
        }
        if(officeNumber === 2)
        {
          this.officeOneActive = false
          this.officeTwoActive = true
        }
      }
    }
  },
  watch: {
    '$route' (to, from)
    {
      let officeNumber = Number(to?.params?.officeNumber)
      this.handleOfficeActive(officeNumber)
      if(to.name !== 'Office')
      {
        this.officeOneActive = this.officeTwoActive = false
      }
    }
  },
  mounted() {
    document.addEventListener('click', this.handleClickOutside)
    if(this.$route.name === 'Office')
    {
      this.handleOfficeActive(Number(this.$route?.params.officeNumber))
    }
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
        <button @click="handleOfficeClick(1)" class="floor-btn" :class="{active: this.officeOneActive}">1 корпус</button>
        <button @click="handleOfficeClick(2)" class="floor-btn" :class="{active: this.officeTwoActive}">2 корпус</button>
      </div>

      <!-- Профиль или кнопка авторизации -->
      <div class="auth-container">
        <!-- Если авторизованы -->
        <div v-if="authStore.isAuthenticated" class="profile-dropdown">
          <div class="profile-trigger" @click="toggleDropdown">
            <img
                :src="userAvatar"
                alt="Профиль"
                class="profile-img"
            >
            <span class="profile-name">{{ userName }}</span>
          </div>
          <div v-show="isDropdownOpen" class="profile-dropdown-content">
            <div class="profile-dropdown-content-inner">
              <img
                  :src="userAvatarLarge"
                  alt="Профиль"
                  class="profile-avatar-large"
              >
              <h3 class="profile-fullname">{{ userFullName }}</h3>
              <p class="profile-email">{{ userEmail }}</p>
            </div>
            <div class="border-t pt-3">
              <button @click="handleLogout" class="logout-btn">
                Выйти
              </button>
            </div>
          </div>
        </div>

        <!-- Если не авторизованы -->
        <button
            v-else
            @click="openLoginModal"
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
  -webkit-transition: -webkit-transform .8s ease-in-out;
  transition: transform .8s ease-in-out;
}

.logo:hover
{
  -webkit-transform: rotate(360deg);
  transform: rotate(360deg);
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
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.3s ease;
  color: #4b5563;
  background: transparent;
}

.floor-btn.active {
  background: white;
  color: #3b82f6;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.floor-btn:not(.active):hover {
  color: #1f2937;
}

.floor-switch {
  display: flex;
  gap: 8px;
  background: #f3f4f6;
  padding: 4px;
  border-radius: 10px;
}

.auth-container {
  display: flex;
  align-items: center;
  flex: 1;
}

.login-btn {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  padding: 10px 24px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 15px;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  margin-left: auto;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
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
  top: 65px;
  background: white;
  min-width: 280px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.15);
  border-radius: 12px;
  padding: 15px;
  z-index: 100;
  animation: fadeIn 0.5s linear;
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
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: background 0.3s ease;
}

.logout-btn:hover {
  background: #dc2626;
  transform: translateY(-2px);
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

  .floor-btn
  {
    font-size: 14px;
    padding: 9px 9px;
  }

  .profile-name
  {
    display: none;
  }
}
</style>