<script>
import { useAuthStore } from '@/stores/auth.js'
import router from "@/router/index.js";
import {useAudienceContext} from "@/stores/officeCtx.js";
import noAvatar from '@/assets/user_no_icon.svg';
import suIcon from '@/assets/crown.svg'
import adminIcon from '@/assets/shield_with_star.svg';
import teacherIcon from '@/assets/graduation-cap.svg';
import logoLight from '@/assets/logo_IT.png';
import logoDark from '@/assets/logo_IT_dark.png'
import {useOfficeStore} from "@/stores/offices.js";
import {useThemeStore} from "@/stores/theme.js";

export default {
  name: 'appHeader',
  data() {
    return {
      isDropdownOpen: false,
      activeOfficeId: null,
      isOfficeDropdownOpen: false,
      officeSwitchRefs: {},
      officeIndicatorStyle: {
        width: '0px',
        height: '0px',
        transform: 'translate3d(0, 0, 0)',
        opacity: '0'
      },
      officeIndicatorFrame: null
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

    isMoreButtonActive() {
      return this.isHiddenOfficeActive || (this.isOfficeDropdownOpen && !this.activeOfficeId);
    },

    desktopActiveOfficeKey() {
      if (this.visibleOffices.some(office => office.id === this.activeOfficeId)) {
        return `office-${this.activeOfficeId}`;
      }

      if (this.isMoreButtonActive) {
        return 'more';
      }

      return null;
    },

    activeOffice() {
      return this.allOffices.find(office => office.id === this.activeOfficeId) || null;
    },

    activeOfficeLabel() {
      return this.activeOffice ? `Корп. №${this.activeOffice.id}` : 'Выбрать корпус';
    },

    authStore()
    {
      return useAuthStore()
    },

    audienceContext()
    {
      return useAudienceContext()
    },

    themeStore() {
      return useThemeStore()
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
    },

    appLogo() {
      return this.themeStore.isDark ? logoDark : logoLight;
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

      if (!event.target.closest('.office-switch-shell'))
      {
        this.isOfficeDropdownOpen = false;
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

    setOfficeSwitchRef(key, element) {
      if (element) {
        this.officeSwitchRefs[key] = element;
        return;
      }

      delete this.officeSwitchRefs[key];
    },

    queueOfficeIndicatorSync() {
      if (this.officeIndicatorFrame) {
        cancelAnimationFrame(this.officeIndicatorFrame);
      }

      this.officeIndicatorFrame = requestAnimationFrame(() => {
        this.updateOfficeIndicator();
      });
    },

    updateOfficeIndicator() {
      const switchElement = this.$refs.officeSwitchDesktop;
      const activeElement = this.desktopActiveOfficeKey ? this.officeSwitchRefs[this.desktopActiveOfficeKey] : null;

      if (!switchElement || !activeElement) {
        this.officeIndicatorStyle = {
          width: '0px',
          height: '0px',
          transform: 'translate3d(0, 0, 0)',
          opacity: '0'
        };
        return;
      }

      const switchRect = switchElement.getBoundingClientRect();
      const activeRect = activeElement.getBoundingClientRect();
      const left = activeRect.left - switchRect.left + switchElement.scrollLeft;
      const top = activeRect.top - switchRect.top + switchElement.scrollTop;

      this.officeIndicatorStyle = {
        width: `${activeRect.width}px`,
        height: `${activeRect.height}px`,
        transform: `translate3d(${left}px, ${top}px, 0)`,
        opacity: '1'
      };
    },

    handleHeaderResize() {
      this.queueOfficeIndicatorSync();
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
    },

    toggleTheme() {
      this.themeStore.toggleTheme()
    }
  },

  watch: {
    '$route'()
    {
      this.updateActiveOffice()
      this.isOfficeDropdownOpen = false
      this.$nextTick(() => {
        this.queueOfficeIndicatorSync()
      })
    },

    'audienceContext.officeId'()
    {
      this.updateActiveOffice()
      this.$nextTick(() => {
        this.queueOfficeIndicatorSync()
      })
    },

    isOfficeDropdownOpen()
    {
      this.$nextTick(() => {
        this.queueOfficeIndicatorSync()
      })
    },

    allOffices()
    {
      this.$nextTick(() => {
        this.queueOfficeIndicatorSync()
      })
    }
  },

  mounted() {
    document.addEventListener('click', this.handleClickOutside)
    window.addEventListener('resize', this.handleHeaderResize)
    this.updateActiveOffice()
    this.$nextTick(() => {
      this.queueOfficeIndicatorSync()
    })
    if (this.officeStore.list.length === 0)
    {
      this.officeStore.fetchOffices();
    }
  },

  beforeUnmount() {
    document.removeEventListener('click', this.handleClickOutside)
    window.removeEventListener('resize', this.handleHeaderResize)
    if (this.officeIndicatorFrame) {
      cancelAnimationFrame(this.officeIndicatorFrame)
    }
  }
}
</script>

<template>
  <header>
    <div class="header-container">
      <!-- Логотип -->
      <div @click="handleHomeClick" class="logo-container">
        <div class="logo">
          <img :src="appLogo" alt="Logo">
        </div>

        <div class="brand-text">
          <span class="brand-title">BGITU</span>
          <span class="brand-subtitle">Computers Management</span>
        </div>
      </div>

      <!-- Переключение между корпусами -->
      <div class="office-switch-shell" v-if="allOffices.length > 0">
        <div ref="officeSwitchDesktop" class="office-switch office-switch-desktop">
          <span class="office-switch-indicator" :style="officeIndicatorStyle" aria-hidden="true"></span>

        <!--  Видимые кнопки (максимум 2) -->
        <button
            v-for="office in visibleOffices"
            :key="office.id"
            @click="handleOfficeClick(office.id)"
            class="office-btn"
            :class="{ active: activeOfficeId === office.id }"
            :ref="element => setOfficeSwitchRef(`office-${office.id}`, element)"
        >
          {{ office.id }} корпус
        </button>

        <!-- Кнопка "Ещё", если корпусов > 2 -->
        <div v-if="hiddenOffices.length > 0" class="more-offices-wrapper">
          <button
              @click="toggleOfficeDropdown"
              class="office-btn more-btn"
              :class="{ active: isMoreButtonActive }"
              :ref="element => setOfficeSwitchRef('more', element)"
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

        <div class="office-switch-mobile">
          <button
              type="button"
              class="office-mobile-trigger"
              :class="{ active: isOfficeDropdownOpen }"
              @click="toggleOfficeDropdown"
          >
            <span class="office-mobile-icon" aria-hidden="true">
              {{ activeOffice?.id ?? '—' }}
            </span>
            <span class="office-mobile-copy">
              <span class="office-mobile-kicker">Корпус</span>
              <span class="office-mobile-value">{{ activeOfficeLabel }}</span>
            </span>
            <svg class="office-mobile-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>

          <transition name="fade">
            <div v-show="isOfficeDropdownOpen" class="office-mobile-dropdown">
              <button
                  v-for="office in allOffices"
                  :key="office.id"
                  type="button"
                  class="office-mobile-option"
                  :class="{ active: activeOfficeId === office.id }"
                  @click="handleOfficeClick(office.id)"
              >
                <span class="office-mobile-option-mark" aria-hidden="true">
                  {{ office.id }}
                </span>
                <span class="office-mobile-option-copy">
                  <span class="office-mobile-option-title">К. №{{ office.id }}</span>
                  <span v-if="office.address" class="office-mobile-option-subtitle">{{ office.address }}</span>
                </span>
                <span class="office-mobile-option-check" aria-hidden="true">
                  <svg v-if="activeOfficeId === office.id" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 12.5l4.2 4.2L19 7"></path>
                  </svg>
                </span>
              </button>
            </div>
          </transition>
        </div>
      </div>

      <!-- Профиль или кнопка авторизации -->
      <div class="auth-container">
        <button
            class="theme-toggle"
            :title="themeStore.isDark ? 'Светлая тема' : 'Тёмная тема'"
            :aria-label="themeStore.isDark ? 'Переключить на светлую тему' : 'Переключить на тёмную тему'"
            @click="toggleTheme"
        >
          <svg v-if="themeStore.isDark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="5"></circle>
            <line x1="12" y1="1" x2="12" y2="3"></line>
            <line x1="12" y1="21" x2="12" y2="23"></line>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
            <line x1="1" y1="12" x2="3" y2="12"></line>
            <line x1="21" y1="12" x2="23" y2="12"></line>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z"></path>
          </svg>
        </button>
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
  z-index: 1;
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
  position: relative;
  z-index: 1;
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
  background: transparent;
  box-shadow: none;
}

.office-btn:not(.active):hover {
  color: #1e293b;
  background: rgba(255, 255, 255, 0.8);
}

.office-switch {
  position: relative;
  display: flex;
  gap: 8px;
  background:
      radial-gradient(circle at top left, rgba(59, 130, 246, 0.08), transparent 36%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.94));
  backdrop-filter: blur(10px);
  padding: 6px;
  border-radius: 14px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  border: 1px solid rgba(226, 232, 240, 0.8);
  isolation: isolate;
}

.office-switch-indicator {
  position: absolute;
  top: 0;
  left: 0;
  border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 62%, #0ea5e9 100%);
  box-shadow:
      0 14px 28px rgba(37, 99, 235, 0.24),
      inset 0 1px 0 rgba(255, 255, 255, 0.26);
  transition:
      transform 0.4s cubic-bezier(0.22, 1, 0.36, 1),
      width 0.4s cubic-bezier(0.22, 1, 0.36, 1),
      height 0.4s cubic-bezier(0.22, 1, 0.36, 1),
      opacity 0.18s ease;
  pointer-events: none;
  z-index: 0;
}

.office-switch-shell {
  position: relative;
  display: flex;
  align-items: center;
}

.office-switch-desktop {
  display: flex;
}

.office-switch-mobile {
  display: none;
  position: relative;
}

.office-mobile-trigger {
  width: 100%;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border: 1px solid rgba(203, 213, 225, 0.92);
  border-radius: 16px;
  background:
      linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(241, 245, 249, 0.96)),
      linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(14, 165, 233, 0.08));
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
  cursor: pointer;
  transition: border-color 0.25s ease, box-shadow 0.25s ease, transform 0.25s ease;
}

.office-mobile-trigger:hover {
  transform: translateY(-1px);
  border-color: rgba(147, 197, 253, 0.95);
  box-shadow: 0 14px 28px rgba(37, 99, 235, 0.12);
}

.office-mobile-trigger.active {
  border-color: rgba(96, 165, 250, 0.95);
  box-shadow: 0 16px 32px rgba(37, 99, 235, 0.16);
}

.office-mobile-icon,
.office-mobile-option-mark {
  min-width: 34px;
  height: 34px;
  padding: 0 9px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1;
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.92), rgba(224, 242, 254, 0.95));
}

.office-mobile-option-check svg,
.office-mobile-chevron {
  width: 18px;
  height: 18px;
}

.office-mobile-copy,
.office-mobile-option-copy {
  min-width: 0;
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: flex-start;
}

.office-mobile-kicker {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #64748b;
}

.office-mobile-value,
.office-mobile-option-title {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.office-mobile-option-subtitle {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
  color: #64748b;
}

.office-mobile-chevron {
  flex-shrink: 0;
  color: #64748b;
  transition: transform 0.25s ease, color 0.25s ease;
}

.office-mobile-trigger.active .office-mobile-chevron {
  color: #2563eb;
  transform: rotate(180deg);
}

.office-mobile-dropdown {
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  right: 0;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-radius: 18px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  background: rgba(255, 255, 255, 0.97);
  backdrop-filter: blur(18px);
  box-shadow: 0 22px 44px rgba(15, 23, 42, 0.14);
  z-index: 120;
}

.office-mobile-option {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: none;
  border-radius: 14px;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease;
}

.office-mobile-option:hover {
  background: rgba(241, 245, 249, 0.92);
  transform: translateY(-1px);
}

.office-mobile-option.active {
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.78), rgba(224, 242, 254, 0.82));
}

.office-mobile-option-check {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: #2563eb;
}

.auth-container {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  flex: 1;
}

.theme-toggle {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  border: 1px solid #cbd5e1;
  background: rgba(248, 250, 252, 0.9);
  color: #334155;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.25s ease;
}

.theme-toggle svg {
  width: 20px;
  height: 20px;
}

.theme-toggle:hover {
  transform: translateY(-1px);
  border-color: #93c5fd;
  color: #1d4ed8;
  background: #eff6ff;
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
  margin-left: 0;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
}

.profile-dropdown
{
  position: relative;
  margin-left: 0;
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

  .header-container {
    gap: 8px;
  }

  .logo-container {
    flex: 0 0 auto;
  }

  .office-switch-shell {
    flex: 1 1 auto;
    min-width: 0;
    margin: 0 6px;
  }

  .office-switch-desktop {
    display: none;
  }

  .office-switch-mobile {
    display: block;
    width: 100%;
  }

  .office-mobile-trigger {
    padding: 7px 10px;
    border-radius: 15px;
    gap: 8px;
  }

  .office-mobile-icon,
  .office-mobile-option-mark {
    min-width: 32px;
    height: 32px;
    padding: 0 8px;
    border-radius: 11px;
    font-size: 12px;
  }

  .office-mobile-value,
  .office-mobile-option-title {
    font-size: 13px;
  }

  .office-mobile-option-subtitle {
    font-size: 10px;
  }

  .office-mobile-dropdown {
    top: calc(100% + 8px);
    border-radius: 16px;
    padding: 7px;
  }

  .office-mobile-option {
    padding: 9px 10px;
  }

  .auth-container {
    flex: 0 0 auto;
    margin-left: 8px;
    gap: 8px;
  }

  .profile-name
  {
    display: none;
  }

  .profile-dropdown-content {
    right: 50%;
  }

  .profile-trigger
  {
    padding: 0;
  }

  .theme-toggle {
    width: 38px;
    height: 38px;
    border-radius: 10px;
  }
}
</style>
