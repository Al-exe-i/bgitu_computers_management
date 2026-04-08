<script>
import { useAuthStore } from "@/stores/auth.js";

export default {
  name: "SettingsLayout",

  data() {
    return {
      observer: null,
      tabIndicatorStyle: {
        width: '0px',
        height: '0px',
        transform: 'translate3d(0, 0, 0)',
        opacity: '0'
      },
      indicatorFrame: null
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
    this.$nextTick(() => {
      this.queueIndicatorSync();
    });
    window.addEventListener('resize', this.handleResize);
  },

  beforeUnmount() {
    if (this.observer) this.observer.disconnect();
    window.removeEventListener('resize', this.handleResize);

    if (this.indicatorFrame) {
      cancelAnimationFrame(this.indicatorFrame);
    }
  },

  watch: {
    '$route.fullPath'() {
      this.$nextTick(() => {
        this.queueIndicatorSync();
      });
    }
  },

  methods: {
    setupObserver() {
      const headerEl = this.$refs.subheader;
      if (!headerEl) return;

      this.observer = new ResizeObserver((entries) => {
        for (const entry of entries) {
          document.documentElement.style.setProperty(
            '--settings-subheader-height',
            `${entry.contentRect.height}px`
          );
        }
      });

      this.observer.observe(headerEl);
    },

    queueIndicatorSync() {
      if (this.indicatorFrame) {
        cancelAnimationFrame(this.indicatorFrame);
      }

      this.indicatorFrame = requestAnimationFrame(() => {
        this.updateIndicator();
      });
    },

    updateIndicator() {
      const navElement = this.$refs.tabsNav;
      const activeElement = navElement?.querySelector('.settings-tab.active');

      if (!navElement || !activeElement) {
        this.tabIndicatorStyle = {
          width: '0px',
          height: '0px',
          transform: 'translate3d(0, 0, 0)',
          opacity: '0'
        };
        return;
      }

      const navRect = navElement.getBoundingClientRect();
      const activeRect = activeElement.getBoundingClientRect();
      const left = activeRect.left - navRect.left + navElement.scrollLeft;
      const top = activeRect.top - navRect.top + navElement.scrollTop;

      this.tabIndicatorStyle = {
        width: `${activeRect.width}px`,
        height: `${activeRect.height}px`,
        transform: `translate3d(${left}px, ${top}px, 0)`,
        opacity: '1'
      };
    },

    handleResize() {
      this.queueIndicatorSync();
    }
  }
};
</script>

<template>
  <div class="settings-layout">
    <header class="settings-subheader glass-effect" ref="subheader">
      <div class="subheader-container">
        <transition name="fade-title" mode="out-in">
          <h1 class="section-title" :key="currentSectionTitle">
            {{ currentSectionTitle }}
          </h1>
        </transition>

        <nav ref="tabsNav" class="icon-tabs settings-tabs" aria-label="Вкладки настроек">
          <span class="settings-tab-indicator" :style="tabIndicatorStyle" aria-hidden="true"></span>

          <router-link
            v-for="tab in navTabs"
            :key="tab.name"
            :to="{ name: tab.name }"
            class="icon-tab settings-tab"
            :class="{ active: tab.isActive() }"
            :title="tab.label"
            :aria-label="tab.label"
          >
            <span class="tab-icon-wrapper" v-html="tab.icon"></span>
          </router-link>
        </nav>
      </div>
    </header>

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

.settings-subheader {
  position: sticky;
  top: 0;
  z-index: 30;
  padding: 0 20px;
  height: 60px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
}

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

.section-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #0f172a;
}

.fade-title-enter-active,
.fade-title-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-title-enter-from {
  opacity: 0;
  transform: translateY(4px);
}

.fade-title-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.settings-tabs {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px;
  border-radius: 10px;
  background: #f1f5f9;
  isolation: isolate;
}

.settings-tab-indicator {
  position: absolute;
  top: 0;
  left: 0;
  border-radius: 8px;
  background: #ffffff;
  box-shadow:
    0 8px 18px rgba(15, 23, 42, 0.08),
    0 1px 2px rgba(15, 23, 42, 0.05);
  transition:
    transform 0.34s cubic-bezier(0.22, 1, 0.36, 1),
    width 0.34s cubic-bezier(0.22, 1, 0.36, 1),
    height 0.34s cubic-bezier(0.22, 1, 0.36, 1),
    opacity 0.16s ease;
  pointer-events: none;
  z-index: 0;
}

.settings-tab {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  color: #64748b;
  text-decoration: none;
  outline: none;
  transition: color 0.22s ease, transform 0.22s ease;
}

.tab-icon-wrapper :deep(svg) {
  width: 24px;
  height: 24px;
  display: block;
}

.settings-tab:hover:not(.active) {
  color: #334155;
  transform: translateY(-1px);
}

.settings-tab.active {
  background: transparent;
  color: #3b82f6;
}

.settings-tab:focus-visible {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.35);
}

.settings-content {
  padding: 30px 20px;
}

.content-wrapper {
  max-width: 800px;
  margin: 0 auto;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

:global(html[data-theme='dark']) .settings-layout {
  background-color: transparent;
}

:global(html[data-theme='dark']) .settings-layout .settings-subheader {
  border-bottom-color: #334155;
}

:global(html[data-theme='dark']) .settings-layout .glass-effect {
  background: rgba(15, 23, 42, 0.82);
}

:global(html[data-theme='dark']) .settings-layout .section-title {
  color: #e2e8f0 !important;
}

:global(html[data-theme='dark']) .settings-layout .settings-tabs {
  background: rgba(30, 41, 59, 0.88) !important;
  box-shadow: inset 0 0 0 1px rgba(51, 65, 85, 0.9);
}

:global(html[data-theme='dark']) .settings-layout .settings-tab-indicator {
  background: #111827;
  box-shadow:
    0 10px 20px rgba(2, 6, 23, 0.32),
    0 1px 0 rgba(255, 255, 255, 0.04);
}

:global(html[data-theme='dark']) .settings-layout .settings-tab {
  color: #94a3b8;
}

:global(html[data-theme='dark']) .settings-layout .settings-tab:hover:not(.active) {
  color: #cbd5e1;
}

:global(html[data-theme='dark']) .settings-layout .settings-tab.active {
  background: transparent !important;
  color: #93c5fd !important;
}

@media (max-width: 640px) {
  .section-title {
    font-size: 18px;
  }

  .settings-tabs {
    gap: 4px;
  }

  .settings-tab {
    width: 36px;
    height: 36px;
  }

  .settings-tab-indicator {
    border-radius: 7px;
  }

  .tab-icon-wrapper :deep(svg) {
    width: 20px;
    height: 20px;
  }
}
</style>
