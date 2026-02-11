<script>
export default {
  name: "SystemLayout"
};
</script>

<template>
  <div class="system-container">
    <!-- Внутренняя навигация -->
    <div class="system-nav">
      <router-link :to="{ name: 'SystemOffices' }" class="nav-pill" active-class="active">
        <span>
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" d="M22 22H2"/><path d="M17 22V6c0-1.886 0-2.828-.586-3.414C15.828 2 14.886 2 13 2h-2c-1.886 0-2.828 0-3.414.586C7 3.172 7 4.114 7 6v16m14 0V11.5c0-1.405 0-2.107-.337-2.611a2 2 0 0 0-.552-.552C19.607 8 18.904 8 17.5 8M3 22V11.5c0-1.405 0-2.107.337-2.611a2 2 0 0 1 .552-.552C4.393 8 5.096 8 6.5 8"/><path stroke-linecap="round" d="M12 22v-3M10 5h4m-4 3h4m-4 3h4m-4 3h4"/></g></svg>
        </span>
        <span class="system-nav-link">Корпуса</span>
      </router-link>

      <router-link :to="{ name: 'SystemUsers' }" class="nav-pill" active-class="active">
        <span>
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M12.3 12.22A4.92 4.92 0 0 0 14 8.5a5 5 0 0 0-10 0a4.92 4.92 0 0 0 1.7 3.72A8 8 0 0 0 1 19.5a1 1 0 0 0 2 0a6 6 0 0 1 12 0a1 1 0 0 0 2 0a8 8 0 0 0-4.7-7.28M9 11.5a3 3 0 1 1 3-3a3 3 0 0 1-3 3m9.74.32A5 5 0 0 0 15 3.5a1 1 0 0 0 0 2a3 3 0 0 1 3 3a3 3 0 0 1-1.5 2.59a1 1 0 0 0-.5.84a1 1 0 0 0 .45.86l.39.26l.13.07a7 7 0 0 1 4 6.38a1 1 0 0 0 2 0a9 9 0 0 0-4.23-7.68"/></svg>
        </span>
        <span class="system-nav-link">Пользователи</span>
      </router-link>

      <router-link :to="{ name: 'SystemAudiences' }" class="nav-pill" active-class="active">
        <span>
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 28 28"><title>Conference-room-28-regular SVG Icon</title><path fill="currentColor" d="m11.894 2.014l11.5 2.25A.75.75 0 0 1 24 5v18a.75.75 0 0 1-.606.736l-11.5 2.25A.75.75 0 0 1 11 25.25V2.75a.75.75 0 0 1 .894-.736m.606 1.647V24.34l10-1.956V5.618zm-2.5.84V6H5.5v16H10v1.5H4.75a.75.75 0 0 1-.743-.649L4 22.75V5.25a.75.75 0 0 1 .648-.743L4.75 4.5zm5 8.5a1 1 0 1 1 0 2a1 1 0 0 1 0-2"/></svg>
        </span>
        <span class="system-nav-link">Аудитории</span>
      </router-link>

      <span class="nav-pill disabled" title="В разработке">
        <span>
          <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 22 22"><path fill="currentColor" d="M15 8H8V6h7m-1 7H9v-2h5m4 10H4v-1H3v-3H2v-3h1v-2H2v-2h1V8H2V5h1V2h1V1h14v1h1v18h-1m-1-1V3H5v2h1v3H5v2h1v2H5v2h1v3H5v2Z"/></svg>
        </span>
        <span class="system-nav-link">Журнал действий</span>
      </span>
    </div>

    <!-- Контент подраздела -->
    <div class="system-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>
  </div>
</template>


<style scoped>
.system-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.system-nav {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  padding-bottom: 10px;
  border-bottom: 1px solid #e2e8f0;
}

.nav-pill {
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 20px;
  background-color: white;
  color: #64748b;
  font-size: 14px;
  font-weight: 500;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;
  display: flex;
  align-items: center;
}

.nav-pill:hover:not(.disabled) {
  border-color: #cbd5e1;
  color: #334155;
}

.nav-pill.active {
  background-color: #3b82f6;
  color: white;
  border-color: #3b82f6;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

.nav-pill.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: #f1f5f9;
}

.nav-pill span {
  margin-right: 2px;
}

/* Анимация */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .system-nav-link {
    display: none;
  }

  .nav-pill {
    padding: 8px 10px;
  }
}
</style>
