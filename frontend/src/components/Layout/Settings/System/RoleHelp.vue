<script>
export default {
  data: () => ({ open: false, position: {}, closeTimer: null }),
  mounted() { document.addEventListener('pointerdown', this.outside); window.addEventListener('resize', this.hide); document.addEventListener('keydown', this.onKey); },
  beforeUnmount() { clearTimeout(this.closeTimer); document.removeEventListener('pointerdown', this.outside); window.removeEventListener('resize', this.hide); document.removeEventListener('keydown', this.onKey); },
  methods: {
    show() {
      clearTimeout(this.closeTimer);
      const rect = this.$refs.trigger.getBoundingClientRect();
      this.position = { left: `${Math.max(12, Math.min(rect.left, window.innerWidth - 380))}px`,
        top: `${Math.max(12, Math.min(rect.bottom + 8, window.innerHeight - 440))}px` };
      this.open = true;
    },
    hide() { this.open = false; clearTimeout(this.closeTimer); },
    deferHide() { clearTimeout(this.closeTimer); this.closeTimer = setTimeout(this.hide, 180); },
    outside(e) { if (!this.$refs.trigger.contains(e.target) && !this.$refs.popup?.contains(e.target)) this.hide(); },
    onKey(e) { if (e.key === 'Escape' && this.open) { e.stopImmediatePropagation(); this.hide(); } },
  },
};
</script>
<template>
  <button ref="trigger" type="button" class="role-help-trigger" aria-label="Права ролей" :aria-expanded="open" :aria-describedby="open ? 'role-help-content' : undefined"
      @mouseenter="show" @mouseleave="deferHide" @focus="show" @blur="deferHide" @click="show">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 0 1 5 .5c0 1.5-2.5 1.8-2.5 3.5M12 16v1"/></svg>
  </button>
  <Teleport to="body">
    <aside v-if="open" id="role-help-content" ref="popup" class="role-help-popup" :style="position" role="tooltip" @mouseenter="show" @mouseleave="deferHide">
      <h3>Роли и возможности</h3>
      <dl>
        <dt>Преподаватель</dt><dd>Просматривает корпуса, этажи и оборудование. Отмечает исправность и проблемы, добавляет фото и видео. Управляет своим профилем, сессиями и подписками на уведомления.</dd>
        <dt>Администратор</dt><dd>Дополнительно создаёт и редактирует корпуса, аудитории и схемы этажей, характеристики оборудования и шаблоны. Управляет пользователями, просматривает аналитику и журнал действий.</dd>
        <dt>SU · суперпользователь</dt><dd>Все возможности администратора, а также удаление пользователей и смена паролей преподавателей и администраторов. Изменять другого SU нельзя; свой пароль меняется в личных настройках.</dd>
      </dl>
      <p>Без входа доступны просмотр корпусов, аудиторий, схем и общей статистики, но не управление ими.</p>
    </aside>
  </Teleport>
</template>
<style scoped>
.role-help-trigger { display: inline-grid; place-items: center; vertical-align: middle; margin-left: 5px; padding: 3px; width: 28px; height: 28px; color: #64748b; background: none; border: 0; cursor: pointer; border-radius: 50%; }
.role-help-trigger svg { width: 19px; height: 19px; }
.role-help-trigger:focus-visible { outline: 2px solid #3b82f6; outline-offset: 2px; }
.role-help-popup { position: fixed; z-index: 1300; box-sizing: border-box; width: min(368px, calc(100vw - 24px)); max-height: calc(100dvh - 24px); overflow-y: auto; overscroll-behavior: contain; padding: 18px; border-radius: 12px; background: #fff; color: #475569; box-shadow: 0 12px 40px rgb(15 23 42 / .2); font-size: 13px; line-height: 1.5; text-transform: none; font-weight: 400; }
.role-help-popup h3 { font-size: 16px; margin: 0 0 16px; color: #172033; font-weight: 600; }
.role-help-popup dl { margin: 0; }
.role-help-popup dt { font-weight: 600; color: #172033; margin-top: 14px; }
.role-help-popup dd { margin: 4px 0 0; }
.role-help-popup p { margin: 16px 0 0; padding-top: 12px; border-top: 1px solid #e2e8f0; }
html[data-theme='dark'] .role-help-popup { background: #1e293b; color: #b8c4d4; }
html[data-theme='dark'] .role-help-popup :is(h3, dt) { color: #e2e8f0; }
html[data-theme='dark'] .role-help-trigger { color: #a6b3c6; }
html[data-theme='dark'] .role-help-popup p { border-color: #475569; }
@media (max-width: 600px) { .role-help-popup { top: 50% !important; left: 12px !important; transform: translateY(-50%); } .role-help-trigger { width: 36px; height: 36px; } }
</style>
