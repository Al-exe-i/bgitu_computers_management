<script>
import TrustedSvgIcon from "@/components/Common/TrustedSvgIcon.vue";

export default {
  name: "SystemLayout",
  components: { TrustedSvgIcon },

  data() {
    return {
      navLinks: [
        {
          name: 'SystemOffices',
          label: 'Корпуса',
          icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" d="M22 22H2"/><path d="M17 22V6c0-1.886 0-2.828-.586-3.414C15.828 2 14.886 2 13 2h-2c-1.886 0-2.828 0-3.414.586C7 3.172 7 4.114 7 6v16m14 0V11.5c0-1.405 0-2.107-.337-2.611a2 2 0 0 0-.552-.552C19.607 8 18.904 8 17.5 8M3 22V11.5c0-1.405 0-2.107.337-2.611a2 2 0 0 1 .552-.552C4.393 8 5.096 8 6.5 8"/><path stroke-linecap="round" d="M12 22v-3M10 5h4m-4 3h4m-4 3h4m-4 3h4"/></svg>'
        },
        {
          name: 'SystemUsers',
          label: 'Пользователи',
          icon: '<svg viewBox="0 0 24 24"><path fill="currentColor" d="M12.3 12.22A4.92 4.92 0 0 0 14 8.5a5 5 0 0 0-10 0a4.92 4.92 0 0 0 1.7 3.72A8 8 0 0 0 1 19.5a1 1 0 0 0 2 0a6 6 0 0 1 12 0a1 1 0 0 0 2 0a8 8 0 0 0-4.7-7.28M9 11.5a3 3 0 1 1 3-3a3 3 0 0 1-3 3m9.74.32A5 5 0 0 0 15 3.5a1 1 0 0 0 0 2a3 3 0 0 1 3 3a3 3 0 0 1-1.5 2.59a1 1 0 0 0-.5.84a1 1 0 0 0 .45.86l.39.26l.13.07a7 7 0 0 1 4 6.38a1 1 0 0 0 2 0a9 9 0 0 0-4.23-7.68"/></svg>'
        },
        {
          name: 'SystemInvites',
          label: 'Пригласительные ссылки',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20"><path fill="currentColor" d="M17.74 2.76a4.32 4.32 0 0 1 0 6.1l-1.53 1.52c-1.12 1.12-2.7 1.47-4.14 1.09l2.62-2.61l.76-.77l.76-.76c.84-.84.84-2.2 0-3.04a2.13 2.13 0 0 0-3.04 0l-.77.76l-3.38 3.38c-.37-1.44-.02-3.02 1.1-4.14l1.52-1.53a4.32 4.32 0 0 1 6.1 0M8.59 13.43l5.34-5.34c.42-.42.42-1.1 0-1.52c-.44-.43-1.13-.39-1.53 0l-5.33 5.34c-.42.42-.42 1.1 0 1.52c.44.43 1.13.39 1.52 0m-.76 2.29l4.14-4.15c.38 1.44.03 3.02-1.09 4.14l-1.52 1.53a4.32 4.32 0 0 1-6.1 0a4.32 4.32 0 0 1 0-6.1l1.53-1.52c1.12-1.12 2.7-1.47 4.14-1.1l-4.14 4.15c-.85.84-.85 2.2 0 3.05c.84.84 2.2.84 3.04 0"/></svg>'
        },
        {
          name: 'SystemAudiences',
          label: 'Аудитории',
          icon: '<svg viewBox="0 0 28 28"><path fill="currentColor" d="m11.894 2.014l11.5 2.25A.75.75 0 0 1 24 5v18a.75.75 0 0 1-.606.736l-11.5 2.25A.75.75 0 0 1 11 25.25V2.75a.75.75 0 0 1 .894-.736m.606 1.647V24.34l10-1.956V5.618zm-2.5.84V6H5.5v16H10v1.5H4.75a.75.75 0 0 1-.743-.649L4 22.75V5.25a.75.75 0 0 1 .648-.743L4.75 4.5zm5 8.5a1 1 0 1 1 0 2a1 1 0 0 1 0-2"/></svg>'
        },
        {
          name: 'SystemHardwareAnalytics',
          label: 'Аналитика',
          icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19h16"/><path d="M7 16V9"/><path d="M12 16V5"/><path d="M17 16v-3"/></svg>'
        },
        {
          name: 'SystemLogs',
          label: 'Журнал действий',
          icon: '<svg viewBox="0 0 22 22"><path fill="currentColor" d="M15 8H8V6h7m-1 7H9v-2h5m4 10H4v-1H3v-3H2v-3h1v-2H2v-2h1V8H2V5h1V2h1V1h14v1h1v18h-1m-1-1V3H5v2h1v3H5v2h1v2H5v2h1v3H5v2Z"/></svg>'
        }
      ],
      navPillRefs: {},
      navIndicatorStyle: {
        width: '0px',
        height: '0px',
        transform: 'translate3d(0, 0, 0)',
        opacity: '0'
      },
      indicatorFrame: null
    };
  },

  computed: {
    activeNavName() {
      const match = this.navLinks.find(link => link.name === this.$route.name);
      return match?.name || this.navLinks[0]?.name || null;
    }
  },

  methods: {
    setNavPillRef(name, element) {
      if (element) {
        this.navPillRefs[name] = element;
        return;
      }

      delete this.navPillRefs[name];
    },

    queueIndicatorSync(scrollIntoView = false) {
      if (this.indicatorFrame) {
        cancelAnimationFrame(this.indicatorFrame);
      }

      this.indicatorFrame = requestAnimationFrame(() => {
        this.updateActiveIndicator(scrollIntoView);
      });
    },

    updateActiveIndicator(scrollIntoView = false) {
      const navElement = this.$refs.systemNav;
      const activeElement = this.activeNavName ? this.navPillRefs[this.activeNavName] : null;

      if (!navElement || !activeElement) {
        this.navIndicatorStyle = {
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

      this.navIndicatorStyle = {
        width: `${activeRect.width}px`,
        height: `${activeRect.height}px`,
        transform: `translate3d(${left}px, ${top}px, 0)`,
        opacity: '1'
      };

      if (scrollIntoView && typeof window !== 'undefined' && window.innerWidth <= 768) {
        activeElement.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
          inline: 'center'
        });
      }
    },

    handleResize() {
      this.queueIndicatorSync();
    }
  },

  watch: {
    '$route.name'() {
      this.$nextTick(() => {
        this.queueIndicatorSync(true);
      });
    }
  },

  mounted() {
    this.$nextTick(() => {
      this.queueIndicatorSync();
    });

    window.addEventListener('resize', this.handleResize);
  },

  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize);

    if (this.indicatorFrame) {
      cancelAnimationFrame(this.indicatorFrame);
    }
  }
};
</script>

<template>
  <div class="system-container">
    <nav ref="systemNav" class="system-nav" aria-label="Системное меню">
      <span class="nav-active-indicator" :style="navIndicatorStyle" aria-hidden="true"></span>

      <router-link
          v-for="link in navLinks"
          :key="link.name"
          :to="{ name: link.name }"
          custom
          v-slot="{ href, navigate }"
      >
        <a
            :href="href"
            class="nav-pill"
            :class="{ 'is-active': activeNavName === link.name }"
            :title="link.label"
            :aria-current="activeNavName === link.name ? 'page' : null"
            :ref="element => setNavPillRef(link.name, element)"
            @click="navigate"
        >
          <span class="nav-icon" aria-hidden="true">
            <TrustedSvgIcon :svg="link.icon" />
          </span>
          <span class="nav-label">{{ link.label }}</span>
        </a>
      </router-link>
    </nav>

    <main class="system-content">
      <router-view v-slot="{ Component }">
        <transition name="fade-slide" mode="out-in">
          <div class="system-view-shell" :key="$route.name">
            <component :is="Component" />
          </div>
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style scoped>
.system-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.system-nav {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 6px;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  background:
      radial-gradient(circle at top left, rgba(59, 130, 246, 0.08), transparent 38%),
      radial-gradient(circle at bottom right, rgba(14, 165, 233, 0.08), transparent 32%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.96));
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.05);
  isolation: isolate;
}

.nav-active-indicator {
  position: absolute;
  top: 0;
  left: 0;
  border-radius: 999px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 58%, #0ea5e9 100%);
  box-shadow:
      0 14px 28px rgba(37, 99, 235, 0.24),
      inset 0 1px 0 rgba(255, 255, 255, 0.26);
  transition:
      transform 0.42s cubic-bezier(0.22, 1, 0.36, 1),
      width 0.42s cubic-bezier(0.22, 1, 0.36, 1),
      height 0.42s cubic-bezier(0.22, 1, 0.36, 1),
      opacity 0.18s ease;
  pointer-events: none;
  z-index: 0;
}

.nav-pill {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 999px;
  background: transparent;
  color: #64748b;
  font-size: 14px;
  font-weight: 600;
  border: 1px solid transparent;
  text-decoration: none;
  outline: none;
  transition:
      color 0.28s ease,
      transform 0.28s ease,
      background-color 0.28s ease,
      box-shadow 0.28s ease;
  will-change: transform, color;
}

.nav-pill::before {
  content: '';
  position: absolute;
  inset: 1px;
  border-radius: inherit;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0));
  opacity: 0;
  transition: opacity 0.28s ease;
  pointer-events: none;
}

.nav-icon,
.nav-label {
  position: relative;
  z-index: 1;
  transition: transform 0.32s ease, opacity 0.32s ease;
}

.nav-icon :deep(svg) {
  width: 20px;
  height: 20px;
  display: block;
}

.nav-pill:hover:not(.is-active) {
  background: rgba(241, 245, 249, 0.88);
  color: #0f172a;
  transform: translateY(-1px);
}

.nav-pill:hover:not(.is-active) .nav-icon {
  transform: translateY(-1px) scale(1.03);
}

.nav-pill.is-active {
  color: #ffffff;
  transform: translateY(-1px);
}

.nav-pill.is-active::before {
  opacity: 1;
}

.nav-pill.is-active .nav-icon {
  transform: scale(1.05);
}

.nav-pill.is-active .nav-label {
  transform: translateX(1px);
}

.nav-pill:focus-visible {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25);
}

.system-content {
  position: relative;
}

.system-view-shell {
  position: relative;
  transform-origin: top center;
  will-change: opacity, transform;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition:
      opacity 0.18s ease,
      transform 0.22s cubic-bezier(0.22, 1, 0.36, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-slide-enter-to,
.fade-slide-leave-from {
  opacity: 1;
  transform: translateY(0);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (max-width: 768px) {
  .system-nav {
    flex-wrap: nowrap;
    overflow-x: auto;
    overflow-y: hidden;
    scrollbar-width: none;
    -ms-overflow-style: none;
    justify-content: stretch;
    gap: 6px;
    padding: 5px;
    border-radius: 18px;
  }

  .system-nav::-webkit-scrollbar {
    display: none;
  }

  .nav-pill {
    flex: 1 0 48px;
    min-width: 48px;
    justify-content: center;
    padding: 11px;
    gap: 0;
    border-radius: 14px;
  }

  .nav-label {
    display: none;
  }

  .nav-active-indicator {
    border-radius: 14px;
  }
}
</style>
