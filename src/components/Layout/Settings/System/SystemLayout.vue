<script>
export default {
  name: "SystemLayout",
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
      ]
    };
  }
};
</script>

<template>
  <div class="system-container">
    <!-- Навигация -->
    <nav class="system-nav" aria-label="Системное меню">
      <router-link
          v-for="link in navLinks"
          :key="link.name"
          :to="{ name: link.name }"
          class="nav-pill"
          active-class="is-active"
          :title="link.label"
      >
        <!-- v-html безопасно использовать здесь, так как мы сами контролируем SVG-строки -->
        <span class="nav-icon" v-html="link.icon" aria-hidden="true"></span>
        <span class="nav-label">{{ link.label }}</span>
      </router-link>
    </nav>

    <!-- Контент текущего раздела -->
    <main class="system-content">
      <router-view v-slot="{ Component }">
        <transition name="fade-slide" mode="out-in">
          <!-- Обертка :key="...$route.name" заставляет Vue перерисовывать компонент,
               чтобы анимация срабатывала всегда, даже между похожими роутами -->
          <component :is="Component" :key="$route.name" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style scoped>
/* --- Лэйаут --- */
.system-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.system-nav {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
}

/* --- Вкладки (Pills) --- */
.nav-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 999px;
  background-color: transparent;
  color: #64748b;
  font-size: 14px;
  font-weight: 500;
  border: 1px solid transparent;
  text-decoration: none;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
}

.nav-icon :deep(svg) {
  width: 20px;
  height: 20px;
  display: block;
}

.nav-pill:hover:not(.is-active) {
  background-color: #f1f5f9;
  color: #0f172a;
}

.nav-pill.is-active {
  background-color: #3b82f6;
  color: #ffffff;
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
  transform: translateY(-1px);
}

.nav-pill:focus-visible {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.4);
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* --- Адаптив --- */
@media (max-width: 768px) {
  .system-nav {
    /* На мобилках вкладки могут скроллиться вбок, если не влезают (как в Google Play) */
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none; /* Прячем скроллбар в Firefox */
    -ms-overflow-style: none; /* Прячем в IE */
    padding-top: 12px;
  }

  .system-nav::-webkit-scrollbar {
    display: none; /* Прячем скроллбар в Chrome/Safari */
  }

  .nav-label {
    display: none;
  }

  .nav-pill {
    padding: 10px; /* Делаем область клика квадратной (круглой) для пальца */
    border-radius: 50%;
  }
}
</style>
