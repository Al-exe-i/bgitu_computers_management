<script>
export default {
  props: { id: { type: String, required: true }, label: { type: String, required: true } },
  data: () => ({ open: false, position: {}, closeTimer: null }),
  mounted() {
    document.addEventListener('pointerdown', this.outside);
    document.addEventListener('keydown', this.onKey);
    window.addEventListener('resize', this.hide);
    window.addEventListener('scroll', this.onScroll, true);
  },
  beforeUnmount() {
    clearTimeout(this.closeTimer);
    document.removeEventListener('pointerdown', this.outside);
    document.removeEventListener('keydown', this.onKey);
    window.removeEventListener('resize', this.hide);
    window.removeEventListener('scroll', this.onScroll, true);
  },
  methods: {
    async show() {
      clearTimeout(this.closeTimer);
      if (this.open) return;
      this.open = true;
      await this.$nextTick();
      if (!this.open || !this.$refs.popup) return;
      const rect = this.$refs.trigger.getBoundingClientRect();
      const popup = this.$refs.popup.getBoundingClientRect();
      this.position = {
        left: `${Math.max(12, Math.min(rect.right - popup.width, window.innerWidth - popup.width - 12))}px`,
        top: `${Math.max(12, Math.min(rect.bottom + 8, window.innerHeight - popup.height - 12))}px`,
      };
    },
    hide() { this.open = false; clearTimeout(this.closeTimer); },
    deferHide() { clearTimeout(this.closeTimer); this.closeTimer = setTimeout(this.hide, 180); },
    outside(event) { if (!this.$refs.trigger.contains(event.target) && !this.$refs.popup?.contains(event.target)) this.hide(); },
    onScroll(event) { if (!this.$refs.popup?.contains(event.target)) this.hide(); },
    onKey(event) { if (this.open && event.key === 'Escape') { this.hide(); event.stopImmediatePropagation(); } },
  },
};
</script>

<template>
  <button ref="trigger" class="context-help-trigger" type="button" :aria-label="label" :aria-expanded="open" :aria-describedby="open ? id : undefined"
    @mouseenter="show" @mouseleave="deferHide" @focus="show" @blur="deferHide" @click="show">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 0 1 5 .5c0 1.5-2.5 1.8-2.5 3.5M12 16.5h.01"/></svg>
  </button>
  <Teleport to="body">
    <aside v-if="open" :id="id" ref="popup" role="tooltip" class="context-help-popup" :style="position" @mouseenter="show" @mouseleave="deferHide">
      <strong>{{ label }}</strong><slot />
    </aside>
  </Teleport>
</template>

<style scoped>
.context-help-trigger { display: inline-grid; place-items: center; width: 32px; height: 32px; padding: 5px; border: 0; border-radius: 50%; background: transparent; color: #52657e; cursor: pointer; }
.context-help-trigger svg { width: 21px; height: 21px; }
.context-help-trigger:focus-visible { outline: 2px solid #3b82f6; outline-offset: 2px; }
.context-help-popup { position: fixed; z-index: 1300; box-sizing: border-box; width: min(320px, calc(100vw - 24px)); max-height: calc(100dvh - 24px); padding: 18px; overflow-y: auto; overscroll-behavior: contain; border-radius: 12px; background: #fff; color: #475569; box-shadow: 0 12px 40px rgb(15 23 42 / .2); font-size: 13px; line-height: 1.6; }
.context-help-popup strong { display: block; color: #172033; font-size: 15px; font-weight: 600; margin-bottom: 10px; }
.context-help-popup :deep(p) { margin: 8px 0 0; }
html[data-theme='dark'] .context-help-popup { background: #1e293b; color: #b8c4d4; }
html[data-theme='dark'] .context-help-popup strong { color: #e2e8f0; }
html[data-theme='dark'] .context-help-trigger { color: #a6b3c6; }
@media (hover: hover) { .context-help-trigger:hover { background: rgb(100 116 139 / .12); } }
@media (pointer: coarse) { .context-help-trigger { width: 44px; height: 44px; } }
</style>
