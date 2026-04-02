<script>
import api from "@/services/api";
import { useNotificationsStore } from "@/stores/notifications";

const FILTER_OPTIONS_ENDPOINT = "/analytics/hardware/filter-options";
const ANALYTICS_ENDPOINT = "/analytics/hardware";

const TYPE_META = Object.freeze({
  computer: { label: "Компьютер", tone: "type-tone-computer" },
  server: { label: "Сервер", tone: "type-tone-server" },
  switch: { label: "Коммутатор", tone: "type-tone-switch" },
  router: { label: "Роутер", tone: "type-tone-router" },
  tv: { label: "Телевизор", tone: "type-tone-tv" },
  projector: { label: "Проектор", tone: "type-tone-projector" },
  printer: { label: "Принтер", tone: "type-tone-printer" },
  other: { label: "Другое", tone: "type-tone-other" },
});

function createEmptyFilterOptions() {
  return {
    offices: [],
    floors: [],
    audiences: [],
    states: [],
    types: [],
    spec_filters: [],
  };
}

function createEmptySummary() {
  return {
    total: 0,
    working: 0,
    broken: 0,
    by_type: {},
  };
}

function createBaseFilters() {
  return {
    office_ids: [],
    floors: [],
    audience_ids: [],
    states: [],
    types: [],
  };
}

function createRangeDraft() {
  return {
    gte: "",
    lte: "",
  };
}

export default {
  name: "ManageHardwareAnalytics",

  data() {
    return {
      initializing: true,
      hasLoadedFilterOptions: false,
      loadingFilterOptions: false,
      loadingResults: false,

      filterOptionsError: null,
      resultsError: null,

      filterOptions: createEmptyFilterOptions(),
      filters: createBaseFilters(),
      specRanges: {},
      specBooleans: {},

      items: [],
      total: 0,
      summary: createEmptySummary(),
      pageSize: 100,
      hasMore: false,
    };
  },

  computed: {
    notify() {
      return useNotificationsStore();
    },

    selectedSingleType() {
      return this.filters.types.length === 1 ? this.filters.types[0] : null;
    },

    visibleSpecFilters() {
      if (!this.selectedSingleType) return [];

      return this.filterOptions.spec_filters.filter((field) =>
        Array.isArray(field.types) && field.types.includes(this.selectedSingleType)
      );
    },

    hasVisibleSpecFilters() {
      return this.visibleSpecFilters.length > 0;
    },

    summaryTypeEntries() {
      const byType = this.summary?.by_type ?? {};

      return Object.entries(byType)
        .map(([type, count]) => ({
          type,
          count: Number(count) || 0,
        }))
        .filter((entry) => entry.count > 0)
        .sort((left, right) => right.count - left.count);
    },

    resultsCaption() {
      if (!this.total) return "Совпадений пока нет";
      return `Показано ${this.items.length} из ${this.total}`;
    },
  },

  watch: {
    selectedSingleType(nextType, prevType) {
      if (nextType === prevType) return;
      this.pruneSpecFilters(nextType);
    },
  },

  methods: {
    async bootstrap() {
      this.initializing = true;
      await this.loadFilterOptions();

      if (!this.filterOptionsError) {
        await this.loadAnalytics();
      }

      this.initializing = false;
    },

    normalizeOptionList(list, { booleanValues = false } = {}) {
      if (!Array.isArray(list)) return [];

      return list
        .map((item) => {
          const rawValue = item?.value;
          const value = booleanValues ? this.coerceBooleanish(rawValue) : rawValue;

          return {
            value,
            label: item?.label ?? String(value ?? ""),
          };
        })
        .filter((item) => item.value !== undefined);
    },

    normalizeSpecFilters(list) {
      if (!Array.isArray(list)) return [];

      return list
        .map((field) => ({
          key: String(field?.key ?? ""),
          label: field?.label ?? String(field?.key ?? ""),
          kind: field?.kind ?? "range",
          unit: field?.unit ?? "",
          types: Array.isArray(field?.types) ? field.types : [],
        }))
        .filter((field) => field.key);
    },

    normalizeFilterOptions(data) {
      return {
        offices: this.normalizeOptionList(data?.offices),
        floors: this.normalizeOptionList(data?.floors),
        audiences: this.normalizeOptionList(data?.audiences),
        states: this.normalizeOptionList(data?.states, { booleanValues: true }),
        types: this.normalizeOptionList(data?.types),
        spec_filters: this.normalizeSpecFilters(data?.spec_filters),
      };
    },

    initializeSpecDrafts() {
      const nextRanges = {};
      const nextBooleans = {};

      for (const field of this.filterOptions.spec_filters) {
        if (field.kind === "range") {
          nextRanges[field.key] = createRangeDraft();
        } else if (field.kind === "boolean") {
          nextBooleans[field.key] = null;
        }
      }

      this.specRanges = nextRanges;
      this.specBooleans = nextBooleans;
    },

    resetFiltersState() {
      this.filters = createBaseFilters();
      this.initializeSpecDrafts();
    },

    async loadFilterOptions() {
      this.loadingFilterOptions = true;
      this.filterOptionsError = null;

      try {
        const res = await api.get(FILTER_OPTIONS_ENDPOINT);
        this.filterOptions = this.normalizeFilterOptions(res.data);
        this.hasLoadedFilterOptions = true;
        this.initializeSpecDrafts();
      } catch (error) {
        const message = error.response?.data?.detail || "Не удалось загрузить фильтры аналитики оборудования";
        this.filterOptionsError = message;
        this.hasLoadedFilterOptions = false;
        this.notify.error(message);
      } finally {
        this.loadingFilterOptions = false;
      }
    },

    normalizeAnalyticsResponse(data) {
      const items = Array.isArray(data?.items) ? data.items : [];
      const total = Number(data?.total);
      const summarySource = data?.summary ?? {};

      return {
        items,
        total: Number.isFinite(total) ? total : items.length,
        summary: {
          total: Number(summarySource.total ?? items.length) || 0,
          working: Number(summarySource.working ?? 0) || 0,
          broken: Number(summarySource.broken ?? 0) || 0,
          by_type: summarySource.by_type && typeof summarySource.by_type === "object"
            ? summarySource.by_type
            : {},
        },
      };
    },

    async loadAnalytics({ append = false } = {}) {
      if (this.loadingResults || this.loadingFilterOptions) return;

      this.loadingResults = true;

      if (!append) {
        this.resultsError = null;
      }

      try {
        const offset = append ? this.items.length : 0;
        const payload = this.buildAnalyticsPayload({
          limit: this.pageSize,
          offset,
        });

        const res = await api.post(ANALYTICS_ENDPOINT, payload);
        const normalized = this.normalizeAnalyticsResponse(res.data);

        if (append) {
          this.items.push(...normalized.items);
        } else {
          this.items = normalized.items;
        }

        this.total = normalized.total;
        this.summary = normalized.summary;
        this.hasMore = this.items.length < this.total;
      } catch (error) {
        const message = error.response?.data?.detail || "Не удалось загрузить результаты аналитики";
        this.resultsError = message;

        if (!append) {
          this.items = [];
          this.total = 0;
          this.summary = createEmptySummary();
          this.hasMore = false;
        }

        this.notify.error(message);
      } finally {
        this.loadingResults = false;
      }
    },

    retryAll() {
      this.bootstrap();
    },

    applyFilters() {
      this.loadAnalytics({ append: false });
    },

    async resetFilters() {
      this.resetFiltersState();
      await this.loadAnalytics({ append: false });
    },

    loadMore() {
      if (!this.hasMore || this.loadingResults) return;
      this.loadAnalytics({ append: true });
    },

    coerceBooleanish(value) {
      if (value === true || value === false) return value;
      if (value === "true") return true;
      if (value === "false") return false;
      return value;
    },

    valueKey(value) {
      if (typeof value === "boolean") return `bool:${value}`;
      return `value:${String(value)}`;
    },

    parseNumberValue(value) {
      if (value === "" || value === null || value === undefined) return null;
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : null;
    },

    normalizeArrayFilter(values, allValues, parser = (value) => value) {
      const normalized = [...new Set(
        (Array.isArray(values) ? values : [])
          .map(parser)
          .filter((value) => value !== null && value !== undefined && value !== "")
      )];

      if (!normalized.length) return null;

      if (Array.isArray(allValues) && allValues.length) {
        const allNormalized = [...new Set(
          allValues
            .map(parser)
            .filter((value) => value !== null && value !== undefined && value !== "")
        )];

        const currentKeys = normalized.map((value) => this.valueKey(value)).sort();
        const allKeys = allNormalized.map((value) => this.valueKey(value)).sort();

        if (
          currentKeys.length === allKeys.length &&
          currentKeys.every((value, index) => value === allKeys[index])
        ) {
          return null;
        }
      }

      return normalized;
    },

    normalizeRangeFilter(key) {
      const raw = this.specRanges[key] ?? createRangeDraft();
      const gte = this.parseNumberValue(raw.gte);
      const lte = this.parseNumberValue(raw.lte);

      if (gte === null && lte === null) return null;

      const range = {};
      if (gte !== null) range.gte = gte;
      if (lte !== null) range.lte = lte;

      return Object.keys(range).length ? range : null;
    },

    buildAnalyticsPayload({ limit = this.pageSize, offset = 0 } = {}) {
      const officeIds = this.normalizeArrayFilter(
        this.filters.office_ids,
        this.filterOptions.offices.map((item) => item.value),
        (value) => this.parseNumberValue(value)
      );

      const floors = this.normalizeArrayFilter(
        this.filters.floors,
        this.filterOptions.floors.map((item) => item.value),
        (value) => this.parseNumberValue(value)
      );

      const audienceIds = this.normalizeArrayFilter(
        this.filters.audience_ids,
        this.filterOptions.audiences.map((item) => item.value),
        (value) => this.parseNumberValue(value)
      );

      const states = this.normalizeArrayFilter(
        this.filters.states,
        this.filterOptions.states.map((item) => item.value),
        (value) => this.coerceBooleanish(value)
      );

      const types = this.normalizeArrayFilter(
        this.filters.types,
        this.filterOptions.types.map((item) => item.value),
        (value) => String(value)
      );

      const payload = {
        office_ids: officeIds,
        floors,
        audience_ids: audienceIds,
        states,
        types,
        limit,
        offset,
      };

      if (this.selectedSingleType) {
        for (const field of this.visibleSpecFilters) {
          if (field.kind === "range") {
            const range = this.normalizeRangeFilter(field.key);
            if (range) payload[field.key] = range;
            continue;
          }

          if (field.kind === "boolean") {
            const value = this.specBooleans[field.key];
            if (typeof value === "boolean") payload[field.key] = value;
          }
        }
      }

      return payload;
    },

    pruneSpecFilters(activeType) {
      const activeKeys = new Set(
        activeType
          ? this.filterOptions.spec_filters
            .filter((field) => Array.isArray(field.types) && field.types.includes(activeType))
            .map((field) => field.key)
          : []
      );

      const nextRanges = { ...this.specRanges };
      const nextBooleans = { ...this.specBooleans };

      for (const key of Object.keys(nextRanges)) {
        if (!activeKeys.has(key)) {
          nextRanges[key] = createRangeDraft();
        }
      }

      for (const key of Object.keys(nextBooleans)) {
        if (!activeKeys.has(key)) {
          nextBooleans[key] = null;
        }
      }

      this.specRanges = nextRanges;
      this.specBooleans = nextBooleans;
    },

    toggleArrayFilter(key, value) {
      const current = Array.isArray(this.filters[key]) ? [...this.filters[key]] : [];
      const targetIndex = current.findIndex((item) => item === value);

      if (targetIndex >= 0) {
        current.splice(targetIndex, 1);
      } else {
        current.push(value);
      }

      this.filters = {
        ...this.filters,
        [key]: current,
      };
    },

    setSpecBoolean(key, value) {
      this.specBooleans = {
        ...this.specBooleans,
        [key]: value,
      };
    },

    isArrayValueSelected(key, value) {
      return Array.isArray(this.filters[key]) && this.filters[key].includes(value);
    },

    getRangeStep(field) {
      return field.key === "cpu_frequency_ghz" ? 0.1 : 1;
    },

    getRangeInputMode(field) {
      return field.key === "cpu_frequency_ghz" ? "decimal" : "numeric";
    },

    getTypeMeta(type) {
      return TYPE_META[type] ?? { label: type, tone: "type-tone-other" };
    },

    getTypeLabel(type) {
      const predefined = TYPE_META[type]?.label;
      if (predefined) return predefined;

      const option = this.filterOptions.types.find((item) => item.value === type);
      return option?.label ?? type;
    },

    getTypeTone(type) {
      return this.getTypeMeta(type).tone;
    },

    getStateLabel(value) {
      return value ? "Исправен" : "Неисправен";
    },

    getSelectHint(selected, total) {
      if (!selected.length) return "Можно выбрать несколько значений";
      return `Выбрано ${selected.length} из ${total}`;
    },

    formatMemory(amount, unit) {
      if (amount === null || amount === undefined || amount === "") return null;
      if (!unit) return String(amount);
      return `${amount} ${String(unit).toUpperCase()}`;
    },

    formatSpecsSummary(item) {
      const specs = item?.specs ?? {};

      if (item?.type === "computer" || item?.type === "server") {
        const parts = [];

        if (specs.cpu_cores) parts.push(`${specs.cpu_cores} ядер`);
        if (specs.cpu_frequency_ghz) parts.push(`${specs.cpu_frequency_ghz} ГГц`);

        const ram = this.formatMemory(specs.ram_amount, specs.ram_unit);
        if (ram) parts.push(`${ram} RAM`);

        const storage = this.formatMemory(specs.storage_amount, specs.storage_unit);
        if (storage) parts.push(storage);

        if (specs.purchase_year) parts.push(`${specs.purchase_year}`);

        return parts.length ? parts.join(" • ") : "Характеристики не указаны";
      }

      if (item?.type === "switch") {
        const parts = [];

        if (specs.ports_count) parts.push(`${specs.ports_count} портов`);
        if (typeof specs.managed === "boolean") {
          parts.push(specs.managed ? "Управляемый" : "Неуправляемый");
        }

        return parts.length ? parts.join(" • ") : "Характеристики не указаны";
      }

      return item?.description || "Характеристики не указаны";
    },

    getSecondaryText(item) {
      if (item?.specs?.cpu_model) return item.specs.cpu_model;
      if (item?.description) return item.description;
      return "";
    },

    getItemTitle(item) {
      return item?.title || "Без названия";
    },

    getInvNumber(item) {
      return item?.inv_number || "—";
    },

    getOfficeText(item) {
      if (item?.office_address) return `№${item.office_id} - ${item.office_address}`;
      if (item?.office_id !== null && item?.office_id !== undefined) return `Корпус №${item.office_id}`;
      return "—";
    },

    getAudienceText(item) {
      if (item?.audience_id === null || item?.audience_id === undefined) return "—";
      return `№${item.audience_id}`;
    },

    openAudience(item) {
      if (item?.audience_id === null || item?.audience_id === undefined) return;
      this.$router.push({ name: "Audience", params: { audienceId: item.audience_id } });
    },
  },

  mounted() {
    this.bootstrap();
  },
};
</script>

<template>
  <div class="audit-card analytics-card">
    <div class="card-header">
      <div>
        <h2 class="section-title">Аналитика оборудования</h2>
        <p class="section-subtitle">Фильтрация оборудования по расположению, состоянию, типу и характеристикам</p>
      </div>

      <div class="header-actions">
        <button class="btn btn-secondary" @click="resetFilters" :disabled="loadingFilterOptions || loadingResults || !hasLoadedFilterOptions">
          Сбросить
        </button>
        <button class="btn btn-primary" @click="applyFilters" :disabled="loadingFilterOptions || loadingResults || !hasLoadedFilterOptions">
          <span v-if="loadingResults" class="spinner"></span>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 5h18"></path>
            <path d="M6 12h12"></path>
            <path d="M10 19h4"></path>
          </svg>
          {{ loadingResults ? 'Загрузка...' : 'Применить' }}
        </button>
      </div>
    </div>

    <div v-if="initializing && !hasLoadedFilterOptions" class="state-container">
      <div class="spinner-large"></div>
      <p>Загрузка фильтров аналитики...</p>
    </div>

    <div v-else-if="filterOptionsError && !hasLoadedFilterOptions" class="state-container error-state">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 9v4"></path>
        <path d="M12 17h.01"></path>
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"></path>
      </svg>
      <p>Не удалось подготовить экран аналитики</p>
      <span class="state-hint">{{ filterOptionsError }}</span>
      <button class="btn btn-secondary" @click="retryAll">Повторить</button>
    </div>

    <template v-else>
      <div class="filters-section analytics-filters">
        <div class="filters-grid filters-grid-primary">
          <div class="filter-group">
            <label>Корпус</label>
            <select v-model="filters.office_ids" class="form-select form-multiselect" multiple :size="Math.min(Math.max(filterOptions.offices.length, 4), 7)">
              <option v-for="office in filterOptions.offices" :key="office.value" :value="office.value">
                {{ office.label }}
              </option>
            </select>
            <span class="filter-hint">{{ getSelectHint(filters.office_ids, filterOptions.offices.length) }}</span>
          </div>

          <div class="filter-group">
            <label>Этаж</label>
            <select v-model="filters.floors" class="form-select form-multiselect" multiple :size="Math.min(Math.max(filterOptions.floors.length, 4), 7)">
              <option v-for="floor in filterOptions.floors" :key="floor.value" :value="floor.value">
                {{ floor.label }}
              </option>
            </select>
            <span class="filter-hint">{{ getSelectHint(filters.floors, filterOptions.floors.length) }}</span>
          </div>

          <div class="filter-group">
            <label>Аудитория</label>
            <select v-model="filters.audience_ids" class="form-select form-multiselect" multiple :size="Math.min(Math.max(filterOptions.audiences.length, 4), 7)">
              <option v-for="audience in filterOptions.audiences" :key="audience.value" :value="audience.value">
                {{ audience.label }}
              </option>
            </select>
            <span class="filter-hint">{{ getSelectHint(filters.audience_ids, filterOptions.audiences.length) }}</span>
          </div>
        </div>

        <div class="filters-grid filters-grid-secondary">
          <div class="filter-group filter-group-wide">
            <label>Состояние</label>
            <div class="chip-group">
              <button
                v-for="state in filterOptions.states"
                :key="String(state.value)"
                type="button"
                class="chip-toggle"
                :class="{ active: isArrayValueSelected('states', state.value) }"
                @click="toggleArrayFilter('states', state.value)"
              >
                {{ state.label || getStateLabel(state.value) }}
              </button>
            </div>
            <span class="filter-hint">Можно выбрать исправное, неисправное или оба состояния</span>
          </div>

          <div class="filter-group filter-group-wide">
            <label>Тип оборудования</label>
            <div class="chip-group">
              <button
                v-for="type in filterOptions.types"
                :key="type.value"
                type="button"
                class="chip-toggle"
                :class="[
                  getTypeTone(type.value),
                  { active: isArrayValueSelected('types', type.value) }
                ]"
                @click="toggleArrayFilter('types', type.value)"
              >
                {{ getTypeLabel(type.value) }}
              </button>
            </div>
            <span class="filter-hint">
              Фильтры по характеристикам показываются только при выборе ровно одного типа
            </span>
          </div>
        </div>

        <div v-if="selectedSingleType" class="spec-filters-panel">
          <div class="spec-filters-header">
            <div>
              <div class="spec-filters-title">Фильтрация по характеристикам</div>
              <div class="spec-filters-subtitle">
                Параметры показаны для типа {{ getTypeLabel(selectedSingleType).toLowerCase() }}
              </div>
            </div>
            <span class="type-pill" :class="getTypeTone(selectedSingleType)">
              {{ getTypeLabel(selectedSingleType) }}
            </span>
          </div>

          <div v-if="hasVisibleSpecFilters" class="spec-filters-grid">
            <div v-for="field in visibleSpecFilters" :key="field.key" class="spec-filter-card">
              <label class="spec-filter-label">{{ field.label }}</label>

              <div v-if="field.kind === 'range'" class="range-inputs">
                <div class="range-input-wrap">
                  <span class="range-prefix">От</span>
                  <input
                    v-model="specRanges[field.key].gte"
                    class="form-input"
                    type="number"
                    :step="getRangeStep(field)"
                    :inputmode="getRangeInputMode(field)"
                    placeholder="Не задано"
                  />
                </div>

                <div class="range-input-wrap">
                  <span class="range-prefix">До</span>
                  <input
                    v-model="specRanges[field.key].lte"
                    class="form-input"
                    type="number"
                    :step="getRangeStep(field)"
                    :inputmode="getRangeInputMode(field)"
                    placeholder="Не задано"
                  />
                </div>

                <span v-if="field.unit" class="filter-unit">{{ field.unit }}</span>
              </div>

              <div v-else-if="field.kind === 'boolean'" class="boolean-group">
                <button
                  type="button"
                  class="boolean-btn"
                  :class="{ active: specBooleans[field.key] === null }"
                  @click="setSpecBoolean(field.key, null)"
                >
                  Любой
                </button>
                <button
                  type="button"
                  class="boolean-btn"
                  :class="{ active: specBooleans[field.key] === true }"
                  @click="setSpecBoolean(field.key, true)"
                >
                  Да
                </button>
                <button
                  type="button"
                  class="boolean-btn"
                  :class="{ active: specBooleans[field.key] === false }"
                  @click="setSpecBoolean(field.key, false)"
                >
                  Нет
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="summary-grid">
        <div class="summary-card">
          <span class="summary-label">Всего</span>
          <strong class="summary-value">{{ summary.total }}</strong>
        </div>

        <div class="summary-card summary-card-good">
          <span class="summary-label">Исправно</span>
          <strong class="summary-value">{{ summary.working }}</strong>
        </div>

        <div class="summary-card summary-card-bad">
          <span class="summary-label">Неисправно</span>
          <strong class="summary-value">{{ summary.broken }}</strong>
        </div>
      </div>

      <div class="type-summary">
        <div class="section-row">
          <div>
            <h3 class="subsection-title">По типам</h3>
            <p class="subsection-subtitle">Сводка по текущей выборке</p>
          </div>
          <span class="section-row-caption">{{ resultsCaption }}</span>
        </div>

        <div v-if="summaryTypeEntries.length" class="type-summary-grid">
          <div
            v-for="entry in summaryTypeEntries"
            :key="entry.type"
            class="type-summary-card"
            :class="getTypeTone(entry.type)"
          >
            <span class="type-summary-label">{{ getTypeLabel(entry.type) }}</span>
            <strong class="type-summary-value">{{ entry.count }}</strong>
          </div>
        </div>

        <div v-else class="type-summary-empty">
          По выбранным фильтрам пока нет данных для распределения по типам
        </div>
      </div>

      <div class="results-section">
        <div class="section-row">
          <div>
            <h3 class="subsection-title">Результаты</h3>
            <p class="subsection-subtitle">Компактный список оборудования и ключевых характеристик</p>
          </div>
          <button class="btn btn-secondary btn-inline" @click="applyFilters" :disabled="loadingResults">
            Обновить
          </button>
        </div>

        <div v-if="resultsError && items.length" class="alert-box error">
          {{ resultsError }}
        </div>

        <div class="table-container analytics-table-wrapper">
          <table v-if="items.length" class="data-table analytics-table">
            <thead>
            <tr>
              <th width="150">Тип</th>
              <th>Наименование</th>
              <th width="150">Инв. номер</th>
              <th width="140">Состояние</th>
              <th>Корпус</th>
              <th width="90">Этаж</th>
              <th width="120">Аудитория</th>
              <th>Характеристики</th>
              <th width="120" class="text-right">Открыть</th>
            </tr>
            </thead>

            <tbody>
            <tr v-for="item in items" :key="item.id" class="table-row">
              <td>
                <span class="type-pill" :class="getTypeTone(item.type)">
                  {{ getTypeLabel(item.type) }}
                </span>
              </td>

              <td>
                <div class="title-cell">
                  <div class="title-main">{{ getItemTitle(item) }}</div>
                  <div v-if="getSecondaryText(item)" class="title-secondary">{{ getSecondaryText(item) }}</div>
                </div>
              </td>

              <td>
                <span class="code-badge">{{ getInvNumber(item) }}</span>
              </td>

              <td>
                <span class="state-pill" :class="item.state ? 'working' : 'broken'">
                  {{ getStateLabel(item.state) }}
                </span>
              </td>

              <td class="location-cell">{{ getOfficeText(item) }}</td>

              <td>
                <span class="badge-neutral">{{ item.floor ?? '—' }}</span>
              </td>

              <td>
                <span class="badge-neutral">{{ getAudienceText(item) }}</span>
              </td>

              <td>
                <div class="specs-cell">{{ formatSpecsSummary(item) }}</div>
              </td>

              <td class="text-right">
                <button
                  class="open-link"
                  type="button"
                  :disabled="item.audience_id === null || item.audience_id === undefined"
                  @click="openAudience(item)"
                >
                  Открыть
                </button>
              </td>
            </tr>
            </tbody>
          </table>

          <div v-else-if="loadingResults" class="state-container">
            <div class="spinner-large"></div>
            <p>Загрузка результатов аналитики...</p>
          </div>

          <div v-else-if="resultsError" class="state-container error-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 9v4"></path>
              <path d="M12 17h.01"></path>
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"></path>
            </svg>
            <p>Не удалось загрузить результаты</p>
            <span class="state-hint">{{ resultsError }}</span>
            <button class="btn btn-secondary" @click="applyFilters">Повторить</button>
          </div>

          <div v-else class="state-container empty">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 6h16"></path>
              <path d="M7 12h10"></path>
              <path d="M10 18h4"></path>
            </svg>
            <p>По выбранным фильтрам оборудование не найдено</p>
            <span class="state-hint">Измените параметры поиска или сбросьте фильтры</span>
          </div>

          <div v-if="hasMore && items.length" class="load-more-wrapper">
            <button class="btn btn-secondary load-more-btn" @click="loadMore" :disabled="loadingResults">
              <span v-if="loadingResults" class="spinner"></span>
              {{ loadingResults ? 'Загрузка...' : 'Показать ещё' }}
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.analytics-card {
  display: flex;
  flex-direction: column;
  gap: 24px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
  padding: 24px;
  color: #0f172a;
  font-family: system-ui, -apple-system, sans-serif;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.section-title {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 600;
}

.section-subtitle {
  margin: 0;
  font-size: 14px;
  color: #64748b;
}

.header-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.analytics-filters {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.filters-grid {
  display: grid;
  gap: 14px;
}

.filters-grid-primary {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.filters-grid-secondary {
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-group-wide {
  min-width: 0;
}

.filter-group label,
.spec-filter-label {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.form-select,
.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #ffffff;
  color: #0f172a;
  font-size: 14px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.form-multiselect {
  min-height: 140px;
  padding-right: 10px;
}

.form-multiselect option {
  padding: 8px 10px;
  border-radius: 6px;
}

.filter-hint,
.spec-filters-subtitle,
.subsection-subtitle,
.section-row-caption,
.filter-unit,
.title-secondary {
  color: #64748b;
  font-size: 13px;
}

.chip-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip-toggle,
.boolean-btn,
.open-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  padding: 8px 14px;
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  background: #ffffff;
  color: #475569;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.chip-toggle:hover,
.boolean-btn:hover,
.open-link:hover {
  border-color: #93c5fd;
  color: #1d4ed8;
  background: #eff6ff;
}

.chip-toggle.active,
.boolean-btn.active {
  background: #dbeafe;
  border-color: #60a5fa;
  color: #1d4ed8;
}

.spec-filters-panel {
  border: 1px solid #dbeafe;
  border-radius: 16px;
  padding: 18px;
  background: linear-gradient(180deg, rgba(239, 246, 255, 0.85), rgba(248, 250, 252, 0.96));
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.spec-filters-header,
.section-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.spec-filters-title,
.subsection-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}

.type-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 12px;
  font-weight: 700;
}

.spec-filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 14px;
}

.spec-filter-card,
.summary-card,
.type-summary-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 16px;
}

.range-inputs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  align-items: center;
}

.range-input-wrap {
  position: relative;
}

.range-input-wrap .form-input {
  padding-left: 38px;
}

.range-prefix {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
}

.boolean-group {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
}

.summary-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: relative;
  overflow: hidden;
}

.summary-card::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  background: #3b82f6;
}

.summary-card-good::before {
  background: #16a34a;
}

.summary-card-bad::before {
  background: #dc2626;
}

.summary-label {
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.summary-value {
  font-size: 30px;
  font-weight: 700;
  color: #0f172a;
}

.type-summary {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.type-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.type-summary-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.type-summary-label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}

.type-summary-value {
  font-size: 26px;
  font-weight: 700;
  color: #0f172a;
}

.type-summary-empty {
  padding: 16px 18px;
  border-radius: 12px;
  border: 1px dashed #cbd5e1;
  background: #f8fafc;
  color: #64748b;
  font-size: 14px;
}

.results-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 40px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn svg {
  width: 16px;
  height: 16px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #0f172a;
  color: #ffffff;
}

.btn-primary:hover:not(:disabled) {
  background: #334155;
}

.btn-secondary {
  background: #f1f5f9;
  color: #0f172a;
  border: 1px solid #e2e8f0;
}

.btn-secondary:hover:not(:disabled) {
  background: #e2e8f0;
}

.btn-inline {
  min-width: 112px;
}

.table-container {
  overflow-x: auto;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
}

.analytics-table-wrapper {
  border-radius: 14px;
}

.analytics-table {
  width: 100%;
  min-width: 1180px;
  border-collapse: collapse;
  text-align: left;
}

.analytics-table th {
  background: #f8fafc;
  padding: 14px 16px;
  font-size: 12px;
  font-weight: 700;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid #e2e8f0;
}

.analytics-table td {
  padding: 14px 16px;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: middle;
  font-size: 14px;
}

.table-row {
  transition: background-color 0.15s ease;
}

.table-row:hover {
  background: #f8fafc;
}

.text-right {
  text-align: right;
}

.title-cell,
.location-cell,
.specs-cell {
  min-width: 0;
}

.title-main {
  color: #0f172a;
  font-weight: 700;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.code-badge,
.badge-neutral,
.state-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 700;
  border: 1px solid transparent;
}

.code-badge {
  font-family: ui-monospace, monospace;
  background: #f8fafc;
  color: #334155;
  border-color: #e2e8f0;
}

.badge-neutral {
  background: #f1f5f9;
  color: #475569;
  border-color: #e2e8f0;
}

.state-pill.working {
  background: #dcfce7;
  color: #166534;
  border-color: #bbf7d0;
}

.state-pill.broken {
  background: #fee2e2;
  color: #b91c1c;
  border-color: #fecaca;
}

.specs-cell {
  color: #334155;
  line-height: 1.5;
}

.open-link {
  min-width: 88px;
}

.open-link:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.type-tone-computer {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.2);
  color: #1d4ed8;
}

.type-tone-server {
  background: rgba(20, 184, 166, 0.12);
  border-color: rgba(20, 184, 166, 0.2);
  color: #0f766e;
}

.type-tone-switch {
  background: rgba(245, 158, 11, 0.14);
  border-color: rgba(245, 158, 11, 0.24);
  color: #b45309;
}

.type-tone-router {
  background: rgba(6, 182, 212, 0.14);
  border-color: rgba(6, 182, 212, 0.24);
  color: #0e7490;
}

.type-tone-tv {
  background: rgba(249, 115, 22, 0.12);
  border-color: rgba(249, 115, 22, 0.22);
  color: #c2410c;
}

.type-tone-projector {
  background: rgba(139, 92, 246, 0.12);
  border-color: rgba(139, 92, 246, 0.2);
  color: #6d28d9;
}

.type-tone-printer {
  background: rgba(16, 185, 129, 0.12);
  border-color: rgba(16, 185, 129, 0.2);
  color: #047857;
}

.type-tone-other {
  background: rgba(100, 116, 139, 0.14);
  border-color: rgba(100, 116, 139, 0.24);
  color: #475569;
}

.state-container {
  padding: 42px 20px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #64748b;
}

.state-container p {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #334155;
}

.state-container svg {
  width: 44px;
  height: 44px;
  color: #cbd5e1;
}

.state-hint {
  font-size: 13px;
  color: #94a3b8;
}

.error-state svg {
  color: #f87171;
}

.alert-box {
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 14px;
}

.alert-box.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
}

.load-more-wrapper {
  padding: 16px;
  text-align: center;
  border-top: 1px solid #e2e8f0;
  background: #fafafa;
}

.load-more-btn {
  width: 100%;
  max-width: 280px;
}

.spinner,
.spinner-large {
  border-radius: 50%;
  border-style: solid;
  border-top-color: currentColor;
  animation: spin 0.8s linear infinite;
}

.spinner {
  width: 16px;
  height: 16px;
  border-width: 2px;
  border-color: rgba(255, 255, 255, 0.3);
}

.btn-secondary .spinner,
.load-more-btn .spinner {
  border-color: rgba(15, 23, 42, 0.18);
  border-top-color: currentColor;
}

.spinner-large {
  width: 34px;
  height: 34px;
  border-width: 3px;
  border-color: rgba(59, 130, 246, 0.18);
  border-top-color: #3b82f6;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

html[data-theme='dark'] .analytics-card .spec-filter-card,
html[data-theme='dark'] .analytics-card .summary-card,
html[data-theme='dark'] .analytics-card .type-summary-card {
  background: #0f172a;
  border-color: #334155;
}

html[data-theme='dark'] .analytics-card .spec-filters-panel {
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.86), rgba(17, 24, 39, 0.96));
  border-color: #334155;
}

html[data-theme='dark'] .analytics-card .section-subtitle,
html[data-theme='dark'] .analytics-card .filter-group label,
html[data-theme='dark'] .analytics-card .spec-filter-label,
html[data-theme='dark'] .analytics-card .filter-hint,
html[data-theme='dark'] .analytics-card .spec-filters-subtitle,
html[data-theme='dark'] .analytics-card .subsection-subtitle,
html[data-theme='dark'] .analytics-card .section-row-caption,
html[data-theme='dark'] .analytics-card .filter-unit,
html[data-theme='dark'] .analytics-card .title-secondary,
html[data-theme='dark'] .analytics-card .summary-label,
html[data-theme='dark'] .analytics-card .type-summary-label,
html[data-theme='dark'] .analytics-card .type-summary-empty,
html[data-theme='dark'] .analytics-card .state-hint {
  color: #94a3b8;
}

html[data-theme='dark'] .analytics-card .spec-filters-title,
html[data-theme='dark'] .analytics-card .subsection-title,
html[data-theme='dark'] .analytics-card .summary-value,
html[data-theme='dark'] .analytics-card .type-summary-value,
html[data-theme='dark'] .analytics-card .title-main,
html[data-theme='dark'] .analytics-card .specs-cell,
html[data-theme='dark'] .analytics-card .state-container p {
  color: #e2e8f0;
}

html[data-theme='dark'] .analytics-card .chip-toggle,
html[data-theme='dark'] .analytics-card .boolean-btn,
html[data-theme='dark'] .analytics-card .open-link {
  background: #0f172a;
  border-color: #334155;
  color: #cbd5e1;
}

html[data-theme='dark'] .analytics-card .chip-toggle:hover,
html[data-theme='dark'] .analytics-card .boolean-btn:hover,
html[data-theme='dark'] .analytics-card .open-link:hover {
  background: rgba(37, 99, 235, 0.18);
  border-color: #60a5fa;
  color: #dbeafe;
}

html[data-theme='dark'] .analytics-card .chip-toggle.active,
html[data-theme='dark'] .analytics-card .boolean-btn.active {
  background: rgba(37, 99, 235, 0.22);
  border-color: #60a5fa;
  color: #dbeafe;
}

html[data-theme='dark'] .analytics-card .code-badge {
  background: #111827;
  border-color: #334155;
  color: #cbd5e1;
}

html[data-theme='dark'] .analytics-card .badge-neutral {
  background: #1e293b;
  border-color: #334155;
  color: #cbd5e1;
}

html[data-theme='dark'] .analytics-card .state-pill.working {
  background: rgba(22, 163, 74, 0.18);
  border-color: rgba(74, 222, 128, 0.28);
  color: #86efac;
}

html[data-theme='dark'] .analytics-card .state-pill.broken {
  background: rgba(220, 38, 38, 0.2);
  border-color: rgba(248, 113, 113, 0.3);
  color: #fca5a5;
}

html[data-theme='dark'] .analytics-card .type-summary-empty,
html[data-theme='dark'] .analytics-card .load-more-wrapper {
  background: #0f172a;
  border-color: #334155;
}

html[data-theme='dark'] .analytics-card .alert-box.error {
  background: rgba(127, 29, 29, 0.28);
  border-color: rgba(248, 113, 113, 0.42);
  color: #fecaca;
}

html[data-theme='dark'] .analytics-card .state-container svg {
  color: #475569;
}

html[data-theme='dark'] .analytics-card .error-state svg {
  color: #f87171;
}

@media (max-width: 900px) {
  .spec-filters-grid,
  .summary-grid,
  .type-summary-grid {
    grid-template-columns: 1fr;
  }

  .range-inputs {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .analytics-card {
    padding: 18px;
    gap: 20px;
  }

  .section-title {
    font-size: 21px;
  }

  .header-actions,
  .section-row {
    width: 100%;
  }

  .header-actions .btn,
  .section-row .btn-inline {
    flex: 1;
  }

  .filters-grid-primary,
  .filters-grid-secondary {
    grid-template-columns: 1fr;
  }

  .boolean-group {
    grid-template-columns: 1fr;
  }

  .spec-filters-header {
    align-items: stretch;
  }

  .type-pill {
    align-self: flex-start;
  }
}
</style>
