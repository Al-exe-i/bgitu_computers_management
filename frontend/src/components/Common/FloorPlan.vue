<script>
import api from '@/services/api.js';
import { useAuthStore } from '@/stores/auth.js';
import { useThemeStore } from '@/stores/theme.js';
import { useAudienceContext } from '@/stores/officeCtx.js';
import { planDraft, planSnapshot, planError, placeRoom, moveFromPointer, FLOOR_DIRECTIONS } from '@/utils/floorPlan.js';
import { audienceOriginQuery } from '@/utils/officeNavigation.js';
import ContextHelp from './ContextHelp.vue';

export default {
  name: 'FloorPlan',
  components: { ContextHelp },
  props: {
    officeId: { type: Number, required: true },
    floor: { type: Number, required: true },
    matchingIds: { type: Array, default: null },
  },
  emits: ['edit-state', 'ready'],
  data: () => ({
    plan: null, draft: null, baseline: '', loading: true, saving: false,
    editing: false, selectedId: null, error: '', notice: '', conflict: false,
    drag: null, preview: null, requestId: 0,
    editingLandmark: null,
    landmarkDraft: '',
    headerOffset: 0,
    headerObserver: null,
  }),
  computed: {
    directions() { return FLOOR_DIRECTIONS; },
    isDark() { return useThemeStore().isDark; },
    canEdit() {
      const auth = useAuthStore();
      return Boolean(auth.isAuthenticated && auth.user && auth.user.role < 2);
    },
    editable() { return this.editing && this.canEdit && !this.saving && !this.loading; },
    dirty() { return Boolean(this.draft && planSnapshot(this.draft) !== this.baseline); },
    editState() { return { dirty: this.dirty, saving: this.saving }; },
    selected() { return this.plan?.rooms.find(room => room.audience_public_id === this.selectedId); },
    selectedPlacement() { return this.draft?.rooms.find(room => room.audience_public_id === this.selectedId); },
    placements() { return new Map(this.draft?.rooms.map(room => [room.audience_public_id, room]) ?? []); },
    placedRooms() { return this.plan?.rooms.filter(room => this.placements.has(room.audience_public_id)) ?? []; },
    unplacedRooms() { return this.plan?.rooms.filter(room => !this.placements.has(room.audience_public_id)) ?? []; },
    matches() { return this.matchingIds === null ? null : new Set(this.matchingIds); },
    matchingCount() { return this.matches ? this.plan?.rooms.filter(room => this.matches.has(room.audience_public_id)).length ?? 0 : 0; },
    previewError() { return this.preview ? planError(placeRoom(this.draft, this.preview)) : ''; },
    endpoint() { return `/offices/${this.officeId}/floors/${this.floor}/plan`; },
  },
  watch: {
    editState: { handler(state) { this.$emit('edit-state', state); }, flush: 'sync' },
    canEdit(value) { if (!value) this.cancelDrag(); },
  },
  mounted() {
    this.load();
    const header = document.querySelector('header');
    if (header) {
      const measure = () => { this.headerOffset = header.getBoundingClientRect().height; };
      measure();
      this.headerObserver = new ResizeObserver(measure);
      this.headerObserver.observe(header);
    }
  },
  beforeUnmount() { this.requestId++; this.cancelDrag(); this.headerObserver?.disconnect(); },
  methods: {
    typeLabel(room) { return room.room_type === 'administrative' ? 'Административный' : 'Учебный'; },
    matchesFilter(room) { return !this.matches || this.matches.has(room.audience_public_id); },
    accept(plan) {
      this.plan = plan;
      this.draft = planDraft(plan);
      this.baseline = planSnapshot(this.draft);
      this.selectedId = null;
      this.editingLandmark = null;
      this.conflict = false;
    },
    async load() {
      if (this.saving || (this.dirty && !window.confirm('Загрузить сохранённую схему? Ваши изменения будут потеряны.'))) return;
      this.cancelDrag();
      const id = ++this.requestId;
      this.loading = true;
      this.error = '';
      this.notice = '';
      try {
        const { data } = await api.get(this.endpoint, { timeout: 15000 });
        if (id === this.requestId) this.accept(data);
      } catch {
        if (id === this.requestId) this.error = 'Не удалось загрузить схему этажа. Попробуйте ещё раз.';
      } finally {
        if (id === this.requestId) {
          this.loading = false;
          this.$emit('ready');
        }
      }
    },
    async save() {
      if (!this.editable || !this.dirty || this.conflict || this.drag) return;
      this.error = planError(this.draft);
      if (this.error) return;
      this.saving = true;
      this.notice = '';
      const id = this.requestId;
      try {
        const { data } = await api.put(this.endpoint, { revision: this.plan.revision, ...this.draft }, { timeout: 15000 });
        if (id !== this.requestId) return;
        this.accept(data);
        this.editing = false;
        this.notice = 'Расположение кабинетов сохранено.';
      } catch (error) {
        if (id !== this.requestId) return;
        this.conflict = error.response?.status === 409;
        this.error = this.conflict
          ? 'Схему уже изменили. Загрузите актуальную версию перед новым сохранением.'
          : [401, 403].includes(error.response?.status)
            ? 'Для сохранения нужны права администратора. Ваш черновик остался на странице.'
            : 'Не удалось сохранить схему. Ваши изменения остались на странице.';
      } finally {
        if (id === this.requestId) this.saving = false;
      }
    },
    discard() {
      if (this.saving || (this.dirty && !window.confirm('Отменить изменения схемы этажа?'))) return;
      this.cancelDrag();
      this.accept(this.plan);
      this.editing = false;
      this.error = '';
      this.notice = '';
    },
    commit(next) {
      if (!this.editable) return false;
      const error = planError(next);
      this.notice = '';
      this.error = error;
      if (error) return false;
      this.draft = next;
      return true;
    },
    resizePlan(field, event) {
      this.commit({ ...this.draft, [field]: Number(event.target.value) });
      event.target.value = this.draft[field];
    },
    resizeRoom(field, event) {
      const current = this.selectedPlacement;
      if (!current) return;
      const offset = field === 'x' || field === 'y' ? 1 : 0;
      this.commit(placeRoom(this.draft, { ...current, [field]: Number(event.target.value) - offset }));
      event.target.value = this.selectedPlacement[field] + offset;
    },
    unplace() {
      this.commit({ ...this.draft, rooms: this.draft.rooms.filter(room => room.audience_public_id !== this.selectedId) });
    },
    activate(room) {
      if (this.editing) { if (this.editable) this.selectedId = room.audience_public_id; return; }
      useAudienceContext().setOffice(this.officeId);
      this.$router.push({ name: 'Audience', params: { audiencePublicId: room.audience_public_id },
        query: audienceOriginQuery('plan', this.floor) });
    },
    placeAt(event) {
      if (!this.editable || !this.selected || this.selectedPlacement || event.target !== this.$refs.grid) return;
      const rect = this.$refs.grid.getBoundingClientRect();
      const cell = rect.width / this.draft.width;
      this.commit(placeRoom(this.draft, {
        audience_public_id: this.selectedId,
        x: Math.floor((event.clientX - rect.left) / cell),
        y: Math.floor((event.clientY - rect.top) / cell),
        width: Math.min(3, this.draft.width), height: Math.min(2, this.draft.height),
      }));
    },
    placeFirstFree() {
      if (!this.editable || !this.selected || this.selectedPlacement) return;
      for (let y = 0; y < this.draft.height; y++) {
        for (let x = 0; x < this.draft.width; x++) {
          const next = placeRoom(this.draft, { audience_public_id: this.selectedId, x, y,
            width: Math.min(3, this.draft.width), height: Math.min(2, this.draft.height) });
          if (!planError(next)) { this.commit(next); return; }
        }
      }
      this.error = 'Нет свободного места для кабинета. Увеличьте сетку или освободите участок.';
    },
    roomStyle(placement) {
      return {
        left: `${placement.x / this.draft.width * 100}%`, top: `${placement.y / this.draft.height * 100}%`,
        width: `${placement.width / this.draft.width * 100}%`, height: `${placement.height / this.draft.height * 100}%`,
      };
    },
    editLandmark(direction) {
      if (!this.editable) return;
      this.editingLandmark = direction;
      this.landmarkDraft = this.draft.landmarks[direction] || '';
      this.$nextTick(() => this.$refs.landmarkInput?.[0]?.focus({ preventScroll: true }));
    },
    saveLandmark() {
      if (!this.editingLandmark) return;
      if (this.commit({ ...this.draft, landmarks: { ...this.draft.landmarks,
        [this.editingLandmark]: this.landmarkDraft.trim() } })) this.editingLandmark = null;
    },
    startDrag(event, room) {
      if (!this.editable || this.drag || !event.isPrimary || event.button !== 0) return;
      this.selectedId = room.audience_public_id;
      const rect = this.$refs.grid.getBoundingClientRect();
      this.drag = { room: { ...this.placements.get(this.selectedId) }, pointerId: event.pointerId,
        localX: event.clientX - rect.left, localY: event.clientY - rect.top,
        clientX: event.clientX, clientY: event.clientY, moved: false };
      event.currentTarget.setPointerCapture(event.pointerId);
    },
    moveDrag(event) {
      if (!this.drag || this.drag.pointerId !== event.pointerId) return;
      if (Math.hypot(event.clientX - this.drag.clientX, event.clientY - this.drag.clientY) > 4) this.drag.moved = true;
      if (this.drag.moved) this.preview = moveFromPointer(this.drag, event.clientX, event.clientY,
        this.$refs.grid.getBoundingClientRect(), this.draft.width);
    },
    finishDrag(event) {
      if (!this.drag || this.drag.pointerId !== event.pointerId) return;
      this.moveDrag(event);
      if (this.preview) this.commit(placeRoom(this.draft, this.preview));
      this.cancelDrag();
    },
    cancelDrag() { this.drag = null; this.preview = null; },
    cancelPointer(event) {
      if (this.drag?.pointerId === event.pointerId) this.cancelDrag();
    },
    roomKey(event, room) {
      if (!this.editable) return;
      if (event.key === 'Escape') { this.cancelDrag(); event.preventDefault(); return; }
      const delta = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[event.key];
      if (!delta || this.drag) return;
      event.preventDefault();
      this.selectedId = room.audience_public_id;
      const current = this.placements.get(this.selectedId);
      this.commit(placeRoom(this.draft, { ...current, x: current.x + delta[0], y: current.y + delta[1] }));
    },
  },
};
</script>

<template>
  <section class="floor-plan" :class="{ 'is-dark': isDark, 'is-editing': editable }" :style="{ '--fp-header-offset': `${headerOffset}px` }" :aria-label="`Схема ${floor} этажа`" :aria-busy="loading || saving">
    <div class="fp-toolbar">
      <div class="fp-caption">
        <strong>{{ editing ? 'Расстановка кабинетов' : 'План этажа' }}</strong>
        <span v-if="draft">{{ draft.rooms.length }} из {{ plan.rooms.length }} кабинетов на плане<span v-if="dirty" class="fp-unsaved"> · Не сохранено</span></span>
      </div>
      <div class="fp-actions">
        <template v-if="editing && plan">
          <button type="button" :disabled="saving || loading" @click="discard">Отмена</button>
          <button type="button" class="fp-primary" :disabled="!editable || !dirty || conflict || !!drag" @click="save">{{ saving ? 'Сохраняем…' : 'Сохранить' }}</button>
        </template>
        <button v-else-if="canEdit && plan" type="button" :disabled="loading" @click="editing = true; notice = ''">
          <svg class="fp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="m16 3 5 5-12 12H4v-5zM13 6l5 5"/></svg>Редактировать
        </button>
        <button type="button" :disabled="loading || saving" @click="load">{{ conflict ? 'Загрузить актуальную' : 'Обновить' }}</button>
      </div>
    </div>
    <p v-if="loading" class="fp-message" role="status">Загружаем схему…</p>
    <p v-if="conflict" class="fp-message fp-error" role="alert">Схему уже изменили. Загрузите актуальную версию перед новым сохранением.</p>
    <p v-else-if="error" class="fp-message fp-error" role="alert">{{ error }}</p>
    <p v-if="notice" class="fp-message" role="status">{{ notice }}</p>
    <template v-if="draft">
      <div v-if="editing" class="fp-editor">
        <fieldset :disabled="!editable || !!drag" class="fp-size fp-grid-size">
          <legend class="sr-only">Размер сетки этажа</legend>
          <label>Столбцы<input type="number" min="1" max="50" :value="draft.width" @change="resizePlan('width', $event)"></label>
          <label>Ряды<input type="number" min="1" max="50" :value="draft.height" @change="resizePlan('height', $event)"></label>
        </fieldset>
        <ContextHelp :id="`floor-help-${officeId}-${floor}`" label="Как редактировать схему">
          <p>Перетаскивайте кабинеты, оставляя место для проходов. Положение и размер выбранного кабинета меняются в панели над сеткой.</p>
          <p>Стрелки клавиатуры сдвигают кабинет на клетку. Чтобы убрать его с сетки, нажмите «Снять с плана».</p>
          <p>Изменения применяются после нажатия «Сохранить».</p>
        </ContextHelp>
      </div>
      <div v-else class="fp-legend"><span>Учебный</span><span class="administrative">Административный</span><span class="fp-help">Нажмите кабинет, чтобы открыть оборудование</span></div>
      <p v-if="matches" class="fp-search-result" role="status">{{ matchingCount ? `Найдено кабинетов: ${matchingCount}. Совпадения выделены на плане и в списке вне плана.` : 'На этом этаже нет подходящих кабинетов.' }}</p>
      <div class="fp-workspace">
      <div v-if="editing" class="fp-inspector">
        <template v-if="selected">
        <div class="fp-inspector-heading"><strong>Кабинет {{ selected.number }}</strong>
          <button v-if="selectedPlacement" class="fp-unplace" type="button" :disabled="!editable || !!drag" @click="unplace">Снять с плана</button>
        </div>
        <template v-if="selectedPlacement">
        <fieldset v-for="group in [{ title: 'Положение', fields: { x: 'Столбец', y: 'Ряд' } }, { title: 'Размер в клетках', fields: { width: 'Ширина', height: 'Высота' } }]" :key="group.title" :disabled="!editable || !!drag" class="fp-size">
          <legend>{{ group.title }}</legend>
          <label v-for="(label, key) in group.fields" :key="key">{{ label }}
            <input type="number" min="1" max="50" :value="selectedPlacement[key] + (key === 'x' || key === 'y' ? 1 : 0)" @change="resizeRoom(key, $event)">
          </label>
        </fieldset>
        </template>
        <template v-else><span class="fp-help">Нажмите свободное место на сетке или</span><button type="button" :disabled="!editable" @click="placeFirstFree">Разместить автоматически</button></template>
        </template>
        <p v-else class="fp-selection-hint">Выберите кабинет на плане, чтобы изменить положение и размер.</p>
      </div>
      <div class="fp-compass">
        <div v-for="(label, direction) in directions" :key="direction" class="fp-bearing" :class="`fp-${direction}`">
          <button v-if="editing" type="button" :disabled="!editable || !!drag" :title="`Изменить ориентир: ${label}`" :aria-label="`Изменить ориентир: ${label}`" @click="editLandmark(direction)">
            <span>{{ draft.landmarks[direction] || label }}</span><svg class="fp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="m16 3 5 5-12 12H4v-5zM13 6l5 5"/></svg>
          </button>
          <span v-else :title="`${label}: ${draft.landmarks[direction] || label}`">{{ draft.landmarks[direction] || label }}</span>
          <form v-if="editable && editingLandmark === direction" class="fp-landmark-editor landmark-editor-popup" :class="`is-${direction}${['west', 'east'].includes(direction) ? '-popup' : ''}`" @submit.prevent="saveLandmark" @keydown.esc.stop.prevent="editingLandmark = null">
            <label class="landmark-editor-title" :for="`floor-${officeId}-${floor}-landmark`">{{ label }}</label>
            <div class="landmark-editor-row">
              <input :id="`floor-${officeId}-${floor}-landmark`" ref="landmarkInput" class="landmark-editor-input" v-model="landmarkDraft" maxlength="128" :placeholder="label">
              <button class="landmark-editor-action is-confirm" type="submit" title="Применить" aria-label="Применить ориентир"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m5 12 4 4L19 6"/></svg></button>
              <button class="landmark-editor-action" type="button" title="Отмена" aria-label="Отменить редактирование ориентира" @click="editingLandmark = null"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 6 12 12M18 6 6 18"/></svg></button>
            </div>
          </form>
        </div>
        <div class="fp-scroll" tabindex="0" aria-label="План этажа, прокручиваемая область">
        <div ref="grid" class="fp-grid" :style="{ '--columns': draft.width, '--rows': draft.height }" @click="placeAt">
          <button v-for="room in placedRooms" :key="room.audience_public_id" type="button" class="fp-room"
            :class="{ administrative: room.room_type === 'administrative', selected: editing && selectedId === room.audience_public_id,
              muted: !!matches && !matchesFilter(room), 'is-match': !!matches && matchesFilter(room), dragging: drag?.moved && selectedId === room.audience_public_id,
              'is-small': placements.get(room.audience_public_id).width < 3 || placements.get(room.audience_public_id).height < 2 }"
            :style="roomStyle(placements.get(room.audience_public_id))"
            :title="`Кабинет ${room.number} · ${typeLabel(room)}`" :aria-label="`Кабинет ${room.number}, ${typeLabel(room)}`"
            :aria-pressed="editing ? selectedId === room.audience_public_id : undefined" :disabled="saving || loading"
            @click.stop="activate(room)" @keydown="roomKey($event, room)"
            @pointerdown="startDrag($event, room)" @pointermove="moveDrag" @pointerup="finishDrag"
            @pointercancel="cancelPointer" @lostpointercapture="cancelPointer">
            <strong>{{ room.number }}</strong><span class="fp-room-type">{{ typeLabel(room) }}</span>
          </button>
          <div v-if="preview" class="fp-preview" :class="{ invalid: !!previewError }" :style="roomStyle(preview)" aria-hidden="true">{{ selected?.number }}</div>
        </div>
        </div>
      </div>
      </div>
      <div v-if="unplacedRooms.length" class="fp-unplaced">
        <p>Вне плана <span>{{ unplacedRooms.length }}</span></p>
        <p v-if="editing" class="fp-help">Выберите кабинет, затем укажите место на сетке.</p>
        <div class="fp-room-list">
          <button v-for="room in unplacedRooms" :key="room.audience_public_id" type="button"
            :class="{ selected: editing && selectedId === room.audience_public_id, muted: !!matches && !matchesFilter(room), 'is-match': !!matches && matchesFilter(room) }"
            :disabled="saving || loading" :aria-pressed="editing ? selectedId === room.audience_public_id : undefined" @click="activate(room)">
            <strong>{{ room.number }}</strong><span>{{ typeLabel(room) }}</span>
          </button>
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
@import './landmark-editor.css';
.floor-plan {
  --fp-bg: #f6f8fc; --fp-surface: #fff; --fp-text: #1e304d; --fp-muted: #52657e;
  --fp-border: #c7d4e6; --fp-grid: #e0e7f1; --fp-room: #dceaff; --fp-admin: #dcf0e9;
  --fp-room-ink: #204b86; --fp-admin-ink: #205d50; --fp-accent: #255bd8; --fp-error: #b42335;
  color: var(--fp-text); min-width: 0; font-size: 14px; line-height: 1.45;
}
.floor-plan.is-dark {
  --fp-bg: #0b1423; --fp-surface: #152338; --fp-text: #dce6f4; --fp-muted: #a2b3cb;
  --fp-border: #3b506e; --fp-grid: #202e43; --fp-room: #1d385a; --fp-admin: #1b3d38;
  --fp-room-ink: #c1d9ff; --fp-admin-ink: #b6e7d7; --fp-accent: #8ab6ff; --fp-error: #ffa3ac;
}
.fp-toolbar, .fp-actions, .fp-editor, .fp-legend, .fp-inspector { display: flex; align-items: center; flex-wrap: wrap; gap: 12px; }
.fp-toolbar { justify-content: space-between; margin-bottom: 16px; }
.fp-caption { display: grid; gap: 3px; }
.fp-caption strong { font-size: 22px; font-weight: 650; letter-spacing: -.025em; }
.fp-caption span, .fp-help, .fp-legend { color: var(--fp-muted); font-size: 14px; line-height: 1.5; }
.fp-caption .fp-unsaved { color: var(--fp-accent); }
.fp-icon { width: 17px; height: 17px; flex-shrink: 0; }
.fp-actions { gap: 8px; }
.floor-plan button:where(:not(.landmark-editor-action, .context-help-trigger)) { display: inline-flex; align-items: center; justify-content: center; gap: 7px; font: inherit; font-weight: 600; color: var(--fp-text); background: var(--fp-surface); border: 1px solid var(--fp-border); border-radius: 10px; padding: 9px 14px; min-height: 40px; cursor: pointer; transition: border-color 160ms, background-color 160ms; }
.floor-plan button:disabled { opacity: .5; cursor: default; }
.floor-plan button.fp-primary { background: #255bd8; border-color: #255bd8; color: #fff; }
.floor-plan :is(button, input, .fp-scroll):not(.landmark-editor-input):focus-visible { outline: 2px solid var(--fp-accent); outline-offset: 3px; }
.fp-editor { margin-bottom: 18px; padding: 16px 0; border-block: 1px solid var(--fp-border); align-items: start; justify-content: space-between; gap: 12px 24px; }
.fp-grid-size { align-items: center; gap: 16px; }
.fp-size.fp-grid-size label { display: flex; align-items: center; gap: 8px; font-size: 14px; }
.fp-grid-size input { text-align: center; font-variant-numeric: tabular-nums; }
.fp-help { margin: 0; flex: 1 1 220px; }
.fp-size { border: 0; padding: 0; margin: 0; display: flex; gap: 8px; flex-wrap: wrap; }
.fp-size legend { color: var(--fp-muted); font-size: 12px; margin-bottom: 6px; }
.fp-size label { display: grid; gap: 5px; color: var(--fp-muted); font-size: 13px; font-weight: 500; }
.fp-size input { width: 70px; min-height: 36px; padding: 6px 8px; border-radius: 6px; border: 1px solid var(--fp-border); background: var(--fp-surface); color: var(--fp-text); font: inherit; font-size: 14px; }
.fp-legend { margin-bottom: 12px; }
.fp-legend > span:not(.fp-help)::before { content: ''; display: inline-block; width: 10px; height: 10px; margin-right: 6px; border: 1px solid var(--fp-border); background: var(--fp-room); }
.fp-legend > .administrative::before { background: var(--fp-admin) !important; }
.fp-scroll { grid-area: map; overflow: auto; max-height: 520px; min-width: 0; border: 1px solid var(--fp-border); border-radius: 12px; background: var(--fp-bg); overscroll-behavior: contain; }
.fp-grid { position: relative; width: 100%; min-width: calc(var(--columns) * 32px); aspect-ratio: var(--columns) / var(--rows); background-image: linear-gradient(to right, var(--fp-grid) 1px, transparent 1px), linear-gradient(to bottom, var(--fp-grid) 1px, transparent 1px); background-size: calc(100% / var(--columns)) calc(100% / var(--rows)); }
.floor-plan .fp-room { position: absolute; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 4px; min-height: 0; border-radius: 10px; border: 3px solid var(--fp-bg); outline: 1px solid var(--fp-border); outline-offset: -4px; background: var(--fp-room); color: var(--fp-room-ink); padding: 6px; overflow: hidden; }
.floor-plan .fp-room.administrative { background: var(--fp-admin); color: var(--fp-admin-ink); }
.fp-room strong { font-family: inherit; font-size: clamp(20px, 2.4vw, 30px); font-weight: 650; letter-spacing: -.025em; font-variant-numeric: tabular-nums; line-height: 1.15; }
.fp-room .fp-room-type { font-size: 13px; font-weight: 500; color: inherit; max-width: 100%; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.fp-room.is-small .fp-room-type { display: none; }
.fp-room.is-small strong { font-size: 15px; letter-spacing: -.02em; }
.floor-plan .fp-room.selected { outline: 2px solid var(--fp-accent); outline-offset: -4px; }
.floor-plan .fp-room:focus-visible { outline: 2px solid var(--fp-accent); outline-offset: -4px; }
.is-editing .fp-room { touch-action: none; cursor: grab; user-select: none; }
.is-editing .fp-room.dragging { opacity: .4; cursor: grabbing; }
.fp-preview { position: absolute; pointer-events: none; display: grid; place-items: center; color: var(--fp-accent); background: var(--fp-room); border: 2px dashed var(--fp-accent); border-radius: 5px; z-index: 1; font-size: 20px; }
.fp-preview.invalid { border-color: var(--fp-error); color: var(--fp-error); }
.fp-workspace { position: relative; }
.fp-inspector { position: sticky; top: calc(var(--fp-header-offset, 0px) + 8px); z-index: 8; display: grid; grid-template-columns: minmax(150px, 1fr) minmax(140px, 1fr) minmax(140px, 1fr); align-items: center; gap: 12px 20px; height: 120px; overflow: auto; box-sizing: border-box; padding: 14px 16px; margin-bottom: 16px; border: 1px solid var(--fp-border); border-radius: 12px; background: var(--fp-surface); }
.fp-inspector-heading { display: flex; flex-direction: column; align-items: flex-start; gap: 6px; min-width: 0; }
.fp-selection-hint { grid-column: 1 / -1; margin: 0; color: var(--fp-muted); font-size: 13px; }
.fp-inspector-heading strong { font-size: 16px; font-weight: 600; }
.fp-inspector .fp-size { min-width: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.fp-inspector .fp-size legend { font-size: 12px; font-weight: 600; color: var(--fp-text); margin-bottom: 6px; }
.fp-inspector input { width: 100%; min-width: 0; box-sizing: border-box; }
.floor-plan .fp-unplace { font-size: 13px; padding: 6px 10px; min-height: 34px; color: var(--fp-muted); }
.fp-unplaced { margin-top: 14px; }
.fp-unplaced p { font-size: 13px; color: var(--fp-muted); margin: 0 0 8px; }
.fp-unplaced p span { margin-left: 6px; font-variant-numeric: tabular-nums; }
.fp-room-list { display: flex; gap: 8px; flex-wrap: wrap; max-height: 180px; overflow: auto; padding: 3px; }
.fp-room-list button { display: flex; align-items: center; gap: 8px; }
.fp-room-list span { font-size: 12px; color: var(--fp-muted); }
.fp-room-list .selected { border-color: var(--fp-accent); outline: 1px solid var(--fp-accent); }
.floor-plan .muted { opacity: .4; }
.floor-plan .fp-room.is-match, .floor-plan .fp-room-list .is-match { border-color: var(--fp-accent); outline: 2px solid var(--fp-accent); outline-offset: -3px; background: color-mix(in srgb, var(--fp-room) 75%, var(--fp-accent) 25%); }
.floor-plan .fp-room.is-match.selected { outline-style: dashed; outline-offset: -5px; }
.fp-search-result { margin: 0 0 14px; font-size: 13px; color: var(--fp-accent); }
.fp-message { font-size: 14px; margin: 8px 0 14px; color: var(--fp-muted); }
.fp-error { color: var(--fp-error); }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
.fp-compass { display: grid; grid-template-areas: '. north .' 'west map east' '. south .'; grid-template-columns: 30px minmax(0, 1fr) 30px; gap: 10px; }
.fp-north { grid-area: north; }
.fp-south { grid-area: south; }
.fp-west { grid-area: west; }
.fp-east { grid-area: east; }
.fp-bearing { position: relative; display: flex; align-items: center; justify-content: center; min-width: 0; color: var(--fp-muted); font-size: 13px; font-weight: 600; }
.fp-bearing > span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100%; }
.floor-plan .fp-bearing > button { min-height: 30px; padding: 3px 6px; border: 0; border-radius: 6px; background: transparent; color: var(--fp-muted); max-width: 100%; font-size: 13px; font-weight: 600; }
.fp-bearing button span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fp-west, .fp-east { max-height: 280px; align-self: center; }
.fp-west > button, .fp-east > button, .fp-west > span, .fp-east > span { writing-mode: vertical-rl; }
.fp-west > button, .fp-west > span { transform: rotate(180deg); }
.fp-bearing .fp-icon { width: 13px; height: 13px; }
.fp-landmark-editor { width: min(320px, calc(100vw - 130px)); min-width: 0; box-sizing: border-box; writing-mode: horizontal-tb; }
.fp-landmark-editor .landmark-editor-title { display: block; }
.fp-landmark-editor .landmark-editor-row { min-width: 0; }
.fp-landmark-editor .landmark-editor-action { flex-shrink: 0; padding: 0; }
.floor-plan.is-dark .landmark-editor-popup { background: #0b1220; border-color: #1e3a8a; box-shadow: none; }
.floor-plan.is-dark .landmark-editor-title { color: #94a3b8; }
.floor-plan.is-dark .landmark-editor-input { background: #0b1220; color: #e2e8f0; border-color: #1e3a8a; box-shadow: none; }
.floor-plan.is-dark .landmark-editor-input:focus { background: #0f172a; border-color: #60a5fa; }
.floor-plan.is-dark .landmark-editor-action { background: #0b1220; border-color: #1e3a8a; color: #cbd5e1; }
.floor-plan.is-dark .landmark-editor-action.is-confirm { background: linear-gradient(135deg, #2563eb, #1d4ed8); border-color: transparent; color: #fff; }
.floor-plan.is-dark .landmark-editor-action:hover { background: #102554; border-color: #60a5fa; color: #e2e8f0; }
@media (hover: hover) { .floor-plan button:not(:disabled):hover { border-color: var(--fp-accent); } .floor-plan .fp-room:not(:disabled):hover { outline-color: var(--fp-accent); } }
@media (max-width: 600px) {
  .fp-scroll { max-height: 360px; }
  .fp-toolbar { align-items: start; }
  .fp-actions { width: 100%; }
  .floor-plan button:where(:not(.landmark-editor-action, .context-help-trigger)) { font-size: 13px; min-height: 40px; }
  .fp-size input { font-size: 16px; }
  .fp-size.fp-grid-size { gap: 12px; flex: 1; min-width: 0; }
  .fp-grid-size label { flex: 1; }
  .fp-grid-size input { min-width: 0; width: 60px; flex: 1; }
  .fp-editor { gap: 8px; align-items: center; }
  .fp-inspector { gap: 10px; padding: 10px 12px; height: 176px; grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fp-inspector-heading { grid-column: 1 / -1; flex-direction: row; align-items: center; justify-content: space-between; }
  .fp-inspector .fp-size { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); width: 100%; }
  .fp-inspector input { width: 100%; }
  .fp-room strong { font-size: 22px; }
  .fp-compass { grid-template-columns: 22px minmax(0, 1fr) 22px; gap: 5px; }
  .fp-landmark-editor { margin-inline: 0; }
  .fp-landmark-editor input { font-size: 16px; }
  .fp-caption strong { font-size: 20px; }
  .fp-help, .fp-caption span, .fp-legend { font-size: 13px; }
}
@media (prefers-reduced-motion: reduce) { .floor-plan button { transition: none; } }
</style>
