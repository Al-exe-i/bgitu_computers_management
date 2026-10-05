<script>
import ModalCloseButton from './ModalCloseButton.vue';
import { confirmationRequest, answerConfirmation } from '@/services/confirmation.js';

export default {
  name: 'ConfirmationModal',
  components: { ModalCloseButton },
  data: () => ({ previousOverflow: '', returnFocus: null, locked: false, backdropStarted: false }),
  computed: { request() { return confirmationRequest.value; } },
  watch: {
    request: {
      async handler(request) {
        if (!request) { this.release(); return; }
        await this.$nextTick();
        if (this.request?.id !== request.id) return;
        if (this.locked) this.release();
        this.returnFocus = document.activeElement;
        this.previousOverflow = document.body.style.overflow;
        this.locked = true;
        document.body.style.overflow = 'hidden';
        this.$refs.dialog.showModal();
        this.$refs.cancel.focus({ preventScroll: true });
        document.addEventListener('keydown', this.onKey, true);
      },
      immediate: true,
      flush: 'post',
    },
  },
  beforeUnmount() {
    this.answer(false);
    this.release();
  },
  methods: {
    answer(accepted) { if (this.request) answerConfirmation(this.request.id, accepted); },
    release() {
      document.removeEventListener('keydown', this.onKey, true);
      this.$refs.dialog?.close();
      if (!this.locked) return;
      document.body.style.overflow = this.previousOverflow;
      this.locked = false;
      if (this.returnFocus?.isConnected) this.returnFocus.focus({ preventScroll: true });
      this.returnFocus = null;
      this.backdropStarted = false;
    },
    onKey(event) {
      // Нижняя модалка или полноэкранная схема не должны обработать тот же Escape/Tab.
      event.stopImmediatePropagation();
      if (event.key === 'Escape') { event.preventDefault(); this.answer(false); }
    },
    isOutside(event) {
      const rect = this.$refs.dialog.getBoundingClientRect();
      return event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom;
    },
    onBackdrop(event) {
      if (this.backdropStarted && this.isOutside(event)) this.answer(false);
      this.backdropStarted = false;
    },
  },
};
</script>

<template>
  <Teleport to="body">
    <dialog ref="dialog" class="action-confirm" :class="{ 'is-danger': request?.tone === 'danger' }"
      role="alertdialog" aria-modal="true" aria-labelledby="action-confirm-title" aria-describedby="action-confirm-description"
      @cancel.prevent="answer(false)" @pointerdown="backdropStarted = isOutside($event)" @click="onBackdrop">
      <template v-if="request">
        <div class="action-confirm-body">
          <div class="action-confirm-topline">
            <span class="action-confirm-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <template v-if="request.tone === 'danger'"><path d="M3 6h18M9 6V4h6v2M5 6l1 14h12l1-14M10 10v6M14 10v6"/></template>
                <template v-else><path d="m10.3 4-8 14a2 2 0 0 0 1.7 3h16a2 2 0 0 0 1.7-3l-8-14a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17h.01"/></template>
              </svg>
            </span>
            <ModalCloseButton @click="answer(false)" />
          </div>
          <h2 id="action-confirm-title">{{ request.title }}</h2>
          <div id="action-confirm-description">
            <p v-if="request.subject" class="action-confirm-subject">{{ request.subject }}</p>
            <p class="action-confirm-message">{{ request.message }}</p>
            <p v-if="request.detail" class="action-confirm-detail">{{ request.detail }}</p>
          </div>
        </div>
        <div class="action-confirm-footer">
          <button ref="cancel" type="button" autofocus class="action-confirm-cancel" @click="answer(false)">{{ request.cancelLabel }}</button>
          <button type="button" class="action-confirm-accept" @click="answer(true)">{{ request.confirmLabel }}</button>
        </div>
      </template>
    </dialog>
  </Teleport>
</template>

<style scoped>
.action-confirm {
  --confirm-bg: #fff; --confirm-ink: #172338; --confirm-muted: #596b83;
  --confirm-line: #d7e0ed; --confirm-footer: #f7f9fc; --confirm-accent: #245bd8;
  --confirm-symbol: #986018; --confirm-tint: #fff5e4;
  box-sizing: border-box; width: min(480px, calc(100% - 32px)); max-height: calc(100dvh - 32px);
  margin: auto; padding: 0; overflow: auto; border: 1px solid var(--confirm-line); border-radius: 24px;
  background: var(--confirm-bg); color: var(--confirm-ink); font-family: inherit;
  box-shadow: 0 24px 80px #0f172a33;
}
.action-confirm[open] { animation: confirm-appear 140ms ease-out; }
.action-confirm::backdrop { background: #0f172a80; backdrop-filter: blur(3px); }
.action-confirm.is-danger { --confirm-accent: #bd263a; --confirm-symbol: #b42338; --confirm-tint: #fff0f2; }
html[data-theme='dark'] .action-confirm {
  --confirm-bg: #111d30; --confirm-ink: #e6edf8; --confirm-muted: #a9b8ce;
  --confirm-line: #334760; --confirm-footer: #152237; --confirm-accent: #3269df;
  --confirm-symbol: #f2c47f; --confirm-tint: #30291f; box-shadow: 0 24px 80px #0006;
}
html[data-theme='dark'] .action-confirm.is-danger { --confirm-accent: #bd263a; --confirm-symbol: #ffa8b2; --confirm-tint: #322330; }
.action-confirm-body { padding: 26px 28px 28px; }
.action-confirm-topline { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 18px; }
.action-confirm-icon { display: grid; place-items: center; width: 44px; height: 44px; border-radius: 14px; color: var(--confirm-symbol); background: var(--confirm-tint); }
.action-confirm-icon svg { width: 24px; height: 24px; }
.action-confirm h2 { margin: 0 0 12px; font-size: 23px; line-height: 1.3; font-weight: 650; overflow-wrap: anywhere; }
.action-confirm p { font-size: 15px; line-height: 1.6; overflow-wrap: anywhere; white-space: pre-line; }
.action-confirm-subject { margin: 0 0 12px; font-weight: 600; color: var(--confirm-ink); }
.action-confirm-message { margin: 0; color: var(--confirm-muted); }
.action-confirm-detail { margin: 18px 0 0; padding: 12px 14px; border-radius: 12px; background: var(--confirm-tint); color: var(--confirm-symbol); }
.action-confirm-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 18px 28px; border-top: 1px solid var(--confirm-line); background: var(--confirm-footer); }
.action-confirm-footer button { min-height: 44px; padding: 10px 18px; border-radius: 12px; font: inherit; font-size: 14px; font-weight: 600; cursor: pointer; line-height: 1.35; }
.action-confirm-cancel { border: 1px solid var(--confirm-line); background: var(--confirm-bg); color: var(--confirm-ink); }
.action-confirm-accept { border: 1px solid transparent; background: var(--confirm-accent); color: #fff; }
.action-confirm-cancel:hover { background: var(--confirm-footer); }
.action-confirm-accept:hover { filter: brightness(1.08); }
.action-confirm button:focus-visible { outline: 2px solid #5b94f7; outline-offset: 3px; }
@keyframes confirm-appear { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 480px) {
  .action-confirm-body { padding: 22px; }
  .action-confirm h2 { font-size: 21px; }
  .action-confirm-footer { padding: 16px 22px; flex-wrap: wrap; }
  .action-confirm-footer button { flex: 1 1 120px; }
}
@media (prefers-reduced-motion: reduce) { .action-confirm[open] { animation: none; } }
</style>
