<script>
import { useAuthStore } from "@/stores/auth.js";

export default {
  name: "SettingsLayout",

  data() {
    return {
      observer: null
    };
  },

  computed: {
    authStore() {
      return useAuthStore();
    },

    currentSectionTitle() {
      return this.$route.meta.title || 'Настройки';
    },

    navTabs() {
      const tabs = [
        {
          name: 'SettingsProfile',
          label: 'Профиль',
          icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>',
          show: true,
          isActive: () => this.$route.name === 'SettingsProfile'
        },
        {
          name: 'SettingsSecurity',
          label: 'Безопасность',
          icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>',
          show: true,
          isActive: () => this.$route.name === 'SettingsSecurity'
        },
        {
          name: 'SystemOffices',
          label: 'Система',
          icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>',
          show: this.authStore.user?.role === 1,
          isActive: () => this.$route.path.includes('/settings/system')
        }
      ];

      return tabs.filter(tab => tab.show);
    }
  },

  mounted() {
    this.setupObserver();
  },

  beforeUnmount() {
    if (this.observer) this.observer.disconnect();
  },

  methods: {
    setupObserver() {
      const headerEl = this.$refs.subheader;
      if (!headerEl) return;

      this.observer = new ResizeObserver((entries) => {
        for (let entry of entries) {
          document.documentElement.style.setProperty(
              '--settings-subheader-height',
              `${entry.contentRect.height}px`
          );
        }
      });

      this.observer.observe(headerEl);
    }
  }
};
</script>

<template>
  <div class="settings-layout">

    <!-- Навигация -->
    <header class="settings-subheader glass-effect" ref="subheader">
      <div class="subheader-container">

        <!-- Плавная смена заголовка -->
        <transition name="fade-title" mode="out-in">
          <h1 class="section-title" :key="currentSectionTitle">
            {{ currentSectionTitle }}
          </h1>
        </transition>

        <!-- Иконки навигации -->
        <nav class="icon-tabs" aria-label="Вкладки настроек">
          <router-link
              v-for="tab in navTabs"
              :key="tab.name"
              :to="{ name: tab.name }"
              class="icon-tab"
              :class="{ 'active': tab.isActive() }"
              :title="tab.label"
              :aria-label="tab.label"
          >
            <!-- Рендерим SVG -->
            <span class="tab-icon-wrapper" v-html="tab.icon"></span>
          </router-link>
        </nav>

      </div>
    </header>

    <!-- Контент -->
    <main class="settings-content">
      <div class="content-wrapper">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
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
  position: sticky;
  top: 0;
  z-index: 30;
  padding: 0 20px;
  height: 60px; /* Вернул оригинальную высоту */
  display: flex;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
}

/* Оставил эффект матового стекла, он делает скролл контента под шапку красивым */
.glass-effect {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.subheader-container {
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* ЗАГОЛОВОК */
.section-title {
  font-size: 20px;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

/* Анимация смены заголовка */
.fade-title-enter-active,
.fade-title-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-title-enter-from { opacity: 0; transform: translateY(4px); }
.fade-title-leave-to { opacity: 0; transform: translateY(-4px); }


/* --- СТИЛИ ВКЛАДОК (ТАБОВ) --- */
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
  outline: none; /* Убираем дефолтную обводку для красивого :focus-visible ниже */
}

/* Фиксируем размер иконки, чтобы она не зависела от того, как вставлена */
.tab-icon-wrapper :deep(svg) {
  width: 24px;
  height: 24px;
  display: block;
}

.icon-tab:hover:not(.disabled):not(.active) {
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

/* Полезная фича для навигации с клавиатуры */
.icon-tab:focus-visible {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.4);
}

/* --- КОНТЕНТ --- */
.settings-content {
  padding: 30px 20px;
}

.content-wrapper {
  max-width: 800px;
  margin: 0 auto;
}

/* Анимация перехода между страницами настроек */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-slide-enter-from { opacity: 0; transform: translateY(8px); }
.fade-slide-leave-to { opacity: 0; transform: translateY(-8px); }

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

  .tab-icon-wrapper :deep(svg) {
    width: 20px;
    height: 20px;
  }
}
</style>
