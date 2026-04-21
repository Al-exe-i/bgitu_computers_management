<script>
import api from "@/services/api";
import { useNotificationsStore } from "@/stores/notifications";

const FILTER_OPTIONS_ENDPOINT = "/analytics/hardware/filter-options";
const ANALYTICS_ENDPOINT = "/analytics/hardware";

const TYPE_ICONS = Object.freeze({
  computer: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"></rect><path d="M8 21h8M12 17v4"></path></svg>',
  server: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M20 3H4a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2M4 9V5h16v4zm16 4H4a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-4a2 2 0 0 0-2-2M4 19v-4h16v4z"/><path fill="currentColor" d="M17 6h2v2h-2zm-3 0h2v2h-2zm3 10h2v2h-2zm-3 0h2v2h-2z"/></svg>',
  switch: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 36 36"><path fill="currentColor" d="M32.26 13.15A7.49 7.49 0 0 1 22.57 7H7.13a2 2 0 0 0-1.91 1.41L2.09 18.48a2 2 0 0 0-.09.59V27a2 2 0 0 0 2 2h28a2 2 0 0 0 2-2v-7.94a2 2 0 0 0-.09-.59ZM8.92 25h-1.8v-3h1.8Zm5 0h-1.8v-3h1.8Zm5 0h-1.8v-3h1.8Zm5 0H22.1v-3h1.8Zm5 0H27.1v-3h1.8ZM31 19.4H5V18h26Z"/><circle cx="30" cy="6" r="5" fill="currentColor"/><path fill="none" d="M0 0h36v36H0z"/></svg>',
  router: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 16 16"><g fill="currentColor"><path d="M5.525 3.025a3.5 3.5 0 0 1 4.95 0a.5.5 0 1 0 .707-.707a4.5 4.5 0 0 0-6.364 0a.5.5 0 0 0 .707.707"/><path d="M6.94 4.44a1.5 1.5 0 0 1 2.12 0a.5.5 0 0 0 .708-.708a2.5 2.5 0 0 0-3.536 0a.5.5 0 0 0 .707.707Z"/><path d="M2.974 2.342a.5.5 0 1 0-.948.316L3.806 8H1.5A1.5 1.5 0 0 0 0 9.5v2A1.5 1.5 0 0 0 1.5 13H2a.5.5 0 0 0 .5.5h2A.5.5 0 0 0 5 13h6a.5.5 0 0 0 .5.5h2a.5.5 0 0 0 .5-.5h.5a1.5 1.5 0 0 0 1.5-1.5v-2A1.5 1.5 0 0 0 14.5 8h-2.306l1.78-5.342a.5.5 0 1 0-.948-.316L11.14 8H4.86zM2.5 11a.5.5 0 1 1 0-1a.5.5 0 0 1 0 1m4.5-.5a.5.5 0 1 1 1 0a.5.5 0 0 1-1 0m2.5.5a.5.5 0 1 1 0-1a.5.5 0 0 1 0 1m1.5-.5a.5.5 0 1 1 1 0a.5.5 0 0 1-1 0m2 0a.5.5 0 1 1 1 0a.5.5 0 0 1-1 0"/><path d="M8.5 5.5a.5.5 0 1 1-1 0a.5.5 0 0 1 1 0"/></g></svg>',
  tv: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 1920 1536"><path fill="currentColor" d="M1792 1120V160q0-13-9.5-22.5T1760 128H160q-13 0-22.5 9.5T128 160v960q0 13 9.5 22.5t22.5 9.5h1600q13 0 22.5-9.5t9.5-22.5m128-960v960q0 66-47 113t-113 47h-736v128h352q14 0 23 9t9 23v64q0 14-9 23t-23 9H544q-14 0-23-9t-9-23v-64q0-14 9-23t23-9h352v-128H160q-66 0-113-47T0 1120V160Q0 94 47 47T160 0h1600q66 0 113 47t47 113"/></svg>',
  projector: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 16 16"><g fill="currentColor"><path d="M14 7.5a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0M2.5 6a.5.5 0 0 0 0 1h4a.5.5 0 0 0 0-1zm0 2a.5.5 0 0 0 0 1h4a.5.5 0 0 0 0-1z"/><path d="M0 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2a1 1 0 0 1-1 1h-1a1 1 0 0 1-1-1H5a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1a2 2 0 0 1-2-2zm2-1a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V6a1 1 0 0 0-1-1z"/></g></svg>',
  printer: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 16 16"><g fill="currentColor"><path d="M5 1a2 2 0 0 0-2 2v1h10V3a2 2 0 0 0-2-2zm6 8H5a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-3a1 1 0 0 0-1-1"/><path d="M0 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2h-1v-2a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v2H2a2 2 0 0 1-2-2zm2.5 1a.5.5 0 1 0 0-1a.5.5 0 0 0 0 1"/></g></svg>',
  other: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M10.358 9.938c1.082-.12 2.202-.12 3.284 0a.464.464 0 0 1 .409.4c.129 1.104.129 2.22 0 3.324a.464.464 0 0 1-.41.4a14.92 14.92 0 0 1-3.283 0a.464.464 0 0 1-.409-.4a14.324 14.324 0 0 1 0-3.324a.464.464 0 0 1 .41-.4"/><path fill="currentColor" fill-rule="evenodd" d="M15 2.25a.75.75 0 0 1 .75.75v2.927a2.929 2.929 0 0 1 2.308 2.323H21a.75.75 0 0 1 0 1.5h-2.788c.037.5.061 1 .073 1.5H20a.75.75 0 0 1 0 1.5h-1.715c-.012.5-.036 1-.073 1.5H21a.75.75 0 0 1 0 1.5h-2.942a2.929 2.929 0 0 1-2.308 2.323V21a.75.75 0 0 1-1.5 0v-2.774c-.498.035-.999.059-1.5.07V20a.75.75 0 0 1-1.5 0v-1.704a31.963 31.963 0 0 1-1.5-.07V21a.75.75 0 0 1-1.5 0v-2.927a2.929 2.929 0 0 1-2.308-2.323H3a.75.75 0 0 1 0-1.5h2.788c-.037-.5-.061-1-.074-1.5H4a.75.75 0 0 1 0-1.5h1.714c.013-.5.037-1 .074-1.5H3a.75.75 0 0 1 0-1.5h2.942A2.929 2.929 0 0 1 8.25 5.927V3a.75.75 0 0 1 1.5 0v2.774c.498-.035.999-.059 1.5-.07V4a.75.75 0 0 1 1.5 0v1.704c.501.011 1.002.035 1.5.07V3a.75.75 0 0 1 .75-.75m-1.192 6.197a16.407 16.407 0 0 0-3.616 0c-.898.1-1.626.808-1.732 1.717a15.808 15.808 0 0 0 0 3.672c.106.91.834 1.616 1.732 1.717c1.192.133 2.424.133 3.616 0a1.963 1.963 0 0 0 1.732-1.717c.143-1.22.143-2.452 0-3.672a1.963 1.963 0 0 0-1.732-1.717" clip-rule="evenodd"/></svg>',
});

const TYPE_META = Object.freeze({
  computer: { label: "Компьютер", tone: "type-tone-computer", icon: TYPE_ICONS.computer },
  server: { label: "Сервер", tone: "type-tone-server", icon: TYPE_ICONS.server },
  switch: { label: "Коммутатор", tone: "type-tone-switch", icon: TYPE_ICONS.switch },
  router: { label: "Роутер", tone: "type-tone-router", icon: TYPE_ICONS.router },
  tv: { label: "Телевизор", tone: "type-tone-tv", icon: TYPE_ICONS.tv },
  projector: { label: "Проектор", tone: "type-tone-projector", icon: TYPE_ICONS.projector },
  printer: { label: "Принтер", tone: "type-tone-printer", icon: TYPE_ICONS.printer },
  other: { label: "Другое", tone: "type-tone-other", icon: TYPE_ICONS.other },
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
      activeSpecProfileId: "",

      showDetailsModal: false,
      selectedItem: null,
    };
  },

  computed: {
    notify() {
      return useNotificationsStore();
    },

    selectedSpecProfiles() {
      const selectedTypes = Array.isArray(this.filters.types)
        ? this.filters.types.map((value) => String(value))
        : [];

      if (!selectedTypes.length) return [];

      const orderMap = new Map(selectedTypes.map((type, index) => [type, index]));
      const profiles = new Map();

      for (const field of this.filterOptions.spec_filters) {
        const fieldTypes = Array.isArray(field.types) ? field.types.map((type) => String(type)) : [];
        const matchedTypes = selectedTypes.filter((type) => fieldTypes.includes(type));

        if (!matchedTypes.length) continue;

        const profileId = [...new Set(fieldTypes)].sort().join("|");

        if (!profiles.has(profileId)) {
          profiles.set(profileId, {
            id: profileId,
            fieldTypes: [...new Set(fieldTypes)],
            selectedTypes: [],
            fields: [],
          });
        }

        const profile = profiles.get(profileId);
        profile.fields.push(field);

        for (const type of matchedTypes) {
          if (!profile.selectedTypes.includes(type)) {
            profile.selectedTypes.push(type);
          }
        }
      }

      return Array.from(profiles.values())
        .map((profile) => ({
          ...profile,
          label: profile.selectedTypes.map((type) => this.getTypeLabel(type)).join(" / "),
          tone: profile.selectedTypes.length === 1
            ? this.getTypeTone(profile.selectedTypes[0])
            : "type-tone-other",
        }))
        .sort((left, right) => {
          const leftIndex = Math.min(...left.selectedTypes.map((type) => orderMap.get(type) ?? Number.MAX_SAFE_INTEGER));
          const rightIndex = Math.min(...right.selectedTypes.map((type) => orderMap.get(type) ?? Number.MAX_SAFE_INTEGER));
          return leftIndex - rightIndex;
        });
    },

    currentSpecProfile() {
      if (!this.selectedSpecProfiles.length) return null;
      return this.selectedSpecProfiles.find((profile) => profile.id === this.activeSpecProfileId) ?? this.selectedSpecProfiles[0];
    },

    visibleSpecFilters() {
      return this.currentSpecProfile?.fields ?? [];
    },

    hasVisibleSpecFilters() {
      return this.visibleSpecFilters.length > 0;
    },

    specFiltersHint() {
      if (!Array.isArray(this.filters.types) || !this.filters.types.length) {
        return "Фильтры по характеристикам появятся после выбора хотя бы одного типа оборудования";
      }

      if (!this.selectedSpecProfiles.length) {
        return "Для выбранных типов дополнительные фильтры по характеристикам пока не доступны";
      }

      if (this.selectedSpecProfiles.length > 1) {
        return "Можно переключаться между наборами характеристик выбранных типов";
      }

      return `Фильтры по характеристикам доступны для типа ${this.currentSpecProfile.label.toLowerCase()}`;
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
    activeFilterBadges() {
      const badges = [];
      const arrayFields = [
        {
          key: "office_ids",
          options: this.filterOptions.offices,
          labelBuilder: (label) => `Корпус ${label}`,
        },
        {
          key: "floors",
          options: this.filterOptions.floors,
          labelBuilder: (label) => `Этаж ${label}`,
        },
        {
          key: "audience_ids",
          options: this.filterOptions.audiences,
          labelBuilder: (label) => `Аудитория ${label}`,
        },
        {
          key: "states",
          options: this.filterOptions.states,
          labelBuilder: (label) => label,
        },
        {
          key: "types",
          options: this.filterOptions.types,
          labelBuilder: (_label, value) => this.getTypeLabel(value),
        },
      ];

      for (const field of arrayFields) {
        const selected = Array.isArray(this.filters[field.key]) ? this.filters[field.key] : [];

        for (const value of selected) {
          badges.push({
            id: `${field.key}:${this.valueKey(value)}`,
            kind: "array",
            key: field.key,
            value,
            label: field.labelBuilder(this.getOptionLabel(field.options, value), value),
          });
        }
      }

      if (this.currentSpecProfile) {
        for (const field of this.visibleSpecFilters) {
          if (field.kind === "range") {
            const range = this.normalizeRangeFilter(field.key);
            if (!range) continue;

            badges.push({
              id: `range:${field.key}`,
              kind: "range",
              key: field.key,
              label: this.getRangeBadgeLabel(field, range),
            });
            continue;
          }

          if (field.kind === "boolean") {
            const value = this.specBooleans[field.key];
            if (typeof value !== "boolean") continue;

            badges.push({
              id: `boolean:${field.key}`,
              kind: "boolean",
              key: field.key,
              label: `${field.label}: ${value ? "Да" : "Нет"}`,
            });
          }
        }
      }

      return badges;
    },

    activeFiltersCount() {
      return this.activeFilterBadges.length;
    },
  },

  watch: {
    "filters.types": {
      handler() {
        const availableIds = this.selectedSpecProfiles.map((profile) => profile.id);

        if (!availableIds.length) {
          this.activeSpecProfileId = "";
        } else if (!availableIds.includes(this.activeSpecProfileId)) {
          this.activeSpecProfileId = availableIds[0];
        }

        this.pruneSpecFilters();
      },
      deep: true,
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
      this.activeSpecProfileId = "";
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
      if (!Number.isFinite(parsed) || parsed < 0) return null;
      return parsed;
    },

    sanitizeRangeInput(key, edge) {
      const current = this.specRanges[key]?.[edge];
      if (current === "" || current === null || current === undefined) return;

      const parsed = Number(current);
      if (!Number.isFinite(parsed)) return;

      if (parsed < 0) {
        this.specRanges = {
          ...this.specRanges,
          [key]: {
            ...(this.specRanges[key] ?? createRangeDraft()),
            [edge]: "0",
          },
        };
      }
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

      if (this.currentSpecProfile) {
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

    pruneSpecFilters() {
      const activeKeys = new Set(
        this.selectedSpecProfiles.flatMap((profile) => profile.fields.map((field) => field.key))
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

    setActiveSpecProfile(profileId) {
      this.activeSpecProfileId = profileId;
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

    getTypeIcon(type) {
      return this.getTypeMeta(type).icon ?? TYPE_ICONS.other;
    },

    getStateLabel(value) {
      return value ? "Исправен" : "Неисправен";
    },

    getSummaryShare(value) {
      if (!this.summary.total) return "0%";
      return `${Math.round((Number(value) / this.summary.total) * 100)}%`;
    },

    getOptionLabel(options, value) {
      const list = Array.isArray(options) ? options : [];
      const targetKey = this.valueKey(value);
      const matched = list.find((item) => this.valueKey(item.value) === targetKey);
      return matched?.label ?? String(value ?? "—");
    },

    getFacetSummary(key, options, emptyLabel = "Все") {
      const selected = Array.isArray(this.filters[key]) ? this.filters[key] : [];

      if (!selected.length) return emptyLabel;
      if (selected.length === 1) return this.getOptionLabel(options, selected[0]);
      return `${selected.length} выбрано`;
    },

    getRangeBadgeLabel(field, range) {
      const parts = [];

      if (range.gte !== undefined) parts.push(`от ${range.gte}`);
      if (range.lte !== undefined) parts.push(`до ${range.lte}`);

      const suffix = field.unit ? ` ${field.unit}` : "";
      return `${field.label}: ${parts.join(" ")}${suffix}`;
    },

    clearRangeFilter(key) {
      this.specRanges = {
        ...this.specRanges,
        [key]: createRangeDraft(),
      };
    },

    removeFilterBadge(badge) {
      if (!badge || !badge.kind) return;

      if (badge.kind === "array") {
        this.toggleArrayFilter(badge.key, badge.value);
        return;
      }

      if (badge.kind === "range") {
        this.clearRangeFilter(badge.key);
        return;
      }

      if (badge.kind === "boolean") {
        this.setSpecBoolean(badge.key, null);
      }
    },

    scrollToResultsTop() {
      this.scrollToAnchor("resultsTopAnchor", "start");
    },

    scrollToResultsBottom() {
      this.scrollToAnchor("resultsBottomAnchor", "end");
    },

    scrollToAnchor(refName, block = "start") {
      const target = Array.isArray(this.$refs[refName]) ? this.$refs[refName][0] : this.$refs[refName];
      if (!target?.scrollIntoView) return;

      target.scrollIntoView({
        behavior: "smooth",
        block,
      });
    },

    formatMemory(amount, unit) {
      if (amount === null || amount === undefined || amount === "") return null;
      if (!unit) return String(amount);
      return `${amount} ${String(unit).toUpperCase()}`;
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
      if (item?.office_id !== null && item?.office_id !== undefined) return `№${item.office_id}`;
      return "—";
    },

    getAudienceText(item) {
      if (item?.audience_id === null || item?.audience_id === undefined) return "—";
      return `№${item.audience_id}`;
    },

    openDetails(item) {
      this.selectedItem = item;
      this.showDetailsModal = true;
      document.body.style.overflow = "hidden";
    },

    closeDetails() {
      this.showDetailsModal = false;
      this.selectedItem = null;
      document.body.style.overflow = "";
    },

    getDetailSpecsEntries(item) {
      const specs = item?.specs ?? {};

      if (item?.type === "computer" || item?.type === "server") {
        return [
          { label: "Модель CPU", value: specs.cpu_model || "—" },
          { label: "Частота CPU", value: specs.cpu_frequency_ghz ? `${specs.cpu_frequency_ghz} ГГц` : "—" },
          { label: "Ядра CPU", value: specs.cpu_cores || "—" },
          { label: "ОЗУ", value: this.formatMemory(specs.ram_amount, specs.ram_unit) || "—" },
          { label: "ПЗУ", value: this.formatMemory(specs.storage_amount, specs.storage_unit) || "—" },
          { label: "Год закупки", value: specs.purchase_year || "—" },
        ];
      }

      if (item?.type === "switch") {
        return [
          { label: "Кол-во портов", value: specs.ports_count || "—" },
          { label: "Управляемый", value: typeof specs.managed === "boolean" ? (specs.managed ? "Да" : "Нет") : "—" },
        ];
      }

      return Object.entries(specs).map(([key, value]) => ({
        label: key,
        value: value === null || value === undefined || value === "" ? "—" : String(value),
      }));
    },

    getPlacementText(item) {
      if (!item) return "—";
      return `Ряд ${(item.y ?? 0) + 1} • Место ${(item.x ?? 0) + 1} • Размер ${item.width ?? 1}×${item.height ?? 1}`;
    },

    openAudience(item) {
      if (item?.audience_id === null || item?.audience_id === undefined) return;
      this.$router.push({ name: "Audience", params: { audienceId: item.audience_id } });
    },
  },

  mounted() {
    this.bootstrap();
  },

  beforeUnmount() {
    document.body.style.overflow = "";
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
        <div class="filters-shell">
          <div class="filters-topline">
            <div>
              <h3 class="subsection-title">Фильтры</h3>
            </div>

            <div class="filters-topline-meta">
              <span class="filters-counter">{{ activeFiltersCount }} активных</span>
              <span class="filters-apply-note">Новые условия попадут в выдачу после кнопки «Применить»</span>
            </div>
          </div>

          <div class="quick-filter-shelf">
            <div class="quick-filter-row">
              <span class="quick-filter-label">Состояние</span>
              <div class="chip-group chip-group-compact">
                <button
                  v-for="state in filterOptions.states"
                  :key="`quick-state-${String(state.value)}`"
                  type="button"
                  class="chip-toggle"
                  :class="{ active: isArrayValueSelected('states', state.value) }"
                  @click="toggleArrayFilter('states', state.value)"
                >
                  {{ state.label || getStateLabel(state.value) }}
                </button>
              </div>
            </div>

            <div class="quick-filter-row">
              <span class="quick-filter-label">Тип</span>
              <div class="chip-group chip-group-compact">
                <button
                  v-for="type in filterOptions.types"
                  :key="`quick-type-${type.value}`"
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
            </div>

            <div class="quick-filter-note">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="9"></circle>
                <path d="M12 8h.01"></path>
                <path d="M11.5 11h1v5"></path>
              </svg>
              <span>
                {{ specFiltersHint }}
              </span>
            </div>
          </div>

          <div class="facet-toolbar">
            <details class="facet-panel">
              <summary class="facet-trigger">
                <div class="facet-trigger-copy">
                  <span class="facet-label">Корпус</span>
                  <span class="facet-value">{{ getFacetSummary('office_ids', filterOptions.offices, 'Все корпуса') }}</span>
                </div>
                <span v-if="filters.office_ids.length" class="facet-count">{{ filters.office_ids.length }}</span>
                <svg class="facet-chevron" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="m5 7.5 5 5 5-5"></path>
                </svg>
              </summary>

              <div class="facet-menu">
                <div class="facet-menu-head">
                  <strong>Корпуса</strong>
                </div>

                <div v-if="filterOptions.offices.length" class="facet-option-list">
                  <label
                    v-for="office in filterOptions.offices"
                    :key="`facet-office-${office.value}`"
                    class="facet-option"
                  >
                    <input
                      class="facet-checkbox"
                      type="checkbox"
                      :checked="isArrayValueSelected('office_ids', office.value)"
                      @change="toggleArrayFilter('office_ids', office.value)"
                    />
                    <span>{{ office.label }}</span>
                  </label>
                </div>

                <div v-else class="facet-empty">Нет доступных корпусов</div>
              </div>
            </details>

            <details class="facet-panel">
              <summary class="facet-trigger">
                <div class="facet-trigger-copy">
                  <span class="facet-label">Этаж</span>
                  <span class="facet-value">{{ getFacetSummary('floors', filterOptions.floors, 'Все этажи') }}</span>
                </div>
                <span v-if="filters.floors.length" class="facet-count">{{ filters.floors.length }}</span>
                <svg class="facet-chevron" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="m5 7.5 5 5 5-5"></path>
                </svg>
              </summary>

              <div class="facet-menu">
                <div class="facet-menu-head">
                  <strong>Этажи</strong>
                </div>

                <div v-if="filterOptions.floors.length" class="facet-option-list">
                  <label
                    v-for="floor in filterOptions.floors"
                    :key="`facet-floor-${floor.value}`"
                    class="facet-option"
                  >
                    <input
                      class="facet-checkbox"
                      type="checkbox"
                      :checked="isArrayValueSelected('floors', floor.value)"
                      @change="toggleArrayFilter('floors', floor.value)"
                    />
                    <span>{{ floor.label }}</span>
                  </label>
                </div>

                <div v-else class="facet-empty">Нет доступных этажей</div>
              </div>
            </details>

            <details class="facet-panel facet-panel-wide">
              <summary class="facet-trigger">
                <div class="facet-trigger-copy">
                  <span class="facet-label">Аудитория</span>
                  <span class="facet-value">{{ getFacetSummary('audience_ids', filterOptions.audiences, 'Все аудитории') }}</span>
                </div>
                <span v-if="filters.audience_ids.length" class="facet-count">{{ filters.audience_ids.length }}</span>
                <svg class="facet-chevron" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="m5 7.5 5 5 5-5"></path>
                </svg>
              </summary>

              <div class="facet-menu">
                <div class="facet-menu-head">
                  <strong>Аудитории</strong>
                </div>

                <div v-if="filterOptions.audiences.length" class="facet-option-list facet-option-list-tall">
                  <label
                    v-for="audience in filterOptions.audiences"
                    :key="`facet-audience-${audience.value}`"
                    class="facet-option"
                  >
                    <input
                      class="facet-checkbox"
                      type="checkbox"
                      :checked="isArrayValueSelected('audience_ids', audience.value)"
                      @change="toggleArrayFilter('audience_ids', audience.value)"
                    />
                    <span>{{ audience.label }}</span>
                  </label>
                </div>

                <div v-else class="facet-empty">Нет доступных аудиторий</div>
              </div>
            </details>
          </div>

          <div class="filters-actions">
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

          <div v-if="activeFilterBadges.length" class="active-filters-strip">
            <span class="active-filters-label">Активные условия</span>
            <button
              v-for="badge in activeFilterBadges"
              :key="badge.id"
              type="button"
              class="active-filter-chip"
              @click="removeFilterBadge(badge)"
            >
              <span>{{ badge.label }}</span>
              <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 6l8 8"></path>
                <path d="m14 6-8 8"></path>
              </svg>
            </button>

            <button type="button" class="filters-clear-inline" @click="resetFilters">
              Сбросить всё
            </button>
          </div>
        </div>
        <div v-if="selectedSpecProfiles.length" class="spec-filters-panel">
          <div class="spec-filters-header">
            <div>
              <div class="spec-filters-title">Характеристики</div>
              <div class="spec-filters-subtitle">
                {{ selectedSpecProfiles.length > 1
                  ? 'Переключайтесь между профилями характеристик выбранных типов'
                  : `Параметры для типа ${currentSpecProfile.label.toLowerCase()}` }}
              </div>
            </div>
            <span class="type-pill" :class="currentSpecProfile.tone">
              {{ currentSpecProfile.label }}
            </span>
          </div>

          <div v-if="selectedSpecProfiles.length > 1" class="spec-profile-switcher">
            <button
              v-for="profile in selectedSpecProfiles"
              :key="profile.id"
              type="button"
              class="spec-profile-tab"
              :class="[profile.tone, { active: currentSpecProfile && currentSpecProfile.id === profile.id }]"
              @click="setActiveSpecProfile(profile.id)"
            >
              {{ profile.label }}
            </button>
          </div>

          <div v-if="hasVisibleSpecFilters" class="spec-filters-grid">
            <div v-for="field in visibleSpecFilters" :key="field.key" class="spec-filter-card">
              <div class="spec-filter-head">
                <label class="spec-filter-label">{{ field.label }}</label>
                <span v-if="field.unit" class="spec-unit-chip">{{ field.unit }}</span>
              </div>

              <div v-if="field.kind === 'range'" class="range-inputs range-inputs-compact">
                <label class="range-chip-field">
                  <span class="range-chip-caption">От</span>
                  <input
                    v-model="specRanges[field.key].gte"
                    class="form-input spec-range-input"
                    type="number"
                    min="0"
                    :step="getRangeStep(field)"
                    :inputmode="getRangeInputMode(field)"
                    placeholder="Минимум"
                    @input="sanitizeRangeInput(field.key, 'gte')"
                  />
                </label>

                <label class="range-chip-field">
                  <span class="range-chip-caption">До</span>
                  <input
                    v-model="specRanges[field.key].lte"
                    class="form-input spec-range-input"
                    type="number"
                    min="0"
                    :step="getRangeStep(field)"
                    :inputmode="getRangeInputMode(field)"
                    placeholder="Максимум"
                    @input="sanitizeRangeInput(field.key, 'lte')"
                  />
                </label>
              </div>

              <div v-else-if="field.kind === 'boolean'" class="boolean-group boolean-group-compact">
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
        <div class="summary-card summary-card-total">
          <span class="summary-icon summary-icon-equipment" aria-hidden="true" v-html="getTypeIcon('other')"></span>
          <div class="summary-copy">
            <span class="summary-label">Всего</span>
            <div class="summary-value-row">
              <strong class="summary-value">{{ summary.total }}</strong>
              <span class="summary-meta">в выборке</span>
            </div>
          </div>
        </div>

        <div class="summary-card summary-card-good">
          <span class="summary-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="8"></circle>
              <path d="m8.8 12.3 2.2 2.2 4.3-4.6"></path>
            </svg>
          </span>
          <div class="summary-copy">
            <span class="summary-label">Исправно</span>
            <div class="summary-value-row">
              <strong class="summary-value">{{ summary.working }}</strong>
              <span class="summary-meta">{{ getSummaryShare(summary.working) }}</span>
            </div>
          </div>
        </div>

        <div class="summary-card summary-card-bad">
          <span class="summary-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 4.5 20 18H4z"></path>
              <path d="M12 9v4"></path>
              <path d="M12 16h.01"></path>
            </svg>
          </span>
          <div class="summary-copy">
            <span class="summary-label">Неисправно</span>
            <div class="summary-value-row">
              <strong class="summary-value">{{ summary.broken }}</strong>
              <span class="summary-meta">{{ getSummaryShare(summary.broken) }}</span>
            </div>
          </div>
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
            <span class="type-summary-icon" aria-hidden="true" v-html="getTypeIcon(entry.type)"></span>
            <div class="type-summary-copy">
              <span class="type-summary-label">{{ getTypeLabel(entry.type) }}</span>
              <span class="type-summary-meta">в выборке</span>
            </div>
            <strong class="type-summary-value">{{ entry.count }}</strong>
          </div>
        </div>

        <div v-else class="type-summary-empty">
          По выбранным фильтрам пока нет данных для распределения по типам
        </div>
      </div>

      <div class="results-section">
        <div ref="resultsTopAnchor" class="results-anchor"></div>

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
              <th width="48" title="Корпус">Корп.</th>
              <th width="52" title="Аудитория">Ауд.</th>
              <th width="55">Тип</th>
              <th width="54" title="Инвентарный номер">Инв.</th>
              <th width="55" class="text-center">Сост.</th>
              <th width="32" title="Этаж">Этаж</th>
              <th width="108" class="text-center">Действия</th>
            </tr>
            </thead>

            <tbody>
            <tr v-for="item in items" :key="item.id" class="table-row">
              <td class="location-cell">{{ getOfficeText(item) }}</td>

              <td>
                <span class="badge-neutral">{{ getAudienceText(item) }}</span>
              </td>

              <td>
                <span class="type-pill" :class="getTypeTone(item.type)">
                  {{ getTypeLabel(item.type) }}
                </span>
              </td>

              <td>
                <span class="code-badge" :title="getInvNumber(item)">{{ getInvNumber(item) }}</span>
              </td>

              <td class="text-center state-dot-cell">
                <span
                  class="state-dot"
                  :class="item.state ? 'working' : 'broken'"
                  :title="getStateLabel(item.state)"
                  :aria-label="getStateLabel(item.state)"
                ></span>
              </td>

              <td>
                <span class="badge-neutral">{{ item.floor ?? '—' }}</span>
              </td>

              <td class="actions-cell">
                <div class="row-actions">
                  <button
                    class="open-link details-btn"
                    type="button"
                    @click="openDetails(item)"
                  >
                    Открыть
                  </button>
                  <button
                    class="open-link audience-link-btn"
                    type="button"
                    :disabled="item.audience_id === null || item.audience_id === undefined"
                    @click="openAudience(item)"
                    aria-label="Перейти к аудитории"
                    title="Перейти к аудитории"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M5 12h14"></path>
                      <path d="m12 5 7 7-7 7"></path>
                    </svg>
                  </button>

                </div>
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

        <div ref="resultsBottomAnchor" class="results-anchor results-anchor-bottom"></div>
      </div>
    </template>

    <Teleport to="body">
      <div
        v-if="items.length > 10 || hasMore"
        class="results-jump-controls analytics-jump-controls"
        aria-label="Навигация по результатам"
      >
        <button
          type="button"
          class="jump-arrow-btn"
          @click="scrollToResultsTop"
          aria-label="Перейти к началу таблицы"
          title="К началу таблицы"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <path d="m6 15 6-6 6 6"></path>
          </svg>
        </button>

        <button
          type="button"
          class="jump-arrow-btn"
          @click="scrollToResultsBottom"
          aria-label="Перейти к концу таблицы"
          title="К концу таблицы"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <path d="m6 9 6 6 6-6"></path>
          </svg>
        </button>
      </div>
    </Teleport>

    <Teleport to="body">
      <transition name="modal">
        <div
          v-if="showDetailsModal && selectedItem"
          class="modal-overlay analytics-modal-overlay"
          role="dialog"
          aria-modal="true"
          @click.self="closeDetails"
        >
          <div class="modal-card">
            <div class="modal-header">
              <div class="modal-header-copy">
                <div class="modal-topline">
                  <span class="type-pill" :class="getTypeTone(selectedItem.type)">
                    {{ getTypeLabel(selectedItem.type) }}
                  </span>
                  <span class="state-pill" :class="selectedItem.state ? 'working' : 'broken'">
                    {{ getStateLabel(selectedItem.state) }}
                  </span>
                </div>

                <h3 class="modal-title">{{ getItemTitle(selectedItem) }}</h3>

                <div class="modal-subtitle-row">
                  <span class="code-badge">{{ getInvNumber(selectedItem) }}</span>
                  <span v-if="selectedItem.specs?.cpu_model" class="modal-secondary">
                    {{ selectedItem.specs.cpu_model }}
                  </span>
                </div>
              </div>

              <button class="close-btn" type="button" @click="closeDetails" aria-label="Закрыть">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M18 6 6 18"></path>
                  <path d="m6 6 12 12"></path>
                </svg>
              </button>
            </div>

            <div class="modal-body">
              <div class="details-grid">
                <div class="details-card">
                  <span class="details-label">Корпус</span>
                  <span class="details-value">{{ getOfficeText(selectedItem) }}</span>
                  <span v-if="selectedItem.office_address" class="details-hint">
                    {{ selectedItem.office_address }}
                  </span>
                </div>

                <div class="details-card">
                  <span class="details-label">Этаж</span>
                  <span class="details-value">{{ selectedItem.floor ?? '—' }}</span>
                </div>

                <div class="details-card">
                  <span class="details-label">Аудитория</span>
                  <span class="details-value">{{ getAudienceText(selectedItem) }}</span>
                </div>

                <div class="details-card">
                  <span class="details-label">Расположение</span>
                  <span class="details-value">{{ getPlacementText(selectedItem) }}</span>
                </div>
              </div>

              <div v-if="selectedItem.description" class="details-note">
                <span class="details-label">Описание</span>
                <span class="details-note-text">{{ selectedItem.description }}</span>
              </div>

              <div class="details-section">
                <div class="section-row">
                  <div>
                    <h4 class="modal-section-title">Характеристики</h4>
                    <p class="subsection-subtitle">Расширенная информация по выбранному оборудованию</p>
                  </div>
                </div>

                <div class="details-specs-grid">
                  <div
                    v-for="entry in getDetailSpecsEntries(selectedItem)"
                    :key="entry.label"
                    class="detail-spec-card"
                  >
                    <span class="details-label">{{ entry.label }}</span>
                    <span class="details-value">{{ entry.value }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <button
                v-if="selectedItem.audience_id !== null && selectedItem.audience_id !== undefined"
                class="btn btn-secondary analytics-modal-action-btn analytics-modal-action-btn-secondary"
                type="button"
                @click="openAudience(selectedItem)"
              >
                К аудитории
              </button>
              <button
                class="btn btn-primary analytics-modal-action-btn analytics-modal-action-btn-primary"
                type="button"
                @click="closeDetails"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
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

.analytics-filters {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.filters-section {
  position: relative;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 18px;
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.08), transparent 34%),
    linear-gradient(180deg, rgba(248, 250, 252, 0.96), rgba(255, 255, 255, 0.98));
}

.filters-shell {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filters-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.filters-topline-meta {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  min-width: 0;
  max-width: 220px;
  margin-left: auto;
}

.filters-counter {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 26px;
  padding: 4px 10px;
  border-radius: 999px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1d4ed8;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.filters-apply-note {
  color: #64748b;
  font-size: 11px;
  text-align: right;
  line-height: 1.35;
  max-width: 220px;
  text-wrap: balance;
}

.quick-filter-shelf {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(8px);
}

.quick-filter-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.quick-filter-label,
.facet-label,
.active-filters-label {
  color: #64748b;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.quick-filter-label {
  min-width: 92px;
  padding-top: 6px;
}

.chip-group-compact .chip-toggle {
  min-height: 34px;
  padding: 7px 12px;
  font-size: 12px;
}

.quick-filter-note {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  color: #475569;
  font-size: 13px;
  line-height: 1.45;
}

.quick-filter-note svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: #3b82f6;
  margin-top: 1px;
}

.facet-toolbar {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  align-items: start;
}

.facet-panel {
  position: relative;
}

.facet-panel[open] {
  z-index: 24;
}

.facet-trigger {
  list-style: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  padding: 13px 14px;
  border-radius: 14px;
  border: 1px solid #dbe2ea;
  background: #ffffff;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.facet-trigger::-webkit-details-marker {
  display: none;
}

.facet-trigger:hover {
  border-color: #bfdbfe;
  box-shadow: 0 8px 20px rgba(148, 163, 184, 0.12);
}

.facet-trigger-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.facet-value {
  color: #0f172a;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.facet-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 999px;
  background: #0f172a;
  color: #ffffff;
  font-size: 11px;
  font-weight: 700;
}

.facet-chevron {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: #94a3b8;
  transition: transform 0.2s ease, color 0.2s ease;
}

.facet-panel[open] .facet-chevron {
  transform: rotate(180deg);
  color: #2563eb;
}

.facet-menu {
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  right: 0;
  min-width: 0;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-radius: 16px;
  border: 1px solid #dbe2ea;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 22px 48px rgba(15, 23, 42, 0.16);
  backdrop-filter: blur(12px);
}

.facet-panel-wide .facet-menu {
  min-width: 300px;
}

.facet-menu-head {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.facet-menu-head strong {
  color: #0f172a;
  font-size: 13px;
  font-weight: 700;
}

.facet-menu-head span {
  color: #64748b;
  font-size: 12px;
}

.facet-option-list {
  display: grid;
  gap: 8px;
  max-height: 224px;
  overflow: auto;
  padding-right: 4px;
}

.facet-option-list-tall {
  max-height: 292px;
}

.facet-option {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 10px 11px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #334155;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.facet-option:hover {
  border-color: #bfdbfe;
  background: #eff6ff;
}

.facet-option span {
  min-width: 0;
  overflow-wrap: anywhere;
}

.facet-checkbox {
  width: 16px;
  height: 16px;
  accent-color: #2563eb;
  flex-shrink: 0;
}

.facet-empty {
  padding: 12px 13px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  color: #64748b;
  font-size: 13px;
}

.filters-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 4px;
}

.active-filters-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.active-filter-chip,
.filters-clear-inline {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 34px;
  padding: 7px 12px;
  border-radius: 999px;
  border: 1px solid #dbe2ea;
  background: #ffffff;
  color: #334155;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.active-filter-chip:hover,
.filters-clear-inline:hover {
  border-color: #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
}

.active-filter-chip svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.filters-clear-inline {
  background: #f8fafc;
}

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
  border-radius: 18px;
  padding: 16px;
  background: linear-gradient(180deg, rgba(239, 246, 255, 0.85), rgba(248, 250, 252, 0.96));
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.spec-filters-header,
.section-row {
  display: flex;
  align-items: center;
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
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 10px;
  font-weight: 700;
}

.spec-filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 12px;
}

.spec-profile-switcher {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.spec-profile-tab {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 36px;
  padding: 7px 12px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #475569;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.spec-profile-tab:hover {
  border-color: #93c5fd;
  color: #1d4ed8;
  background: #eff6ff;
}

.spec-profile-tab.active {
  box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.16), 0 8px 18px rgba(59, 130, 246, 0.12);
}

.spec-filter-card,
.summary-card,
.type-summary-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 14px;
}

.spec-filter-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.spec-filter-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.spec-unit-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 24px;
  padding: 4px 8px;
  border-radius: 999px;
  background: #eff6ff;
  border: 1px solid #dbeafe;
  color: #1d4ed8;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.range-inputs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  align-items: center;
}

.range-inputs-compact {
  gap: 8px;
}

.range-chip-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  padding: 10px 11px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.range-chip-caption {
  color: #64748b;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.spec-range-input {
  min-height: 36px;
  padding: 8px 10px;
  font-size: 13px;
}

.boolean-group {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.boolean-group-compact .boolean-btn {
  min-height: 34px;
  padding: 6px 10px;
  font-size: 12px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(155px, 1fr));
  gap: 8px;
}

.summary-card {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  position: relative;
  overflow: hidden;
  min-height: 68px;
  padding: 12px 14px;
  border-radius: 14px;
  background:
    radial-gradient(circle at right top, rgba(59, 130, 246, 0.08), transparent 44%),
    linear-gradient(180deg, #ffffff, #f8fafc);
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.04);
}

.summary-card-total {
  background:
    radial-gradient(circle at right top, rgba(59, 130, 246, 0.1), transparent 42%),
    linear-gradient(180deg, #ffffff, #f8fbff);
}

.summary-card-good {
  background:
    radial-gradient(circle at right top, rgba(34, 197, 94, 0.1), transparent 42%),
    linear-gradient(180deg, #ffffff, #f8fdf9);
}

.summary-card-bad {
  background:
    radial-gradient(circle at right top, rgba(239, 68, 68, 0.1), transparent 42%),
    linear-gradient(180deg, #ffffff, #fff9f9);
}

.summary-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.summary-label {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.summary-value-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  min-width: 0;
  flex-wrap: wrap;
}

.summary-value {
  font-size: 22px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1;
}

.summary-meta {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
}

.summary-icon {
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 12px;
  border: 1px solid transparent;
}

.summary-icon svg,
.summary-icon :deep(svg) {
  width: 20px;
  height: 20px;
}

.summary-card-total .summary-icon {
  background: rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.16);
  color: #2563eb;
}

.summary-icon-equipment :deep(svg) {
  width: 18px;
  height: 18px;
}

.summary-card-good .summary-icon {
  background: rgba(34, 197, 94, 0.12);
  border-color: rgba(34, 197, 94, 0.16);
  color: #16a34a;
}

.summary-card-bad .summary-icon {
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.16);
  color: #dc2626;
}

.type-summary {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.type-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
}

.type-summary-card {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 12px 13px;
}

.type-summary-icon {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(255, 255, 255, 0.88);
}

.type-summary-icon :deep(svg) {
  width: 18px;
  height: 18px;
}

.type-summary-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.type-summary-label {
  font-size: 12px;
  font-weight: 700;
  color: currentColor;
}

.type-summary-meta {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
}

.type-summary-value {
  font-size: 22px;
  font-weight: 800;
  color: currentColor;
  line-height: 1;
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

.results-anchor {
  height: 0;
  scroll-margin-top: 92px;
}

.results-jump-controls {
  position: fixed;
  right: max(18px, env(safe-area-inset-right));
  bottom: max(18px, env(safe-area-inset-bottom));
  z-index: 12;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 18px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(16px);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.jump-arrow-btn {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 1px solid #dbe2ea;
  border-radius: 999px;
  background: #f8fafc;
  color: #334155;
  cursor: pointer;
  transition: all 0.2s ease;
}

.jump-arrow-btn svg {
  width: 16px;
  height: 16px;
}

.jump-arrow-btn:hover {
  border-color: #93c5fd;
  background: #eff6ff;
  color: #1d4ed8;
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
  min-width: 760px;
  border-collapse: collapse;
  text-align: left;
  table-layout: fixed;
}

.analytics-table th {
  background: #f8fafc;
  padding: 9px 10px;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid #e2e8f0;
}

.analytics-table td {
  padding: 9px 10px;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: middle;
  font-size: 12px;
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

.text-center {
  text-align: center;
}

.actions-cell {
  white-space: nowrap;
  padding-left: 6px;
  padding-right: 6px;
}

.row-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
}

.title-cell,
.location-cell {
  min-width: 0;
}

.title-main {
  color: #0f172a;
  font-weight: 700;
  line-height: 1.35;
  overflow-wrap: anywhere;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.title-secondary {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
  overflow: hidden;
}

.location-cell {
  font-weight: 600;
}

.code-badge,
.badge-neutral,
.state-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 3px 7px;
  font-size: 10px;
  font-weight: 700;
  border: 1px solid transparent;
}

.code-badge {
  font-family: ui-monospace, monospace;
  background: #f8fafc;
  color: #334155;
  border-color: #e2e8f0;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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

.state-dot-cell {
  vertical-align: middle;
}

.state-dot {
  display: inline-flex;
  width: 12px;
  height: 12px;
  border-radius: 999px;
  border: 2px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 0 0 1px rgba(148, 163, 184, 0.28);
}

.state-dot.working {
  background: #22c55e;
}

.state-dot.broken {
  background: #ef4444;
}

.open-link {
  min-width: 72px;
  min-height: 32px;
  padding: 5px 10px;
  border-radius: 9px;
  font-size: 12px;
}

.open-link svg {
  width: 14px;
  height: 14px;
}

.details-btn {
  min-width: 68px;
}

.audience-link-btn {
  width: 32px;
  min-width: 32px;
  padding: 0;
}

.open-link:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.58);
  backdrop-filter: blur(6px);
}

.modal-card {
  width: min(920px, 100%);
  max-height: calc(100vh - 48px);
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  box-shadow: 0 28px 80px rgba(15, 23, 42, 0.22);
  overflow: hidden;
}

.modal-header,
.modal-footer {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 22px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header-copy {
  min-width: 0;
}

.modal-topline,
.modal-subtitle-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.modal-topline {
  margin-bottom: 12px;
}

.modal-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
  color: #0f172a;
  overflow-wrap: anywhere;
}

.modal-subtitle-row {
  margin-top: 12px;
}

.modal-secondary,
.details-hint {
  color: #64748b;
  font-size: 13px;
}

.close-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #f8fafc;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.close-btn svg {
  width: 18px;
  height: 18px;
}

.close-btn:hover {
  background: #eff6ff;
  border-color: #bfdbfe;
  color: #1d4ed8;
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 22px 24px;
  overflow-y: auto;
}

.details-grid,
.details-specs-grid {
  display: grid;
  gap: 12px;
}

.details-grid {
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

.details-specs-grid {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.details-card,
.detail-spec-card,
.details-note {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  padding: 14px 15px;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
}

.details-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #64748b;
}

.details-value,
.details-note-text {
  color: #0f172a;
  font-size: 15px;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.details-note-text {
  font-size: 14px;
  font-weight: 500;
  line-height: 1.6;
}

.details-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.modal-section-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}

.modal-footer {
  align-items: center;
  justify-content: flex-end;
  border-top: 1px solid #e2e8f0;
  border-bottom: none;
}

.analytics-modal-action-btn {
  min-width: 138px;
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

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.22s ease;
}

.modal-enter-active .modal-card,
.modal-leave-active .modal-card {
  transition: transform 0.22s ease, opacity 0.22s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-card,
.modal-leave-to .modal-card {
  opacity: 0;
  transform: translateY(10px) scale(0.98);
}

html[data-theme='dark'] .analytics-card .spec-filter-card,
html[data-theme='dark'] .analytics-card .summary-card,
html[data-theme='dark'] .analytics-card .type-summary-card {
  background: #0f172a;
  border-color: #334155;
}

html[data-theme='dark'] .analytics-card .type-summary-icon {
  background: rgba(2, 6, 23, 0.42);
  border-color: rgba(51, 65, 85, 0.88);
}

html[data-theme='dark'] .analytics-card .spec-filters-panel {
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.86), rgba(17, 24, 39, 0.96));
  border-color: #334155;
}

html[data-theme='dark'] .analytics-card .filters-section {
  background:
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.16), transparent 36%),
    linear-gradient(180deg, rgba(15, 23, 42, 0.88), rgba(17, 24, 39, 0.96));
  border-color: #334155;
}

html[data-theme='dark'] .analytics-card .quick-filter-shelf,
html[data-theme='dark'] .analytics-card .quick-filter-note,
html[data-theme='dark'] .analytics-card .facet-trigger,
html[data-theme='dark'] .analytics-card .facet-menu,
html[data-theme='dark'] .analytics-card .facet-option,
html[data-theme='dark'] .analytics-card .spec-profile-tab,
html[data-theme='dark'] .analytics-card .range-chip-field,
html[data-theme='dark'] .analytics-card .active-filter-chip,
html[data-theme='dark'] .analytics-card .filters-clear-inline {
  background: #0f172a;
  border-color: #334155;
  color: #cbd5e1;
}

html[data-theme='dark'] .analytics-card .quick-filter-note {
  background: #111827;
}

html[data-theme='dark'] .analytics-card .filters-counter {
  background: rgba(37, 99, 235, 0.18);
  border-color: #60a5fa;
  color: #dbeafe;
}

html[data-theme='dark'] .analytics-card .spec-unit-chip {
  background: rgba(37, 99, 235, 0.18);
  border-color: rgba(96, 165, 250, 0.24);
  color: #dbeafe;
}

html[data-theme='dark'] .analytics-card .summary-card {
  box-shadow: none;
}

html[data-theme='dark'] .analytics-card .summary-card-total {
  background:
    radial-gradient(circle at right top, rgba(37, 99, 235, 0.18), transparent 42%),
    linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(17, 24, 39, 0.98));
}

html[data-theme='dark'] .analytics-card .summary-card-good {
  background:
    radial-gradient(circle at right top, rgba(34, 197, 94, 0.18), transparent 42%),
    linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(17, 24, 39, 0.98));
}

html[data-theme='dark'] .analytics-card .summary-card-bad {
  background:
    radial-gradient(circle at right top, rgba(239, 68, 68, 0.18), transparent 42%),
    linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(17, 24, 39, 0.98));
}

html[data-theme='dark'] .analytics-card .summary-card-total .summary-icon {
  background: rgba(37, 99, 235, 0.18);
  border-color: rgba(96, 165, 250, 0.24);
  color: #93c5fd;
}

html[data-theme='dark'] .analytics-card .summary-card-good .summary-icon {
  background: rgba(34, 197, 94, 0.18);
  border-color: rgba(74, 222, 128, 0.24);
  color: #86efac;
}

html[data-theme='dark'] .analytics-card .summary-card-bad .summary-icon {
  background: rgba(239, 68, 68, 0.18);
  border-color: rgba(248, 113, 113, 0.24);
  color: #fca5a5;
}

html[data-theme='dark'] .analytics-card .section-subtitle,
html[data-theme='dark'] .analytics-card .spec-filter-label,
html[data-theme='dark'] .analytics-card .spec-filters-subtitle,
html[data-theme='dark'] .analytics-card .subsection-subtitle,
html[data-theme='dark'] .analytics-card .section-row-caption,
html[data-theme='dark'] .analytics-card .filter-unit,
html[data-theme='dark'] .analytics-card .filters-apply-note,
html[data-theme='dark'] .analytics-card .quick-filter-label,
html[data-theme='dark'] .analytics-card .facet-label,
html[data-theme='dark'] .analytics-card .facet-menu-head span,
html[data-theme='dark'] .analytics-card .range-chip-caption,
html[data-theme='dark'] .analytics-card .title-secondary,
html[data-theme='dark'] .analytics-card .summary-label,
html[data-theme='dark'] .analytics-card .summary-meta,
html[data-theme='dark'] .analytics-card .type-summary-label,
html[data-theme='dark'] .analytics-card .type-summary-meta,
html[data-theme='dark'] .analytics-card .type-summary-empty,
html[data-theme='dark'] .analytics-card .state-hint {
  color: #94a3b8;
}

html[data-theme='dark'] .analytics-card .spec-filters-title,
html[data-theme='dark'] .analytics-card .subsection-title,
html[data-theme='dark'] .analytics-card .summary-value,
html[data-theme='dark'] .analytics-card .type-summary-value,
html[data-theme='dark'] .analytics-card .facet-value,
html[data-theme='dark'] .analytics-card .facet-menu-head strong,
html[data-theme='dark'] .analytics-card .title-main,
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

html[data-theme='dark'] .analytics-card .facet-trigger:hover,
html[data-theme='dark'] .analytics-card .facet-option:hover,
html[data-theme='dark'] .analytics-card .spec-profile-tab:hover,
html[data-theme='dark'] .analytics-card .active-filter-chip:hover,
html[data-theme='dark'] .analytics-card .filters-clear-inline:hover {
  background: rgba(37, 99, 235, 0.18);
  border-color: #60a5fa;
  color: #dbeafe;
}

html[data-theme='dark'] .analytics-card .spec-profile-tab.active {
  box-shadow: 0 0 0 1px rgba(96, 165, 250, 0.18), 0 10px 22px rgba(15, 23, 42, 0.24);
}

html[data-theme='dark'] .analytics-card .facet-count {
  background: #2563eb;
  color: #eff6ff;
}

html[data-theme='dark'] .analytics-card .facet-chevron {
  color: #64748b;
}

html[data-theme='dark'] .analytics-card .facet-empty {
  background: #111827;
  border-color: #334155;
  color: #94a3b8;
}

html[data-theme='dark'] .analytics-modal-overlay .modal-card,
html[data-theme='dark'] .analytics-modal-overlay .details-card,
html[data-theme='dark'] .analytics-modal-overlay .detail-spec-card,
html[data-theme='dark'] .analytics-modal-overlay .details-note {
  background: #0f172a;
  border-color: #334155;
}

html[data-theme='dark'] .analytics-modal-overlay .modal-header,
html[data-theme='dark'] .analytics-modal-overlay .modal-footer {
  border-color: #334155;
}

html[data-theme='dark'] .analytics-modal-overlay .modal-title,
html[data-theme='dark'] .analytics-modal-overlay .details-value,
html[data-theme='dark'] .analytics-modal-overlay .details-note-text {
  color: #e2e8f0;
}

html[data-theme='dark'] .analytics-modal-overlay .modal-secondary,
html[data-theme='dark'] .analytics-modal-overlay .details-label,
html[data-theme='dark'] .analytics-modal-overlay .details-hint {
  color: #94a3b8;
}

html[data-theme='dark'] .analytics-modal-overlay .close-btn {
  background: #111827;
  border-color: #334155;
  color: #cbd5e1;
}

html[data-theme='dark'] .analytics-modal-overlay .close-btn:hover {
  background: rgba(37, 99, 235, 0.18);
  border-color: #60a5fa;
  color: #dbeafe;
}

html[data-theme='dark'] .analytics-modal-overlay .analytics-modal-action-btn-secondary {
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.92), rgba(22, 34, 52, 0.9));
  border: 1px solid rgba(71, 85, 105, 0.9);
  color: #cbd5e1;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.03),
    0 12px 24px rgba(2, 6, 23, 0.2);
}

html[data-theme='dark'] .analytics-modal-overlay .analytics-modal-action-btn-secondary:hover:not(:disabled) {
  background: linear-gradient(180deg, rgba(22, 34, 52, 0.96), rgba(30, 41, 59, 0.94));
  border-color: rgba(96, 165, 250, 0.3);
  color: #e2e8f0;
}

html[data-theme='dark'] .analytics-modal-overlay .analytics-modal-action-btn-primary {
  background: linear-gradient(135deg, #0f766e, #0f5f8a);
  border: 1px solid rgba(94, 234, 212, 0.18);
  color: #f8fafc;
  box-shadow:
    0 14px 28px rgba(8, 47, 73, 0.32),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

html[data-theme='dark'] .analytics-modal-overlay .analytics-modal-action-btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #0d9488, #0369a1);
  border-color: rgba(125, 211, 252, 0.24);
}

html[data-theme='dark'] .analytics-modal-overlay .analytics-modal-action-btn-primary:disabled,
html[data-theme='dark'] .analytics-modal-overlay .analytics-modal-action-btn-secondary:disabled {
  box-shadow: none;
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

html[data-theme='dark'] .analytics-card .state-dot {
  border-color: #0f172a;
  box-shadow: 0 0 0 1px rgba(148, 163, 184, 0.24);
}

html[data-theme='dark'] .analytics-card .state-dot.working {
  background: #4ade80;
}

html[data-theme='dark'] .analytics-card .state-dot.broken {
  background: #f87171;
}

html[data-theme='dark'] .analytics-card .type-summary-empty,
html[data-theme='dark'] .analytics-card .load-more-wrapper {
  background: #0f172a;
  border-color: #334155;
}

:global(html[data-theme='dark']) .analytics-jump-controls {
  background: rgba(15, 23, 42, 0.88);
  border-color: rgba(51, 65, 85, 0.92);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.34);
}

:global(html[data-theme='dark']) .analytics-jump-controls .jump-arrow-btn {
  background: #0f172a;
  border-color: #334155;
  color: #cbd5e1;
}

:global(html[data-theme='dark']) .analytics-jump-controls .jump-arrow-btn:hover {
  background: rgba(37, 99, 235, 0.18);
  border-color: #60a5fa;
  color: #dbeafe;
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
  .filters-topline,
  .quick-filter-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filters-topline-meta {
    align-items: flex-start;
  }

  .quick-filter-label {
    min-width: 0;
    padding-top: 0;
  }

  .facet-menu {
    position: static;
    margin-top: 10px;
    box-shadow: none;
  }

  .spec-filters-grid,
  .summary-grid,
  .type-summary-grid {
    grid-template-columns: 1fr;
  }

  .spec-profile-switcher {
    width: 100%;
  }

  .range-inputs {
    grid-template-columns: 1fr;
  }

  .modal-overlay {
    padding: 12px;
  }

  .modal-card {
    max-height: calc(100vh - 24px);
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

  .filters-actions,
  .section-row {
    width: 100%;
  }

  .results-jump-controls {
    right: max(12px, env(safe-area-inset-right));
    bottom: max(12px, env(safe-area-inset-bottom));
    gap: 6px;
    padding: 6px;
  }

  .jump-arrow-btn {
    width: 32px;
    height: 32px;
  }

  .filters-actions .btn,
  .section-row .btn-inline {
    flex: 1;
  }

  .filters-section,
  .quick-filter-shelf {
    padding: 14px;
  }

  .facet-toolbar {
    grid-template-columns: 1fr;
  }

  .filters-counter,
  .filters-apply-note {
    text-align: left;
  }

  .chip-group-compact {
    width: 100%;
  }

  .boolean-group {
    grid-template-columns: 1fr;
  }

  .spec-filters-header {
    align-items: stretch;
  }

  .spec-profile-tab {
    flex: 1;
  }

  .type-pill {
    align-self: flex-start;
  }

  .modal-header,
  .modal-body,
  .modal-footer {
    padding-left: 18px;
    padding-right: 18px;
  }

  .modal-title {
    font-size: 20px;
  }

  .details-grid,
  .details-specs-grid {
    grid-template-columns: 1fr;
  }
}
</style>
