<script>
import api from '@/services/api.js';
import ModalCloseButton from './ModalCloseButton.vue';

export default {
  components: { ModalCloseButton },
  props: {
    title: { type: String, required: true },
    endpoint: { type: String, required: true },
    fields: { type: Array, required: true },
    editable: { type: Boolean, default: false },
    kind: { type: String, default: 'office' },
    marker: { type: [String, Number], default: '' },
    avatarSrc: { type: String, default: '' },
  },
  emits: ['close', 'saved'],
  data: () => ({ record: {}, draft: {}, loading: true, saving: false, editing: false,
    error: '', discardRequested: false, requestId: 0, returnFocus: null, previousOverflow: '', avatarFailed: false }),
  computed: {
    identity() {
      const used = [];
      const take = key => {
        const field = this.fields.find(item => item.key === key);
        const value = field ? String(this.display(field) ?? '').trim() : '';
        if (value) used.push(key);
        return value;
      };
      if (this.kind === 'user') {
        const name = take('name'), surname = take('surname');
        const fullName = [name, surname].filter(Boolean).join(' ');
        return { heading: fullName || take('email') || this.title, subtitle: '', role: take('role'),
          initials: [name, surname].filter(Boolean).map(value => Array.from(value)[0]).join('').toLocaleUpperCase(), used };
      }
      return { heading: this.title, subtitle: take('name'), role: '', initials: '', used };
    },
    detailFields() { return this.fields.filter(field => !this.identity.used.includes(field.key)); },
    changes() {
      return Object.fromEntries(this.fields.filter(field => !field.readonly &&
        (this.draft[field.key] || '') !== (this.record[field.key] || ''))
        .map(field => [field.key, this.draft[field.key] || null]));
    },
    dirty() { return this.editing && Object.keys(this.changes).length > 0; },
  },
  mounted() {
    this.returnFocus = document.activeElement;
    this.previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', this.onKey);
    this.$refs.dialog.focus({ preventScroll: true });
    this.load();
  },
  beforeUnmount() {
    this.requestId++;
    document.removeEventListener('keydown', this.onKey);
    document.body.style.overflow = this.previousOverflow;
    this.returnFocus?.focus({ preventScroll: true });
  },
  methods: {
    display(field) { return field.format ? field.format(this.record) : this.record[field.key]; },
    edit() {
      this.editing = true;
      this.$nextTick(() => this.$refs.dialog.querySelector('input, textarea')?.focus({ preventScroll: true }));
    },
    close() {
      if (this.saving) return;
      if (this.dirty) { this.discardRequested = true; return; }
      this.$emit('close');
    },
    onKey(event) {
      if (event.key === 'Escape') { event.preventDefault(); this.close(); }
      if (event.key !== 'Tab') return;
      const nodes = [...this.$refs.dialog.querySelectorAll('button:not(:disabled), input:not(:disabled), textarea:not(:disabled)')];
      const first = nodes[0], last = nodes.at(-1);
      if (!this.$refs.dialog.contains(document.activeElement)) {
        event.preventDefault(); (event.shiftKey ? last : first)?.focus(); return;
      }
      if (event.shiftKey && (document.activeElement === first || document.activeElement === this.$refs.dialog)) {
        event.preventDefault(); last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    },
    async load() {
      const id = ++this.requestId;
      this.loading = true;
      this.error = '';
      try {
        const { data } = await api.get(this.endpoint);
        if (id !== this.requestId) return;
        this.record = data;
        this.draft = { ...data };
      } catch {
        if (id === this.requestId) this.error = 'Не удалось загрузить сведения. Попробуйте ещё раз.';
      } finally { if (id === this.requestId) this.loading = false; }
    },
    async save() {
      if (!this.editable || !this.dirty || this.saving || this.loading) return;
      this.saving = true;
      this.error = '';
      const id = this.requestId;
      try {
        const { data } = await api.patch(this.endpoint, this.changes);
        if (id !== this.requestId) return;
        this.record = { ...this.record, ...data };
        this.draft = { ...this.record };
        this.editing = false;
        this.discardRequested = false;
        this.$emit('saved', data);
      } catch (error) {
        if (id !== this.requestId) return;
        this.error = error.response?.status === 403 ? 'Нет прав для изменения этих сведений.'
          : 'Не удалось сохранить сведения. Проверьте поля и повторите попытку.';
      } finally { if (id === this.requestId) this.saving = false; }
    },
  },
};
</script>

<template>
  <Teleport to="body">
    <Transition name="entity-info" appear>
    <div class="entity-info-overlay" @click.self="close">
      <section ref="dialog" class="entity-info-dialog" role="dialog" aria-modal="true" :aria-label="title" tabindex="-1" :aria-busy="loading || saving">
        <div class="entity-info-header" :class="{ 'is-person': kind === 'user' }">
          <ModalCloseButton class="entity-info-close" :disabled="saving" @click="close" />
          <div class="entity-info-identity">
          <div class="entity-info-emblem" :class="{ 'is-avatar': kind === 'user' }" aria-hidden="true">
          <img v-if="kind === 'user' && avatarSrc && !avatarFailed" :src="avatarSrc" alt="" @error="avatarFailed = true">
          <span v-else-if="kind === 'user' && identity.initials" class="entity-info-initials">{{ identity.initials }}</span>
          <svg v-else class="entity-info-symbol" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <template v-if="kind === 'user'"><circle cx="16" cy="10" r="5"/><path d="M6 27v-3a6 6 0 0 1 6-6h8a6 6 0 0 1 6 6v3Z"/></template>
            <template v-else-if="kind === 'floor'"><path d="m4 11 12-6 12 6-12 6-12-6Zm0 7 12 6 12-6M4 24l12 6 12-6"/></template>
            <template v-else><path d="M7 28V6l18-3v25M4 28h24M13 28v-7h6v7M12 10h2m5-1h2m-9 6h2m5-1h2"/></template>
          </svg>
          <span v-if="kind !== 'user' && marker !== ''" class="entity-info-marker">{{ marker }}</span>
          </div>
          <div class="entity-info-heading">
            <h2>{{ loading ? title : identity.heading }}</h2>
            <p v-if="!loading && identity.subtitle" class="entity-info-subtitle">{{ identity.subtitle }}</p>
            <span v-if="!loading && identity.role" class="entity-info-role">{{ identity.role }}</span>
          </div>
          </div>
          <button v-if="editable && !loading && !error && !editing" type="button" class="entity-info-button entity-info-edit" @click="edit">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m12.5 3.5 4 4M3 17l4.5-1 9-9a2.8 2.8 0 0 0-4-4l-9 9L3 17Z"/></svg>
            Редактировать
          </button>
        </div>
        <div class="entity-info-body">
          <div v-if="loading" class="entity-info-loading" role="status">
            <span class="entity-info-sr-only">Загружаем сведения…</span>
            <span v-for="index in 3" :key="index" class="entity-info-placeholder" aria-hidden="true" />
          </div>
          <form v-else-if="editing" id="entity-info-form" class="entity-info-form" @submit.prevent="save">
            <label v-for="field in fields.filter(item => !item.readonly)" :key="field.key" class="entity-info-field">
              <span class="entity-info-field-label">{{ field.label }}</span>
              <textarea v-if="field.multiline" v-model="draft[field.key]" :maxlength="field.max || 4000" :disabled="saving" rows="4" />
              <input v-else v-model="draft[field.key]" :maxlength="field.max || 120" :disabled="saving" type="text">
              <span v-if="field.multiline" class="entity-info-length">{{ (draft[field.key] || '').length }} / {{ field.max || 4000 }}</span>
            </label>
          </form>
          <dl v-else-if="!error" class="entity-info-list">
            <div v-for="field in detailFields" :key="field.key" class="entity-info-row" :class="{ 'is-multiline': field.multiline, 'is-wide': field.key === 'email' }">
              <dt>{{ field.label }}</dt>
              <dd :class="{ 'is-empty': !display(field) }">{{ display(field) || 'Не указано' }}</dd>
            </div>
          </dl>
          <p v-if="error" class="entity-info-error" role="alert">{{ error }}</p>
        </div>
        <div v-if="discardRequested" class="entity-info-footer is-discard">
          <p>Закрыть без сохранения?</p>
          <div class="entity-info-actions"><button type="button" class="entity-info-button" @click="discardRequested = false">Остаться</button><button type="button" class="entity-info-button is-danger" @click="$emit('close')">Не сохранять</button></div>
        </div>
        <div v-else-if="editing || (error && !loading)" class="entity-info-footer">
          <button v-if="error && !editing" type="button" class="entity-info-button" :disabled="loading" @click="load">Повторить</button>
          <template v-if="editing">
            <span class="entity-info-save-state" role="status">{{ saving ? 'Сохраняем сведения' : dirty ? 'Есть изменения' : 'Нет изменений' }}</span>
            <div class="entity-info-actions">
              <button type="button" class="entity-info-button" :disabled="saving" @click="draft = { ...record }; editing = false; error = ''">Отмена</button>
              <button type="submit" form="entity-info-form" class="entity-info-button is-primary" :disabled="!editable || !dirty || saving">{{ saving ? 'Сохранение...' : 'Сохранить' }}</button>
            </div>
          </template>
        </div>
      </section>
    </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.entity-info-overlay {
  --info-bg: var(--surface, #fff);
  --info-ink: var(--text-primary, #172033);
  --info-muted: var(--text-secondary, #637187);
  --info-tint: #f1f6fd;
  --info-emblem: #e5efff;
  --info-emblem-ink: #2863da;
  --info-border: #e3e8ef;
  --info-input: #f8fafc;
  --info-hover: #eef2f7;
  --info-input-border: #cbd5e1;
  --info-accent: #285bd4;
  --info-error: #b42332;
  --info-error-bg: #fff2f3;
  --info-disabled: #e9eef5;
  --info-disabled-ink: #7b8799;
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgb(9 17 32 / .54);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}
html[data-theme='dark'] .entity-info-overlay {
  --info-bg: var(--surface, #111827);
  --info-ink: var(--text-primary, #e0e7f1);
  --info-muted: #9eafc5;
  --info-tint: #152136;
  --info-emblem: #203657;
  --info-emblem-ink: #9ec5ff;
  --info-border: #28364b;
  --info-input: #0d1625;
  --info-hover: #213149;
  --info-input-border: #34455d;
  --info-accent: #86b0ff;
  --info-error: #ffb3b8;
  --info-error-bg: #301f2b;
  --info-disabled: #223048;
  --info-disabled-ink: #8394ad;
}
.entity-info-dialog {
  box-sizing: border-box;
  width: min(100%, 540px);
  min-width: 0;
  max-height: calc(100dvh - 40px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--info-bg);
  color: var(--info-ink);
  border: 0;
  border-radius: 24px;
  box-shadow: 0 28px 90px rgb(3 10 22 / .28);
  outline: none;
}
.entity-info-header {
  position: relative;
  flex: 0 0 auto;
  padding: 32px 30px 24px;
  background: var(--info-tint);
}
.entity-info-close { position: absolute; top: 16px; right: 16px; }
.entity-info-identity { display: flex; align-items: center; gap: 20px; padding-right: 30px; }
.entity-info-emblem { position: relative; flex: 0 0 64px; width: 64px; height: 64px; display: grid; place-items: center; background: var(--info-emblem); color: var(--info-emblem-ink); border-radius: 19px; }
.entity-info-emblem.is-avatar { border-radius: 50%; overflow: hidden; }
.entity-info-emblem img { width: 100%; height: 100%; object-fit: cover; }
.entity-info-initials { font-size: 22px; font-weight: 600; letter-spacing: -.02em; }
.entity-info-marker { position: absolute; right: -5px; bottom: -5px; min-width: 26px; height: 26px; display: grid; place-items: center; padding: 0 5px; border: 3px solid var(--info-tint); border-radius: 50%; background: #2863da; color: #fff; font-size: 11px; font-weight: 600; }
.entity-info-symbol { width: 32px; height: 32px; }
.entity-info-heading { min-width: 0; }
.entity-info-header h2 { margin: 0; font: inherit; color: var(--info-ink); font-size: 26px; font-weight: 600; line-height: 1.2; letter-spacing: -.03em; overflow-wrap: anywhere; text-wrap: balance; }
.entity-info-subtitle { color: var(--info-muted); margin: 8px 0 0; font-size: 14px; line-height: 1.5; overflow-wrap: anywhere; }
.entity-info-role { display: inline-block; margin-top: 10px; padding: 4px 9px; border-radius: 6px; color: var(--info-emblem-ink); background: var(--info-emblem); font-size: 12px; font-weight: 500; line-height: 1.4; }
.entity-info-header .entity-info-edit { margin: 22px 0 0 84px; min-height: 34px; padding: 6px 10px; font-size: 12px; background: var(--info-bg); border-color: transparent; }
.entity-info-body { min-height: 0; overflow-y: auto; padding: 0 30px; overscroll-behavior: contain; scrollbar-width: thin; scrollbar-color: var(--info-input-border) transparent; }
.entity-info-list { margin: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px 28px; padding-block: 28px 30px; }
.entity-info-row { display: grid; align-content: start; gap: 7px; min-width: 0; }
.entity-info-row dt { font-size: 12px; line-height: 1.5; color: var(--info-muted); font-weight: 400; }
.entity-info-row dd { margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; color: var(--info-ink); font-size: 15px; font-weight: 500; line-height: 1.55; }
.entity-info-row.is-multiline, .entity-info-row.is-wide { grid-column: 1 / -1; }
.entity-info-row.is-multiline { order: 1; padding-top: 20px; border-top: 1px solid var(--info-border); }
.entity-info-row.is-multiline:only-child { padding-top: 0; border-top: 0; }
.entity-info-row.is-multiline dd { font-weight: 400; }
.entity-info-row dd.is-empty { color: var(--info-muted); font-size: 14px; font-weight: 400; }
.entity-info-form { padding: 24px 0; display: grid; gap: 20px; }
.entity-info-field { display: grid; gap: 8px; min-width: 0; }
.entity-info-field-label { color: var(--info-muted); font-size: 13px; font-weight: 500; }
.entity-info-field :is(input, textarea) { width: 100%; min-width: 0; box-sizing: border-box; background: var(--info-input); color: var(--info-ink); border: 1px solid var(--info-input-border); border-radius: 10px; padding: 11px 13px; font: inherit; font-size: 15px; font-weight: 400; line-height: 1.5; transition: border-color 150ms ease-out; }
.entity-info-field textarea { resize: vertical; min-height: 112px; }
.entity-info-length { justify-self: end; color: var(--info-muted); font-size: 11px; line-height: 1; font-variant-numeric: tabular-nums; }
.entity-info-footer { flex: 0 0 auto; display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-end; gap: 12px; padding: 17px 26px; border-top: 1px solid var(--info-border); }
.entity-info-save-state { margin-right: auto; color: var(--info-muted); font-size: 12px; }
.entity-info-actions { display: flex; gap: 8px; }
.entity-info-button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; box-sizing: border-box; font: inherit; font-size: 13px; font-weight: 500; padding: 9px 14px; min-height: 40px; background: transparent; color: var(--info-ink); border: 1px solid var(--info-input-border); border-radius: 10px; cursor: pointer; transition: background-color 150ms ease-out, border-color 150ms ease-out, transform 120ms ease-out; }
.entity-info-button:not(:disabled):active { transform: scale(.97); }
.entity-info-button svg { width: 16px; height: 16px; }
.entity-info-button.is-primary { background: #285bd4; color: #fff; border-color: #285bd4; }
.entity-info-button.is-danger { color: var(--info-error); }
.entity-info-button:disabled { background: var(--info-disabled); color: var(--info-disabled-ink); border-color: transparent; cursor: default; }
.entity-info-dialog button:focus-visible { outline: 2px solid var(--info-accent); outline-offset: 3px; }
.entity-info-field :is(input, textarea):focus { border-color: var(--info-accent); outline: none; box-shadow: inset 0 0 0 1px var(--info-accent); }
html[data-theme='dark'] .entity-info-field :is(input, textarea):focus { border-color: var(--info-accent) !important; }
.entity-info-footer.is-discard { justify-content: space-between; }
.entity-info-footer.is-discard p { margin: 0; font-size: 14px; color: var(--info-ink); }
.entity-info-error { margin: 16px 0; padding: 12px 14px; border-radius: 10px; background: var(--info-error-bg); color: var(--info-error); font-size: 14px; line-height: 1.5; }
.entity-info-loading { display: grid; gap: 20px; padding: 24px 0; }
.entity-info-placeholder { display: block; height: 34px; border-radius: 6px; background: var(--info-input); }
.entity-info-placeholder:last-child { width: 70%; }
.entity-info-sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
@media (hover: hover) {
  .entity-info-button:not(:disabled):hover { background: var(--info-hover); border-color: var(--info-muted); }
  .entity-info-button.is-primary:not(:disabled):hover { background: #214fbf; border-color: #214fbf; }
  .entity-info-field :is(input, textarea):not(:disabled):not(:focus):hover { border-color: var(--info-muted); }
}
.entity-info-enter-active { transition: opacity 220ms ease-out; }
.entity-info-leave-active { transition: opacity 150ms ease-out; }
.entity-info-enter-active .entity-info-dialog { transition: transform 220ms cubic-bezier(.22, 1, .36, 1); }
.entity-info-leave-active .entity-info-dialog { transition: transform 150ms ease-out; }
.entity-info-enter-from, .entity-info-leave-to { opacity: 0; }
.entity-info-enter-from .entity-info-dialog, .entity-info-leave-to .entity-info-dialog { transform: translateY(8px) scale(.97); }
@media (max-width: 480px) {
  .entity-info-overlay { padding: 12px; }
  .entity-info-dialog { max-height: calc(100dvh - 24px); border-radius: 18px; }
  .entity-info-header { padding: 28px 22px 22px; }
  .entity-info-header h2 { font-size: 23px; }
  .entity-info-identity { gap: 15px; padding-right: 24px; align-items: flex-start; }
  .entity-info-emblem { width: 52px; height: 52px; flex-basis: 52px; border-radius: 16px; }
  .entity-info-symbol { width: 28px; height: 28px; }
  .entity-info-header .entity-info-edit { margin-left: 67px; min-height: 40px; }
  .entity-info-close { top: 10px; right: 10px; }
  .entity-info-body { padding: 0 22px; }
  .entity-info-list { gap: 22px 18px; padding-block: 24px; }
  .entity-info-row dd { font-size: 14px; }
  .entity-info-footer { padding: 14px 18px; gap: 10px; }
  .entity-info-save-state { flex-basis: 100%; }
  .entity-info-actions { flex: 1; }
  .entity-info-actions .entity-info-button { flex: 1; }
  .entity-info-button { min-height: 44px; }
  .entity-info-field :is(input, textarea) { font-size: 16px; }
}
@media (max-width: 350px) { .entity-info-list { grid-template-columns: minmax(0, 1fr); } }
@media (max-height: 500px) { .entity-info-header { padding-block: 16px; } .entity-info-emblem { width: 40px; height: 40px; flex-basis: 40px; } .entity-info-header .entity-info-edit { margin: 10px 0 0 60px; } }
@media (prefers-reduced-transparency: reduce) { .entity-info-overlay { backdrop-filter: none; -webkit-backdrop-filter: none; background: rgb(9 17 32 / .75); } }
@media (prefers-reduced-motion: reduce) { .entity-info-enter-active, .entity-info-leave-active, .entity-info-enter-active .entity-info-dialog, .entity-info-leave-active .entity-info-dialog, .entity-info-button, .entity-info-field :is(input, textarea) { transition: none; } }
</style>
