<script>
import { useAuthStore } from '@/stores/auth.js'
import router from "@/router/index.js";
import {useAudienceContext} from "@/stores/officeCtx.js";
import noAvatar from '@/assets/user_no_icon.svg';
import suIcon from '@/assets/crown.svg'
import adminIcon from '@/assets/shield_with_star.svg';
import teacherIcon from '@/assets/graduation-cap.svg';
import api from "@/services/api.js";
import {useOfficeStore} from "@/stores/offices.js";

export default {
  name: 'appHeader',
  data() {
    return {
      isDropdownOpen: false,
      activeOfficeId: null,
      isOfficeDropdownOpen: false,
      offices: []
    }
  },

  computed: {
    officeStore() { return useOfficeStore() },

    // Все корпуса из глобального стора
    allOffices() {
      return this.officeStore.list;
    },

    // Первые 2 корпуса (для кнопок)
    visibleOffices() {
      return this.allOffices.slice(0, 2);
    },

    // Остальные корпуса (для дропдауна)
    hiddenOffices() {
      return this.allOffices.slice(2);
    },

    // Проверка, выбран ли корпус из скрытых (чтобы подсветить кнопку "Еще")
    isHiddenOfficeActive() {
      return this.hiddenOffices.some(o => o.id === this.activeOfficeId);
    },

    authStore()
    {
      return useAuthStore()
    },

    audienceContext()
    {
      return useAudienceContext()
    },

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
      if(this.authStore.user?.is_superuser)
        return `SU`
      switch (this.authStore.user?.role)
      {
        case 1:
          return `Админ`
        case 2:
          return `Преподаватель`
      }
    },
    userAvatar()
    {
      return this.authStore.user?.photo || null
    },
    userAvatarLarge() {
      return this.authStore.user?.photo || noAvatar
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

    toggleOfficeDropdown()
    {
      this.isOfficeDropdownOpen = !this.isOfficeDropdownOpen;
    },

    handleOfficeClick(id)
    {
      router.push({ name: 'Office', params: { officeNumber: id } });
      this.isOfficeDropdownOpen = false;
    },

    updateActiveOffice() {
      const routeOffice = Number(this.$route.params.officeNumber);
      if (this.$route.name === 'Office' || this.$route.name === 'Audience') {
        this.activeOfficeId = routeOffice || this.audienceContext.officeId || null;
      } else {
        this.activeOfficeId = null;
      }
    },

    getPermissionIcon(user)
    {
      if(user?.is_superuser) return suIcon;
      if(user?.role === 1) return adminIcon;
      return teacherIcon;
    },

    goSettings() {
      router.push("/settings")
      this.isDropdownOpen = false
    }
  },

  watch: {
    '$route'()
    {
      this.updateActiveOffice()
    },

    'audienceContext.officeId'()
    {
      this.updateActiveOffice()
    }
  },

  mounted() {
    document.addEventListener('click', this.handleClickOutside)
    if (this.officeStore.list.length === 0)
    {
      this.officeStore.fetchOffices();
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

        <div class="brand-text">
          <span class="brand-title">BGITU</span>
          <span class="brand-subtitle">Computers Management</span>
        </div>
      </div>

      <!-- Переключение между корпусами -->
      <div class="office-switch" v-if="allOffices.length > 0">

        <!--  Видимые кнопки (максимум 2) -->
        <button
            v-for="office in visibleOffices"
            :key="office.id"
            @click="handleOfficeClick(office.id)"
            class="office-btn"
            :class="{ active: activeOfficeId === office.id }"
        >
          {{ office.id }} корпус
        </button>

        <!-- Кнопка "Ещё", если корпусов > 2 -->
        <div v-if="hiddenOffices.length > 0" class="more-offices-wrapper">
          <button
              @click="toggleOfficeDropdown"
              class="office-btn more-btn"
              :class="{ active: isHiddenOfficeActive || isOfficeDropdownOpen }"
          >
            Ещё
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>

          <!-- Выпадающий список скрытых корпусов -->
          <transition name="fade">
            <div v-show="isOfficeDropdownOpen" class="office-dropdown">
              <div
                  v-for="office in hiddenOffices"
                  :key="office.id"
                  @click="handleOfficeClick(office.id)"
                  class="office-dropdown-item"
                  :class="{ active: activeOfficeId === office.id }"
              >
                {{ office.id }} корпус
              </div>
            </div>
          </transition>
        </div>

      </div>

      <!-- Профиль или кнопка авторизации -->
      <div class="auth-container">
        <!-- Если авторизованы -->
        <div v-if="authStore.isAuthenticated" class="profile-dropdown">
          <div class="profile-trigger" :class="{active: isDropdownOpen}" @click="toggleDropdown">
            <img
                v-if="userAvatar"
                :src="userAvatar"
                alt="Профиль"
                class="profile-img"
            >
            <div class="profile-no-icon" v-else>{{ userName[0].toUpperCase() }}</div>
            <span class="profile-name">{{ userName }} </span>
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
                <img :src="getPermissionIcon(authStore.user)" alt="Роль">
                <span>{{ userRole }}</span>
              </div>
            </div>
            <div class="user-dropdown-menu">
              <div class="menu-item">
                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                </svg>
                <span>Мой профиль</span>
              </div>

              <div @click="goSettings" class="menu-item">
                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                </svg>
                <span>Настройки</span>
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

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.brand-title {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: -0.2px;
}

.brand-subtitle {
  font-size: 12px;
  color: oklch(0.65 0.02 260);
}

.more-offices-wrapper {
  position: relative;
}

.more-btn {
  display: flex;
  align-items: center;
  gap: 4px;
}

.office-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0; /* Или left: 0 */
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  padding: 6px;
  min-width: 140px;
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.office-dropdown-item {
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 14px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.office-dropdown-item:hover {
  background: #f1f5f9;
  color: #334155;
}

.office-dropdown-item.active {
  background: #eff6ff;
  color: #3b82f6;
  font-weight: 600;
}

.office-btn {
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

.office-btn.active {
  color: white;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.office-btn:not(.active):hover {
  color: #1e293b;
  background: rgba(255, 255, 255, 0.8);
}

.office-switch {
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

.profile-trigger.active {
  background: rgba(59, 130, 246, 0.2);
  border-color: #3b82f6;
}

.profile-img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid #dbeafe;
  object-fit: cover;
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
  user-select: none;
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
  padding: 25px 20px;
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
  object-fit: cover;
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

.user-dropdown-menu {
  padding-bottom: 10px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #4b5563;
  font-weight: 500;
  font-size: 15px;
}

.menu-item:hover {
  color: #3b82f6;
  transform: translateX(4px);
}

.menu-item svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
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
  .brand-text
  {
    display: none;
  }
}

@media (max-width: 768px)
{
  .office-switch
  {
    margin-right: 0;
  }

  .office-btn
  {
    font-size: 14px;
    padding: 5px 5px;
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