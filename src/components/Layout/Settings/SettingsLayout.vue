<script>
import {useAuthStore} from "@/stores/auth.js";

export default {
  name: "SettingsLayout",
  data() {
    return {
      observer: null
    };
  },
  computed: {
    currentSectionTitle() {
      return this.$route.meta.title || 'Настройки';
    },

    authStore() {
      return useAuthStore()
    }
  },
  mounted() {
    this.updateHeaderHeight();
    const mainHeader = document.querySelector('header');
    if (mainHeader) {
      this.observer = new ResizeObserver(() => this.updateHeaderHeight());
      this.observer.observe(mainHeader);
    }
    window.addEventListener('resize', this.updateHeaderHeight);
  },
  beforeUnmount() {
    if (this.observer) this.observer.disconnect();
    window.removeEventListener('resize', this.updateHeaderHeight);
  },
  methods: {
    updateHeaderHeight() {
      const mainHeader = document.querySelector('header');
      if (mainHeader) {
        const height = mainHeader.offsetHeight;
        document.documentElement.style.setProperty('--global-header-height', `${height}px`);
      }
    }
  }
};
</script>

<template>
  <div class="settings-layout">

    <!-- Навигация -->
    <header class="settings-subheader">
      <div class="subheader-container">

        <!-- Динамический заголовок раздела -->
        <h1 class="section-title">{{ currentSectionTitle }}</h1>

        <!-- Иконки навигации -->
        <nav class="icon-tabs">
          <!-- Профиль -->
          <router-link :to="{ name: 'SettingsProfile' }" class="icon-tab" active-class="active" title="Профиль">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
          </router-link>

          <!-- Безопасность -->
          <router-link :to="{ name: 'SettingsSecurity' }" class="icon-tab" active-class="active" title="Безопасность">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            </svg>
          </router-link>

          <!-- Система -->
          <router-link
              v-if="authStore.user?.role === 1"
              :to="{ name: 'SystemOffices' }"
              class="icon-tab"
              active-class="active"
              :class="{ 'active': $route.path.includes('/settings/system') }"
              title="Система"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
          </router-link>
        </nav>
      </div>
    </header>

    <main class="settings-content">
      <div class="content-wrapper">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<style scoped>
.settings-layout {
  min-height: 100vh;
  background-color: #f8fafc;
}

/* --- SUB-HEADER --- */
.settings-subheader {
  background: white;
  border-bottom: 1px solid #e2e8f0;
  position: sticky;
  z-index: 30;
  padding: 0 20px;
  height: 60px; /* Фиксированная высота */
  display: flex;
  align-items: center;
}

.subheader-container {
  max-width: 800px; /* Ширина контента */
  width: 100%;
  margin: 0 auto;
  display: flex;
  justify-content: space-between; /* Заголовок слева, иконки справа */
  align-items: center;
}

/* ЗАГОЛОВОК */
.section-title {
  font-size: 20px;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
  /* Анимация смены заголовка */
  transition: color 0.3s;
}

/* ТАБЫ (ИКОНКИ) */
.icon-tabs {
  display: flex;
  gap: 8px;
  background: #f1f5f9; /* Подложка под кнопки */
  padding: 4px;
  border-radius: 10px;
}

.icon-tab {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  color: #64748b;
  transition: all 0.2s ease;
  cursor: pointer;
}

.icon-tab:hover:not(.disabled) {
  background: #e2e8f0;
  color: #334155;
}

.icon-tab.active {
  background: white;
  color: #3b82f6; /* Активный цвет (синий) */
  box-shadow: 0 1px 3px rgba(0,0,0,0.1); /* Эффект "поднятой" кнопки */
}

.icon-tab.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* --- КОНТЕНТ --- */
.settings-content {
  padding: 30px 20px;
}

.content-wrapper {
  max-width: 800px;
  margin: 0 auto;
}

/* Анимация перехода страниц */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Адаптив для мобильных */
@media (max-width: 640px) {
  .section-title {
    font-size: 18px;
  }

  .icon-tabs {
    gap: 4px;
  }

  .icon-tab {
    width: 36px;
    height: 36px;
  }

  .icon-tab svg {
    width: 20px;
    height: 20px;
  }
}
</style>
