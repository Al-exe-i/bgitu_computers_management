<script>
import { useAuthStore } from '@/stores/auth.js'
import router from "@/router/index.js";
import {useAudienceContext} from "@/stores/officeCtx.js";

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
    audienceContext()
    {
      return useAudienceContext()
    },
    // Данные пользователя
    userName()
    {
      const user = this.authStore.user
      if (!user) return 'Гость'
      return user.name || user.email.split('@')[0] || 'Пользователь'
    },
    userEmail()
    {
      return this.authStore.user?.email || ''
    },
    userRole()
    {
      switch (this.authStore.user?.role)
      {
        case 1:
          return `Админ`
        case 2:
          return `Преподаватель`
      }
    },
    userRoleNum()
    {
      return this.authStore.user?.role
    },
    userAvatar()
    {
      return this.authStore.user?.photo || null
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
      if(to.name !== 'Office' && to.name !== 'Audience')
      {
        this.officeOneActive = this.officeTwoActive = false
      }
    },
    'audienceContext.officeId' (newId, oldId)
    {
      if (newId)
      {
        this.handleOfficeActive(newId)
      }
    }
  },
  mounted() {
    document.addEventListener('click', this.handleClickOutside)
    let officeNumber = Number(this.$route?.params.officeNumber) | this.audienceContext.officeId
    if(this.$route.name === 'Office' || this.$route.name === 'Audience')
    {
      this.handleOfficeActive(officeNumber)
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
          <img src="../../assets/logo_IT.png">
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
                v-if="userAvatar"
                :src="userAvatar"
                alt="Профиль"
                class="profile-img"
            >
            <div class="profile-no-icon" v-else>{{ userName[0].toUpperCase() }}</div>
            <span class="profile-name">{{ userName }}</span>
          </div>
          <div v-show="isDropdownOpen" class="profile-dropdown-content">
            <div class="profile-dropdown-content-inner">
              <img
                  :src="userAvatarLarge"
                  alt="Профиль"
                  class="profile-avatar-large"
              >
              <h3 class="profile-fullname">{{ userEmail }}</h3>
              <div class="role-badge">
                <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 48 48"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" d="M33.07 19.51L28 23.2l2 5.93a.57.57 0 0 1-.87.63L24 26.15l-5.08 3.7a.56.56 0 0 1-.79-.15a.62.62 0 0 1-.08-.48L20 23.3l-5.07-3.7a.55.55 0 0 1 .32-1h6.27l1.95-5.93a.55.55 0 0 1 1.06-.09l1.95 5.92h6.27a.56.56 0 0 1 .55.57a.53.53 0 0 1-.23.44"/><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" d="M24 4.5s-11.26 2-15.25 2v20a11.2 11.2 0 0 0 .8 4.1a15 15 0 0 0 2 3.61a22 22 0 0 0 2.81 3.07a35 35 0 0 0 3 2.48a34 34 0 0 0 2.89 1.86c1 .59 1.71 1 2.13 1.19l1 .49a1.44 1.44 0 0 0 1.24 0l1-.49c.42-.2 1.13-.6 2.13-1.19a34 34 0 0 0 2.89-1.86a35 35 0 0 0 3-2.48a22 22 0 0 0 2.81-3.07a15 15 0 0 0 2-3.61a11.2 11.2 0 0 0 .8-4.1v-20c-3.99.03-15.25-2-15.25-2"/></svg>
                <span>{{ userRole }}</span>
              </div>
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
  padding: 12px 28px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  border: none;
  transition: all 0.3s ease;
  color: #64748b;
  background: transparent;
}

.floor-btn.active {
  color: white;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.floor-btn:not(.active):hover {
  color: #1e293b;
  background: rgba(255, 255, 255, 0.8);
}

.floor-switch {
  display: flex;
  gap: 8px;
  background: rgba(241, 245, 249, 0.8);
  backdrop-filter: blur(10px);
  padding: 6px;
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(226, 232, 240, 0.8);
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
  gap: 12px;
  padding: 8px 16px;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 50px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.profile-img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid #dbeafe;
}

.profile-no-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #667eea 0%, #3b82f6 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
}

.profile-name {
  font-weight: 600;
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
  border-radius: 20px;
  padding: 30px 25px;
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

.profile-fullname
{
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  text-align: center;
  margin-bottom: 8px;
}

.role-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
  border: 1px solid #667eea30;
  border-radius: 50px;
  font-size: 13px;
  font-weight: 600;
  color: #3b82f6;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.logout-btn {
  width: 100%;
  background: #ef4444;
  color: white;
  padding: 12px 16px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1rem;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  position: relative;
  overflow: hidden;
}

.logout-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.6s;
}

.logout-btn:hover {
  background: #dc2626;
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.logout-btn:hover::before {
  left: 100%;
}

.logout-btn:active {
  transform: translateY(-1px) scale(1.01);
  transition: transform 0.1s;
}

@media (max-width: 768px)
{
  .app-title
  {
    display: none;
  }
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

  .profile-trigger
  {
    padding: 0;
  }
}
</style>