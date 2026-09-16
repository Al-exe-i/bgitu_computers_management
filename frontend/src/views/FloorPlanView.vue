<script>
import api from '@/services/api.js';
import FloorPlan from '@/components/Common/FloorPlan.vue';
import EntityInfoModal from '@/components/Common/EntityInfoModal.vue';
import { FLOOR_INFO_FIELDS } from '@/config/locationInfo.js';
import { useAuthStore } from '@/stores/auth.js';
import { useNotificationsStore } from '@/stores/notifications.js';
import { officeFloor } from '@/utils/officeNavigation.js';
import { readFloorView, saveFloorView } from '@/utils/floorPlanViewState.js';

export default {
  name: 'FloorPlanView',
  components: { FloorPlan, EntityInfoModal },
  props: { officeNumber: { type: String, required: true }, floorNumber: { type: String, required: true } },
  data: () => ({ office: null, loading: true, error: '', search: '', requestId: 0,
    editState: { dirty: false, saving: false }, showInfo: false, fields: FLOOR_INFO_FIELDS }),
  computed: {
    viewKey() { return `${this.officeNumber}:${this.floorNumber}`; },
    floor() { return officeFloor(this.floorNumber); },
    floors() { return [...new Set((this.office?.audiences ?? []).map(room => room.floor))].sort((a, b) => a - b); },
    matchingIds() {
      const query = this.search.trim().toLowerCase();
      return query ? (this.office?.audiences ?? []).filter(room => room.floor === this.floor
        && String(room.number ?? room.id).toLowerCase().startsWith(query)).map(room => room.public_id) : null;
    },
    officeLocation() { return { name: 'Office', params: { officeNumber: this.officeNumber }, query: { floor: this.floorNumber } }; },
    canEditInfo() { const auth = useAuthStore(); return auth.isAuthenticated && auth.user?.role === 1; },
  },
  mounted() {
    this.load();
    window.addEventListener('beforeunload', this.beforeUnload);
    window.addEventListener('pagehide', this.remember);
  },
  beforeUnmount() {
    this.requestId++;
    window.removeEventListener('beforeunload', this.beforeUnload);
    window.removeEventListener('pagehide', this.remember);
  },
  beforeRouteLeave() { return this.allowLeave(); },
  beforeRouteUpdate(to, from) {
    return to.fullPath === from.fullPath || this.allowLeave();
  },
  watch: { '$route.fullPath'() { this.load(); } },
  methods: {
    async load() {
      const id = ++this.requestId;
      this.loading = true;
      this.error = '';
      this.office = null;
      this.showInfo = false;
      this.editState = { dirty: false, saving: false };
      const cached = readFloorView(this.viewKey);
      this.search = typeof this.$route.query.q === 'string' ? this.$route.query.q.slice(0, 100) : cached.search;
      if (!/^\d+$/.test(this.officeNumber) || Number(this.officeNumber) < 1 || this.floor === null) {
        this.error = 'Некорректный адрес схемы этажа.';
        this.loading = false;
        return;
      }
      try {
        const { data } = await api.get(`/offices/${this.officeNumber}`, { timeout: 15000 });
        if (id !== this.requestId) return;
        this.office = data;
        if (!this.floors.includes(this.floor)) this.error = 'В этом корпусе нет указанного этажа.';
      } catch (error) {
        if (id !== this.requestId) return;
        this.error = error.response?.status === 404 ? 'Корпус не найден.' : 'Не удалось загрузить этаж. Проверьте соединение и попробуйте ещё раз.';
      } finally {
        if (id === this.requestId) this.loading = false;
      }
    },
    remember() {
      if (this.loading || this.error) return;
      const scroll = this.$refs.plan?.$el.querySelector('.fp-scroll');
      saveFloorView(this.viewKey, { search: this.search, x: scroll?.scrollLeft ?? 0,
        y: scroll?.scrollTop ?? 0, pageY: window.scrollY });
    },
    async restorePosition() {
      const id = this.requestId;
      const state = readFloorView(this.viewKey);
      await this.$nextTick();
      if (id !== this.requestId) return;
      this.$refs.plan?.$el.querySelector('.fp-scroll')?.scrollTo({ left: state.x, top: state.y, behavior: 'instant' });
      window.scrollTo({ top: state.pageY, behavior: 'instant' });
    },
    allowLeave() {
      if (this.editState.saving) {
        useNotificationsStore().info('Дождитесь сохранения схемы этажа');
        return false;
      }
      if (this.editState.dirty && !window.confirm('На схеме есть несохранённые изменения. Уйти без сохранения?')) return false;
      this.remember();
      return true;
    },
    beforeUnload(event) {
      this.remember();
      if (!this.editState.dirty && !this.editState.saving) return;
      event.preventDefault();
      event.returnValue = '';
    },
    floorLocation(number) {
      return { name: 'FloorPlan', params: { officeNumber: this.officeNumber, floorNumber: String(number) }, query: { q: this.search } };
    },
    async selectFloor(event) {
      const number = Number(event.target.value);
      if (number !== this.floor) await this.$router.push(this.floorLocation(number));
      event.target.value = this.floorNumber;
    },
  },
};
</script>

<template>
  <div class="floor-page">
    <nav class="floor-breadcrumbs" aria-label="Навигация по корпусу">
      <RouterLink :to="officeLocation"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="m10 5-7 7 7 7M3 12h18"/></svg>Корпус №{{ officeNumber }}</RouterLink>
      <span aria-hidden="true">/</span><span aria-current="page">{{ floorNumber }} этаж</span>
    </nav>
    <div class="floor-page-heading">
      <div><h1>Схема этажа</h1><p>Расположение кабинетов · {{ floorNumber }} этаж</p></div>
      <button v-if="office && !error" type="button" class="floor-info-button" @click="showInfo = true" aria-label="Информация об этаже" title="Информация об этаже"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7v1"/></svg></button>
    </div>
    <div v-if="loading" class="floor-page-message" role="status">Загружаем этаж…</div>
    <div v-else-if="error" class="floor-page-message" role="alert"><p>{{ error }}</p><button type="button" @click="load">Повторить</button><RouterLink :to="officeLocation">К корпусу</RouterLink></div>
    <template v-else>
      <div class="floor-page-controls">
        <label class="floor-page-search"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></svg><input v-model="search" type="search" maxlength="100" aria-label="Поиск кабинета на этаже" placeholder="Найти кабинет…"></label>
        <nav v-if="floors.length <= 6" class="floor-tabs" aria-label="Этажи корпуса">
          <RouterLink v-for="number in floors" :key="number" :to="number === floor ? $route.fullPath : floorLocation(number)" :aria-label="`${number} этаж`" :aria-current="number === floor ? 'page' : undefined">{{ number }}<span> этаж</span></RouterLink>
        </nav>
        <label class="floor-select" :class="{ 'always-visible': floors.length > 6 }"><span>Этаж</span><select aria-label="Этаж корпуса" :value="floorNumber" :disabled="editState.saving" @change="selectFloor"><option v-for="number in floors" :key="number" :value="number">{{ number }} этаж</option></select><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg></label>
      </div>
      <div class="floor-page-canvas">
        <FloorPlan :key="viewKey" ref="plan" :office-id="Number(officeNumber)" :floor="floor" :matching-ids="matchingIds" :search-text="search" @edit-state="editState = $event" @ready="restorePosition" />
      </div>
    </template>
    <EntityInfoModal v-if="showInfo" kind="floor" :marker="floor" :title="`${floorNumber} этаж · корпус №${officeNumber}`" :endpoint="`/offices/${officeNumber}/floors/${floorNumber}/info`" :fields="fields" :editable="canEditInfo" @close="showInfo = false" />
  </div>
</template>

<style scoped>
.floor-page { --page-surface: #fff; --page-ink: #172d4c; --page-muted: #596d87; --page-line: #d2deed; --page-accent: #255bd8; --page-active: #eaf1fd; width: 100%; box-sizing: border-box; max-width: 1440px; margin: 0 auto; padding: 28px 32px 48px; color: var(--page-ink); }
html[data-theme='dark'] .floor-page { --page-surface: #111d30; --page-ink: #e1eafa; --page-muted: #a2b3cb; --page-line: #334760; --page-accent: #8ab6ff; --page-active: #203653; }
.floor-breadcrumbs { display: flex; align-items: center; gap: 12px; font-size: 14px; color: var(--page-muted); }
.floor-breadcrumbs a { display: inline-flex; align-items: center; gap: 8px; min-height: 36px; color: inherit; text-decoration: none; }
.floor-breadcrumbs svg, .floor-page-search svg { width: 20px; height: 20px; flex-shrink: 0; }
.floor-page-heading { display: flex; align-items: center; gap: 16px; margin: 20px 0 28px; }
.floor-page-heading h1 { margin: 0; font: inherit; font-size: clamp(26px, 3vw, 36px); font-weight: 650; letter-spacing: -.03em; line-height: 1.15; }
.floor-page-heading p { margin: 8px 0 0; font-size: 14px; color: var(--page-muted); }
.floor-info-button { display: grid; place-items: center; width: 40px; height: 40px; padding: 8px; border: 0; border-radius: 50%; background: var(--page-active); color: var(--page-accent); cursor: pointer; }
.floor-info-button svg { width: 22px; height: 22px; }
.floor-page-controls { display: flex; flex-wrap: wrap; align-items: center; gap: 16px; margin-bottom: 24px; }
.floor-page-search { display: flex; align-items: center; gap: 10px; flex: 1; max-width: 420px; min-width: 180px; padding: 0 14px; background: var(--page-surface); border: 1px solid var(--page-line); border-radius: 12px; color: var(--page-muted); }
.floor-page-search input { min-width: 0; width: 100%; min-height: 46px; border: 0; background: transparent; color: var(--page-ink); font: inherit; font-size: 15px; outline: none; box-shadow: none; }
.floor-page-search:focus-within { border-color: var(--page-accent); box-shadow: inset 0 0 0 1px var(--page-accent); }
.floor-page-search input:focus-visible { outline: none; }
.floor-tabs { display: flex; gap: 4px; padding: 4px; margin-left: auto; border-bottom: 1px solid var(--page-line); }
.floor-tabs a { padding: 10px 14px; border-radius: 8px; font-size: 14px; font-weight: 600; color: var(--page-muted); text-decoration: none; }
.floor-tabs a[aria-current] { color: var(--page-accent); background: var(--page-active); box-shadow: inset 0 -2px var(--page-accent); }
.floor-select { display: none; position: relative; align-items: center; gap: 10px; color: var(--page-muted); font-size: 14px; }
.floor-select.always-visible { display: flex; margin-left: auto; }
.floor-select select { appearance: none; padding: 10px 34px 10px 12px; min-height: 46px; border: 1px solid var(--page-line); border-radius: 10px; background: var(--page-surface); color: var(--page-ink); font: inherit; }
.floor-select svg { position: absolute; pointer-events: none; right: 12px; width: 16px; height: 16px; }
.floor-page-canvas { padding: 24px; border: 1px solid var(--page-line); border-radius: 20px; background: var(--page-surface); animation: floor-appear 180ms ease-out; }
.floor-page-canvas :deep(.fp-scroll) { max-height: min(70dvh, 850px); }
.floor-page-message { padding: 32px 0; color: var(--page-muted); }
.floor-page-message button { margin-right: 16px; padding: 10px 16px; background: var(--page-surface); border: 1px solid var(--page-line); border-radius: 10px; color: var(--page-ink); cursor: pointer; }
.floor-page-message a { color: var(--page-accent); }
.floor-page :is(a, button, select):focus-visible { outline: 2px solid var(--page-accent); outline-offset: 3px; }
@media (hover: hover) { .floor-breadcrumbs a:hover { color: var(--page-accent); } .floor-tabs a:hover { background: var(--page-active); } }
@media (max-width: 700px) { .floor-page { padding: 16px 12px 32px; } .floor-page-heading { margin: 16px 0 22px; } .floor-page-controls { gap: 10px; } .floor-page-search { max-width: none; min-width: 0; } .floor-page-search input { font-size: 16px; } .floor-tabs { display: none; } .floor-select { display: flex; } .floor-select > span { display: none; } .floor-page-canvas { padding: 16px 10px; border-radius: 14px; } .floor-page-canvas :deep(.fp-scroll) { max-height: 60dvh; } }
@keyframes floor-appear { from { opacity: 0; } to { opacity: 1; } }
@media (prefers-reduced-motion: reduce) { .floor-page-canvas { animation: none; } }
</style>
