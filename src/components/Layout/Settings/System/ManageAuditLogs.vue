<script>
import api from "@/services/api";
import { useNotificationsStore } from "@/stores/notifications";
import {
  AUDIT_ACTION_OPTIONS,
  AUDIT_ENTITY_TYPE_OPTIONS,
  formatAuditListResponse,
  formatAuditLogEntry,
  sortAuditLogItems,
} from "@/utils/auditLogs.js";

const AUDIT_ENDPOINT = "/admin/audit-log";
const AUDIT_QUERY_KEYS = Object.freeze({
  q: "audit_q",
  action: "audit_action",
  entityType: "audit_entity_type",
  entityId: "audit_entity_id",
  userId: "audit_user_id",
  page: "audit_page",
  limit: "audit_limit",
  order: "audit_order",
});
const DEFAULT_PAGE_SIZE = 25;
const PAGE_SIZE_OPTIONS = Object.freeze([25, 50, 100]);
const DEFAULT_SORT_ORDER = "desc";
const SORT_OPTIONS = Object.freeze([
  { value: "desc", label: "Сначала новые" },
  { value: "asc", label: "Сначала старые" },
]);

function createEmptyFilters() {
  return {
    q: "",
    action: "",
    entity_type: "",
    entity_id: "",
    user_id: "",
  };
}

function normalizeText(value) {
  return String(value ?? "").trim();
}

function normalizeFilters(source = {}) {
  const filters = createEmptyFilters();

  Object.keys(filters).forEach((key) => {
    filters[key] = normalizeText(source[key]);
  });

  return filters;
}

function buildFilterParams(filters) {
  const params = {};
  const normalizedFilters = normalizeFilters(filters);

  Object.entries(normalizedFilters).forEach(([key, value]) => {
    if (value) {
      params[key] = value;
    }
  });

  return params;
}

function normalizePositiveInt(value, fallback) {
  const numericValue = Number.parseInt(String(value ?? ""), 10);
  return Number.isFinite(numericValue) && numericValue > 0 ? numericValue : fallback;
}

function normalizePageSize(value) {
  const normalized = normalizePositiveInt(value, DEFAULT_PAGE_SIZE);
  return PAGE_SIZE_OPTIONS.includes(normalized) ? normalized : DEFAULT_PAGE_SIZE;
}

function normalizeSortOrder(value) {
  return value === "asc" ? "asc" : DEFAULT_SORT_ORDER;
}

function stringifySnapshot(value) {
  return JSON.stringify(value);
}

function stringifyQuery(query = {}) {
  const normalized = {};

  Object.keys(query)
    .sort()
    .forEach((key) => {
      const value = query[key];
      if (value == null || value === "") return;

      normalized[key] = Array.isArray(value)
        ? value.map((item) => String(item))
        : String(value);
    });

  return JSON.stringify(normalized);
}

export default {
  name: "ManageAuditLogs",

  data() {
    const emptyFilters = createEmptyFilters();

    return {
      logs: [],
      total: null,
      totalKey: "",
      loading: false,
      error: null,

      page: 1,
      pageSize: DEFAULT_PAGE_SIZE,
      sortOrder: DEFAULT_SORT_ORDER,

      filters: { ...emptyFilters },
      appliedFilters: { ...emptyFilters },

      requestSeq: 0,
      isInitialized: false,

      showDetails: false,
      selected: null,
    };
  },

  computed: {
    notify() {
      return useNotificationsStore();
    },

    actionOptions() {
      return this.getSelectOptions(AUDIT_ACTION_OPTIONS, this.filters.action);
    },

    entityTypeOptions() {
      return this.getSelectOptions(AUDIT_ENTITY_TYPE_OPTIONS, this.filters.entity_type);
    },

    sortOptions() {
      return SORT_OPTIONS;
    },

    pageSizeOptions() {
      return PAGE_SIZE_OPTIONS;
    },

    presentedLogs() {
      return this.logs.map((item) => formatAuditLogEntry(item));
    },

    selectedPresentation() {
      return this.selected ? formatAuditLogEntry(this.selected) : null;
    },

    pageCount() {
      return this.getPageCountFor(this.total, this.pageSize);
    },

    pageLabel() {
      return `Страница ${this.page} из ${this.pageCount}`;
    },

    resultsCaption() {
      if (!Number.isFinite(Number(this.total)) || this.total == null) {
        return `Показано ${this.logs.length} из ${this.total}`;
      }

      if (!this.logs.length) {
        return "Записей пока нет";
      }

      return `Показано ${this.logs.length} записей`;
    },

    activeFiltersCount() {
      return Object.keys(buildFilterParams(this.appliedFilters)).length;
    },

    hasAppliedFilters() {
      return this.activeFiltersCount > 0;
    },

    hasPendingFilterChanges() {
      return stringifySnapshot(buildFilterParams(this.filters))
        !== stringifySnapshot(buildFilterParams(this.appliedFilters));
    },

    canGoPrev() {
      return !this.loading && this.page > 1;
    },

    canGoNext() {
      return !this.loading && this.page < this.pageCount;
    },

    emptyStateText() {
      return this.hasAppliedFilters
        ? "По выбранным фильтрам записи не найдены"
        : "Записей пока нет";
    },

    resultsCaption() {
      if (!Number.isFinite(Number(this.total)) || this.total == null) {
        if (!this.logs.length) {
          return "Записей пока нет";
        }

        return `Показано ${this.logs.length} записей`;
      }

      if (!this.total) {
        return this.activeFiltersCount
          ? "По выбранным фильтрам ничего не найдено"
          : "Записей пока нет";
      }

      const rangeStart = (this.page - 1) * this.pageSize + 1;
      const rangeEnd = rangeStart + this.logs.length - 1;

      return `Показаны записи ${rangeStart}-${rangeEnd} из ${this.total}`;
    },
  },

  methods: {
    buildParams() {
      const offset = (this.page - 1) * this.pageSize;
      const params = { limit: this.pageSize, offset };

      Object.entries(this.filters).forEach(([key, value]) => {
        const normalized = String(value ?? "").trim();
        if (normalized !== "") {
          params[key] = normalized;
        }
      });

      return params;
    },

    async fetchLogs({ reset = false } = {}) {
      if (this.loading) return;

      this.loading = true;
      this.error = null;

      try {
        if (reset) {
          this.page = 1;
          this.hasMore = true;
        }

        const response = await api.get(AUDIT_ENDPOINT, {
          params: this.buildParams(),
        });

        const { items, total } = formatAuditListResponse(response.data);

        if (reset) {
          this.logs = items;
        } else {
          this.logs.push(...items);
        }

        this.total = total;
        this.hasMore = total != null
          ? this.logs.length < total
          : items.length === this.pageSize;
      } catch (error) {
        const message = error.response?.data?.detail || "Не удалось загрузить журнал действий";
        this.error = message;
        this.notify.error(message);
      } finally {
        this.loading = false;
      }
    },

    refreshLogs() {
      this.fetchLogs({ reset: true });
    },

    applyFilters() {
      clearTimeout(this._timer);
      this._timer = setTimeout(() => {
        this.fetchLogs({ reset: true });
      }, 300);
    },

    clearFilters() {
      this.filters = {
        q: "",
        action: "",
        entity_type: "",
        entity_id: "",
        user_id: "",
      };
      this.fetchLogs({ reset: true });
    },

    loadMore() {
      if (!this.hasMore || this.loading) return;

      this.page += 1;
      this.fetchLogs({ reset: false });
    },

    openDetails(item) {
      this.selected = item;
      this.showDetails = true;
      document.body.style.overflow = "hidden";
    },

    closeDetails() {
      this.showDetails = false;
      this.selected = null;
      document.body.style.overflow = "";
    },

    getTagKey(itemId, tag, index) {
      return `${itemId}-${index}-${tag}`;
    },

    getMetaKey(itemId, meta, index) {
      return `${itemId}-meta-${index}-${meta}`;
    },

    getSelectOptions(options, currentValue) {
      const normalizedValue = normalizeText(currentValue);
      if (!normalizedValue) return options;

      if (options.some((option) => option.value === normalizedValue)) {
        return options;
      }

      return [{ value: normalizedValue, label: normalizedValue }, ...options];
    },

    getPageCountFor(totalValue = this.total, pageSize = this.pageSize) {
      const total = Number(totalValue);
      if (!Number.isFinite(total) || total <= 0) return 1;
      return Math.max(1, Math.ceil(total / pageSize));
    },

    getLocalStateSnapshot() {
      return {
        filters: normalizeFilters(this.appliedFilters),
        page: this.page,
        pageSize: this.pageSize,
        sortOrder: this.sortOrder,
      };
    },

    getRouteStateSnapshot(query = this.$route.query) {
      const filters = createEmptyFilters();

      filters.q = normalizeText(query[AUDIT_QUERY_KEYS.q]);
      filters.action = normalizeText(query[AUDIT_QUERY_KEYS.action]);
      filters.entity_type = normalizeText(query[AUDIT_QUERY_KEYS.entityType]);
      filters.entity_id = normalizeText(query[AUDIT_QUERY_KEYS.entityId]);
      filters.user_id = normalizeText(query[AUDIT_QUERY_KEYS.userId]);

      return {
        filters: normalizeFilters(filters),
        page: normalizePositiveInt(query[AUDIT_QUERY_KEYS.page], 1),
        pageSize: normalizePageSize(query[AUDIT_QUERY_KEYS.limit]),
        sortOrder: normalizeSortOrder(query[AUDIT_QUERY_KEYS.order]),
      };
    },

    applyRouteState(snapshot) {
      this.filters = { ...snapshot.filters };
      this.appliedFilters = { ...snapshot.filters };
      this.page = snapshot.page;
      this.pageSize = snapshot.pageSize;
      this.sortOrder = snapshot.sortOrder;
    },

    buildRouteQuery() {
      const nextQuery = { ...this.$route.query };
      Object.values(AUDIT_QUERY_KEYS).forEach((key) => {
        delete nextQuery[key];
      });

      const filterParams = buildFilterParams(this.appliedFilters);
      if (filterParams.q) nextQuery[AUDIT_QUERY_KEYS.q] = filterParams.q;
      if (filterParams.action) nextQuery[AUDIT_QUERY_KEYS.action] = filterParams.action;
      if (filterParams.entity_type) nextQuery[AUDIT_QUERY_KEYS.entityType] = filterParams.entity_type;
      if (filterParams.entity_id) nextQuery[AUDIT_QUERY_KEYS.entityId] = filterParams.entity_id;
      if (filterParams.user_id) nextQuery[AUDIT_QUERY_KEYS.userId] = filterParams.user_id;
      if (this.page > 1) nextQuery[AUDIT_QUERY_KEYS.page] = String(this.page);
      if (this.pageSize !== DEFAULT_PAGE_SIZE) nextQuery[AUDIT_QUERY_KEYS.limit] = String(this.pageSize);
      if (this.sortOrder !== DEFAULT_SORT_ORDER) nextQuery[AUDIT_QUERY_KEYS.order] = this.sortOrder;

      return nextQuery;
    },

    syncRouteQuery() {
      const nextQuery = this.buildRouteQuery();
      if (stringifyQuery(nextQuery) === stringifyQuery(this.$route.query)) return;
      this.$router.replace({ query: nextQuery });
    },

    buildAppliedFilterParams() {
      return buildFilterParams(this.appliedFilters);
    },

    getAppliedFilterKey() {
      return stringifySnapshot(this.buildAppliedFilterParams());
    },

    computeRequestPagination(totalForCurrentFilters) {
      if (
        this.sortOrder !== "asc" ||
        !Number.isFinite(Number(totalForCurrentFilters)) ||
        Number(totalForCurrentFilters) <= 0
      ) {
        return {
          limit: this.pageSize,
          offset: (this.page - 1) * this.pageSize,
        };
      }

      const total = Number(totalForCurrentFilters);
      const itemsBeforePage = (this.page - 1) * this.pageSize;
      const pageItemCount = Math.min(this.pageSize, Math.max(total - itemsBeforePage, 0));

      return {
        limit: Math.max(pageItemCount, 1),
        offset: Math.max(total - itemsBeforePage - pageItemCount, 0),
      };
    },

    async fetchTotalForCurrentFilters(filterParams, filterKey, requestId) {
      const response = await api.get(AUDIT_ENDPOINT, {
        params: {
          ...filterParams,
          limit: 1,
          offset: 0,
        },
      });

      if (requestId !== this.requestSeq) return null;

      const { total } = formatAuditListResponse(response.data);
      const normalizedTotal = Number.isFinite(Number(total)) ? Number(total) : 0;

      this.total = normalizedTotal;
      this.totalKey = filterKey;

      return normalizedTotal;
    },

    async fetchLogs({ allowPageCorrection = true } = {}) {
      const requestId = ++this.requestSeq;
      this.loading = true;
      this.error = null;

      const filterParams = this.buildAppliedFilterParams();
      const filterKey = stringifySnapshot(filterParams);

      try {
        let totalForCurrentFilters = this.totalKey === filterKey ? this.total : null;

        if (this.sortOrder === "asc" && !Number.isFinite(Number(totalForCurrentFilters))) {
          totalForCurrentFilters = await this.fetchTotalForCurrentFilters(filterParams, filterKey, requestId);
          if (requestId !== this.requestSeq) return;
        }

        const response = await api.get(AUDIT_ENDPOINT, {
          params: {
            ...filterParams,
            ...this.computeRequestPagination(totalForCurrentFilters),
          },
        });

        if (requestId !== this.requestSeq) return;

        const { items, total } = formatAuditListResponse(response.data);
        const normalizedTotal = Number.isFinite(Number(total)) ? Number(total) : items.length;
        const totalPages = this.getPageCountFor(normalizedTotal, this.pageSize);

        if (normalizedTotal > 0 && this.page > totalPages && allowPageCorrection) {
          this.total = normalizedTotal;
          this.totalKey = filterKey;
          this.page = totalPages;
          this.syncRouteQuery();
          return this.fetchLogs({ allowPageCorrection: false });
        }

        if (normalizedTotal === 0 && this.page !== 1) {
          this.page = 1;
          this.syncRouteQuery();
        }

        this.logs = sortAuditLogItems(items, this.sortOrder);
        this.total = normalizedTotal;
        this.totalKey = filterKey;
      } catch (error) {
        if (requestId !== this.requestSeq) return;

        const message = error.response?.data?.detail || "Не удалось загрузить журнал действий";
        this.error = message;
        this.notify.error(message);
      } finally {
        if (requestId === this.requestSeq) {
          this.loading = false;
        }
      }
    },

    refreshLogs() {
      this.fetchLogs();
    },

    applyFilters() {
      const previousFilterKey = this.getAppliedFilterKey();
      const nextFilters = normalizeFilters(this.filters);
      const nextFilterKey = stringifySnapshot(buildFilterParams(nextFilters));

      this.filters = { ...nextFilters };
      this.appliedFilters = { ...nextFilters };
      this.page = 1;

      if (nextFilterKey !== previousFilterKey) {
        this.total = null;
        this.totalKey = "";
      }

      this.syncRouteQuery();
      this.fetchLogs();
    },

    clearFilters() {
      const emptyFilters = createEmptyFilters();

      this.filters = { ...emptyFilters };
      this.appliedFilters = { ...emptyFilters };
      this.page = 1;
      this.total = null;
      this.totalKey = "";

      this.syncRouteQuery();
      this.fetchLogs();
    },

    changeSortOrder(nextOrder) {
      const normalizedOrder = normalizeSortOrder(nextOrder);
      if (normalizedOrder === this.sortOrder && this.page === 1) return;

      this.sortOrder = normalizedOrder;
      this.page = 1;

      this.syncRouteQuery();
      this.fetchLogs();
    },

    changePageSize(nextPageSize) {
      const normalizedPageSize = normalizePageSize(nextPageSize);
      if (normalizedPageSize === this.pageSize) return;

      const currentOffset = (this.page - 1) * this.pageSize;
      this.pageSize = normalizedPageSize;
      this.page = Math.floor(currentOffset / normalizedPageSize) + 1;

      const totalPages = this.getPageCountFor(this.total, normalizedPageSize);
      if (this.page > totalPages) {
        this.page = totalPages;
      }

      this.syncRouteQuery();
      this.fetchLogs();
    },

    goToPage(nextPage) {
      const clampedPage = Math.min(Math.max(1, nextPage), this.pageCount);
      if (clampedPage === this.page) return;

      this.page = clampedPage;
      this.syncRouteQuery();
      this.fetchLogs();
    },

    goToFirstPage() {
      this.goToPage(1);
    },

    goToPrevPage() {
      this.goToPage(this.page - 1);
    },

    goToNextPage() {
      this.goToPage(this.page + 1);
    },

    goToLastPage() {
      this.goToPage(this.pageCount);
    },

    handleRouteQueryChange(query) {
      const nextRouteState = this.getRouteStateSnapshot(query);
      const previousFilterKey = this.getAppliedFilterKey();
      const nextFilterKey = stringifySnapshot(buildFilterParams(nextRouteState.filters));

      if (this.isInitialized) {
        const currentStateKey = stringifySnapshot(this.getLocalStateSnapshot());
        const routeStateKey = stringifySnapshot(nextRouteState);
        if (currentStateKey === routeStateKey) {
          return;
        }
      }

      this.applyRouteState(nextRouteState);

      if (previousFilterKey !== nextFilterKey) {
        this.total = null;
        this.totalKey = "";
      }

      this.isInitialized = true;
      this.fetchLogs();
    },
  },

  watch: {
    "$route.query": {
      immediate: true,
      handler(query) {
        this.handleRouteQueryChange(query);
      },
    },
  },

  beforeUnmount() {
    document.body.style.overflow = "";
  },
};
</script>

<template>
  <div class="audit-card">
    <div class="card-header">
      <div>
        <h2 class="section-title">Журнал действий</h2>
        <p class="section-subtitle">Понятная история изменений, действий пользователей и служебных событий системы</p>
      </div>

      <div class="header-actions">
        <button class="btn btn-primary" type="button" @click="refreshLogs" :disabled="loading">
          <svg
            v-if="loading"
            class="spinner"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M12 2a10 10 0 0 1 10 10"></path>
          </svg>
          <svg
            v-else
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polyline points="23 4 23 10 17 10"></polyline>
            <polyline points="1 20 1 14 7 14"></polyline>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
          </svg>
          Обновить
        </button>
      </div>
    </div>

    <form class="filters-section filters-form" @submit.prevent="applyFilters">
      <div class="search-bar">
        <svg
          class="search-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        <input
          v-model="filters.q"
          class="form-input search-input"
          placeholder="Поиск по действию, сущности, пути и payload..."
        />
      </div>

      <div class="filters-grid">
        <div class="filter-group">
          <label>Действие</label>
          <select v-model="filters.action" class="form-input">
            <option value="">Все действия</option>
            <option
              v-for="option in actionOptions"
              :key="`action-${option.value}`"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>Сущность</label>
          <select v-model="filters.entity_type" class="form-input">
            <option value="">Все сущности</option>
            <option
              v-for="option in entityTypeOptions"
              :key="`entity-${option.value}`"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>ID сущности</label>
          <input
            v-model="filters.entity_id"
            class="form-input"
            placeholder="Напр. 42"
            inputmode="numeric"
          />
        </div>

        <div class="filter-group">
          <label>ID пользователя</label>
          <input
            v-model="filters.user_id"
            class="form-input"
            placeholder="Напр. 7"
            inputmode="numeric"
          />
        </div>
      </div>

      <div class="filters-actions">
        <span class="filters-note">
          {{ hasPendingFilterChanges ? "Есть неприменённые изменения фильтров" : "Фильтры применены" }}
        </span>
        <div class="filters-actions-row">
          <button class="btn btn-secondary" type="button" @click="clearFilters">
            Сбросить фильтры
          </button>
          <button class="btn btn-primary" type="submit">
            Применить
          </button>
        </div>
      </div>
    </form>

    <div v-if="false" class="filters-section legacy-filters">
      <div class="search-bar">
        <svg
          class="search-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        <input
          v-model="filters.q"
          class="form-input search-input"
          placeholder="Поиск по действию, сущности, payload и маршруту..."
        />
      </div>

      <div class="filters-grid">
        <div class="filter-group">
          <label>Действие</label>
          <input v-model="filters.action" class="form-input" placeholder="Напр. user.update" />
        </div>

        <div class="filter-group">
          <label>Сущность</label>
          <input v-model="filters.entity_type" class="form-input" placeholder="Напр. audience" />
        </div>

        <div class="filter-group">
          <label>ID сущности</label>
          <input v-model="filters.entity_id" class="form-input" placeholder="ID" />
        </div>

        <div class="filter-group">
          <label>ID пользователя</label>
          <input v-model="filters.user_id" class="form-input" placeholder="ID" />
        </div>
      </div>
    </div>

    <div class="results-toolbar">
      <span class="results-caption">{{ resultsCaption }}</span>
      <span v-if="activeFiltersCount" class="results-caption muted">Активных фильтров: {{ activeFiltersCount }}</span>
      <span class="results-caption muted">{{ pageLabel }}</span>

      <div class="results-toolbar-controls">
        <label class="toolbar-field">
          <span>Порядок</span>
          <select
            class="form-input toolbar-select"
            :value="sortOrder"
            @change="changeSortOrder($event.target.value)"
          >
            <option
              v-for="option in sortOptions"
              :key="`sort-${option.value}`"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </label>

        <label class="toolbar-field">
          <span>На странице</span>
          <select
            class="form-input toolbar-select"
            :value="pageSize"
            @change="changePageSize($event.target.value)"
          >
            <option
              v-for="size in pageSizeOptions"
              :key="`page-size-${size}`"
              :value="size"
            >
              {{ size }}
            </option>
          </select>
        </label>
      </div>
    </div>

    <div v-if="error" class="alert-box error">{{ error }}</div>

    <div class="audit-list-shell">
      <div v-if="loading && !logs.length" class="state-container">
        <div class="spinner-large"></div>
        <p>Загрузка журнала действий...</p>
      </div>

      <div v-else-if="!presentedLogs.length" class="state-container empty">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="3" y1="9" x2="21" y2="9"></line>
          <line x1="9" y1="21" x2="9" y2="9"></line>
        </svg>
        <p>{{ emptyStateText }}</p>
      </div>

      <div v-else class="audit-list">
        <button
          v-for="item in presentedLogs"
          :key="item.id"
          type="button"
          class="audit-entry"
          @click="openDetails(item.original)"
        >
          <div class="audit-entry-top">
            <span class="audit-action-chip" :class="item.toneClass">{{ item.actionLabel }}</span>
            <span class="audit-entry-time">{{ item.createdAtLabel }}</span>
          </div>

          <h3 class="audit-entry-title">{{ item.title }}</h3>
          <p class="audit-entry-summary">{{ item.summary }}</p>

          <div v-if="item.summaryTags.length" class="audit-entry-tags">
            <span
              v-for="(tag, index) in item.summaryTags"
              :key="getTagKey(item.id, tag, index)"
              class="audit-entry-tag"
            >
              {{ tag }}
            </span>
          </div>

          <div class="audit-entry-meta">
            <span
              v-for="(meta, index) in item.listMeta"
              :key="getMetaKey(item.id, meta, index)"
              class="audit-entry-meta-item"
            >
              {{ meta }}
            </span>
          </div>
        </button>

        <div v-if="false" class="load-more-wrapper">
          <button class="btn btn-secondary load-more-btn" type="button" @click="loadMore" :disabled="loading">
            <span v-if="loading" class="spinner"></span>
            {{ loading ? 'Загрузка...' : 'Показать следующие записи' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="total > 0" class="pagination-bar">
      <div class="pagination-meta">
        <span class="pagination-title">{{ pageLabel }}</span>
        <span class="results-caption muted">Всего записей: {{ total }}</span>
      </div>

      <div class="pagination-actions">
        <button class="btn btn-secondary pagination-btn" type="button" :disabled="!canGoPrev" @click="goToFirstPage">
          Первая
        </button>
        <button class="btn btn-secondary pagination-btn" type="button" :disabled="!canGoPrev" @click="goToPrevPage">
          Назад
        </button>
        <button class="btn btn-secondary pagination-btn" type="button" :disabled="!canGoNext" @click="goToNextPage">
          Вперёд
        </button>
        <button class="btn btn-secondary pagination-btn" type="button" :disabled="!canGoNext" @click="goToLastPage">
          Последняя
        </button>
      </div>
    </div>

    <Teleport to="body">
      <transition name="modal">
        <div
          v-if="showDetails && selectedPresentation"
          class="modal-overlay audit-log-modal-overlay"
          @click.self="closeDetails"
        >
          <div class="modal-card audit-modal-card">
            <div class="modal-header audit-modal-header">
              <div class="audit-modal-title-block">
                <div class="audit-modal-head-row">
                  <span class="audit-action-chip" :class="selectedPresentation.toneClass">
                    {{ selectedPresentation.actionLabel }}
                  </span>
                  <code class="audit-action-code">{{ selectedPresentation.action }}</code>
                </div>

                <h3 class="modal-title">{{ selectedPresentation.title }}</h3>
                <p class="modal-subtitle">{{ selectedPresentation.summary }}</p>
              </div>

              <button class="audit-modal-close" type="button" @click="closeDetails" aria-label="Закрыть">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" d="M6 6l12 12M18 6L6 18"/>
                </svg>
              </button>
            </div>

            <div class="modal-body audit-modal-body">
              <div class="meta-grid audit-modal-meta-grid">
                <div class="meta-item">
                  <span class="meta-label">Дата и время</span>
                  <span class="meta-value">{{ selectedPresentation.createdAtLabel }}</span>
                </div>

                <div class="meta-item">
                  <span class="meta-label">Кто выполнил</span>
                  <span class="meta-value">{{ selectedPresentation.actorLabel }}</span>
                </div>

                <div class="meta-item">
                  <span class="meta-label">Сущность</span>
                  <span class="meta-value">{{ selectedPresentation.entityLabel || "—" }}</span>
                </div>

                <div class="meta-item">
                  <span class="meta-label">Код действия</span>
                  <span class="meta-value">{{ selectedPresentation.action }}</span>
                </div>
              </div>

              <section v-if="selectedPresentation.payloadDetailRows.length" class="audit-modal-section">
                <h4 class="audit-section-title">Краткая сводка</h4>
                <div class="audit-detail-grid">
                  <div
                    v-for="row in selectedPresentation.payloadDetailRows"
                    :key="`${selectedPresentation.id}-${row.label}`"
                    class="audit-detail-card"
                  >
                    <span class="audit-detail-label">{{ row.label }}</span>
                    <strong class="audit-detail-value">{{ row.value }}</strong>
                  </div>
                </div>
              </section>

              <details v-if="selectedPresentation.hasTechnicalRows" class="audit-disclosure">
                <summary>Технические данные запроса</summary>
                <div class="audit-disclosure-content">
                  <div class="audit-detail-grid compact">
                    <div
                      v-for="row in selectedPresentation.technicalRows"
                      :key="`${selectedPresentation.id}-tech-${row.label}`"
                      class="audit-detail-card compact"
                    >
                      <span class="audit-detail-label">{{ row.label }}</span>
                      <strong class="audit-detail-value">{{ row.value }}</strong>
                    </div>
                  </div>
                </div>
              </details>

              <details v-if="selectedPresentation.hasRawPayload" class="audit-disclosure">
                <summary>Raw JSON payload</summary>
                <div class="audit-disclosure-content">
                  <div class="code-block-wrapper">
                    <pre class="code-block">{{ selectedPresentation.rawPayload }}</pre>
                  </div>
                </div>
              </details>
            </div>

            <div class="modal-footer">
              <button class="btn btn-secondary" type="button" @click="closeDetails">Закрыть</button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<style scoped>
.audit-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
  padding: 24px;
  color: #0f172a;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 24px;
}

.section-title {
  margin: 0 0 4px;
  font-size: 24px;
  font-weight: 700;
}

.section-subtitle {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: #64748b;
  max-width: 760px;
}

.header-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.filters-section {
  background: #f8fafc;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 16px;
  border: 1px solid #e2e8f0;
}

.filters-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.search-bar {
  position: relative;
  margin-bottom: 16px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  color: #94a3b8;
}

.search-input {
  width: 100%;
  padding-left: 38px !important;
  font-size: 15px;
}

.filters-form .search-bar {
  margin-bottom: 0;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-group label {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.form-input {
  padding: 9px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 13px;
  background: #ffffff;
  transition: all 0.2s ease;
  box-sizing: border-box;
  color: #0f172a;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.filters-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.filters-actions-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.filters-note {
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
}

.results-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.results-toolbar-controls {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  flex-wrap: wrap;
}

.toolbar-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.toolbar-field span {
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.toolbar-select {
  min-width: 170px;
}

.results-caption {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}

.results-caption.muted {
  color: #94a3b8;
}

.audit-list-shell {
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  overflow: hidden;
  background: #ffffff;
}

.audit-list {
  display: flex;
  flex-direction: column;
}

.audit-entry {
  width: 100%;
  text-align: left;
  border: none;
  border-bottom: 1px solid #e2e8f0;
  background: #ffffff;
  padding: 18px 20px;
  cursor: pointer;
  transition: background-color 0.18s ease, transform 0.18s ease;
}

.audit-entry:last-child {
  border-bottom: none;
}

.audit-entry:hover {
  background: #f8fafc;
}

.audit-entry-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.audit-entry-time {
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  white-space: nowrap;
}

.audit-action-chip {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  border: 1px solid transparent;
}

.audit-action-chip.tone-success {
  background: #dcfce7;
  color: #166534;
  border-color: #bbf7d0;
}

.audit-action-chip.tone-warning {
  background: #fef3c7;
  color: #92400e;
  border-color: #fde68a;
}

.audit-action-chip.tone-danger {
  background: #fee2e2;
  color: #991b1b;
  border-color: #fecaca;
}

.audit-action-chip.tone-neutral {
  background: #e2e8f0;
  color: #334155;
  border-color: #cbd5e1;
}

.audit-entry-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.35;
  color: #0f172a;
}

.audit-entry-summary {
  margin: 10px 0 0;
  font-size: 14px;
  line-height: 1.6;
  color: #475569;
}

.audit-entry-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.audit-entry-tag {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  color: #475569;
  font-size: 12px;
  font-weight: 600;
}

.audit-entry-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 18px;
  margin-top: 14px;
}

.audit-entry-meta-item {
  position: relative;
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
}

.audit-entry-meta-item:not(:first-child)::before {
  content: "";
  position: absolute;
  left: -10px;
  top: 50%;
  width: 4px;
  height: 4px;
  border-radius: 999px;
  background: #cbd5e1;
  transform: translateY(-50%);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  min-height: 40px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn svg {
  width: 16px;
  height: 16px;
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

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.load-more-wrapper {
  padding: 16px;
  text-align: center;
  background: #fafafa;
  border-top: 1px solid #e2e8f0;
}

.load-more-btn {
  width: 100%;
  max-width: 320px;
}

.pagination-bar {
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 14px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: #f8fafc;
}

.pagination-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.pagination-title {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.pagination-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.pagination-btn {
  min-width: 106px;
}

.state-container {
  padding: 40px 20px;
  text-align: center;
  color: #64748b;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.state-container.empty svg {
  width: 48px;
  height: 48px;
  color: #cbd5e1;
}

.alert-box {
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
}

.alert-box.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
}

.spinner,
.spinner-large {
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top-color: currentColor;
  animation: spin 0.8s linear infinite;
}

.spinner {
  width: 16px;
  height: 16px;
}

.spinner-large {
  width: 32px;
  height: 32px;
  border-width: 3px;
  border-top-color: #3b82f6;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1200;
  padding: 20px;
}

.audit-modal-card {
  background: #ffffff;
  border-radius: 18px;
  width: min(980px, 100%);
  max-height: calc(100vh - 40px);
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.18);
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.audit-modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.audit-modal-title-block {
  min-width: 0;
}

.audit-modal-head-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.audit-action-code {
  padding: 4px 8px;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  color: #475569;
  font-size: 12px;
  font-family: ui-monospace, monospace;
}

.modal-title {
  margin: 0;
  font-size: 24px;
  line-height: 1.25;
  color: #0f172a;
}

.modal-subtitle {
  margin: 10px 0 0;
  font-size: 14px;
  line-height: 1.65;
  color: #64748b;
}

.audit-modal-close {
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 1px solid #e2e8f0;
  background: rgba(255, 255, 255, 0.72);
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 0;
  flex-shrink: 0;
}

.audit-modal-close:hover {
  background: #ffffff;
  color: #0f172a;
}

.audit-modal-close svg {
  width: 16px;
  height: 16px;
}

.audit-modal-body {
  padding: 24px;
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
  overscroll-behavior: contain;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-label {
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.meta-value {
  font-size: 14px;
  line-height: 1.55;
  color: #0f172a;
  word-break: break-word;
}

.audit-modal-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.audit-section-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.audit-detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.audit-detail-grid.compact {
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  align-items: stretch;
}

.audit-detail-card {
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.audit-detail-card.compact {
  background: #ffffff;
  min-height: 100%;
}

.audit-detail-label {
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #94a3b8;
}

.audit-detail-value {
  font-size: 14px;
  line-height: 1.55;
  color: #0f172a;
  word-break: break-word;
}

.audit-disclosure {
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: #ffffff;
  overflow: hidden;
  box-sizing: border-box;
}

.audit-disclosure summary {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  color: #334155;
  list-style: none;
}

.audit-disclosure summary::-webkit-details-marker {
  display: none;
}

.audit-disclosure summary::after {
  content: "▾";
  margin-left: auto;
  flex-shrink: 0;
  color: #94a3b8;
  transition: transform 0.2s ease;
}

.audit-disclosure[open] summary::after {
  transform: rotate(180deg);
}

.audit-disclosure-content {
  padding: 12px 16px 18px;
  border-top: 1px solid #e2e8f0;
  box-sizing: border-box;
}

.code-block-wrapper {
  margin-top: 0;
  background: #0f172a;
  border-radius: 10px;
  padding: 16px;
}

.code-block {
  margin: 0;
  color: #e2e8f0;
  font-family: ui-monospace, monospace;
  font-size: 13px;
  line-height: 1.55;
  overflow: auto;
  max-height: 420px;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  background: #f8fafc;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.24s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .audit-modal-card,
.modal-leave-active .audit-modal-card {
  transition: transform 0.24s ease, opacity 0.24s ease;
}

.modal-enter-from .audit-modal-card,
.modal-leave-to .audit-modal-card {
  transform: translateY(10px) scale(0.99);
  opacity: 0;
}

:global(html[data-theme='dark']) .audit-card .filters-section,
:global(html[data-theme='dark']) .audit-card .audit-list-shell,
:global(html[data-theme='dark']) .audit-card .audit-entry,
:global(html[data-theme='dark']) .audit-card .audit-detail-card.compact,
:global(html[data-theme='dark']) .audit-card .audit-disclosure {
  background: #0f172a;
  border-color: #334155;
}

:global(html[data-theme='dark']) .audit-card .audit-entry:hover {
  background: #111827;
}

:global(html[data-theme='dark']) .audit-card .section-subtitle,
:global(html[data-theme='dark']) .audit-card .results-caption.muted,
:global(html[data-theme='dark']) .audit-card .audit-entry-time,
:global(html[data-theme='dark']) .audit-card .audit-entry-meta-item,
:global(html[data-theme='dark']) .audit-card .filter-group label,
:global(html[data-theme='dark']) .audit-card .meta-label,
:global(html[data-theme='dark']) .audit-card .filters-note,
:global(html[data-theme='dark']) .audit-card .toolbar-field span {
  color: #94a3b8;
}

:global(html[data-theme='dark']) .audit-card .section-title,
:global(html[data-theme='dark']) .audit-card .audit-entry-title,
:global(html[data-theme='dark']) .audit-card .results-caption,
:global(html[data-theme='dark']) .audit-card .audit-section-title,
:global(html[data-theme='dark']) .audit-card .audit-detail-value,
:global(html[data-theme='dark']) .audit-card .meta-value,
:global(html[data-theme='dark']) .audit-card .pagination-title {
  color: #e2e8f0;
}

:global(html[data-theme='dark']) .audit-card .audit-entry-summary {
  color: #cbd5e1;
}

:global(html[data-theme='dark']) .audit-card .form-input,
:global(html[data-theme='dark']) .audit-card .pagination-bar {
  background: #111827;
  border-color: #334155;
  color: #e2e8f0;
}

:global(html[data-theme='dark']) .audit-card .audit-entry-tag,
:global(html[data-theme='dark']) .audit-card .audit-action-code,
:global(html[data-theme='dark']) .audit-card .load-more-wrapper {
  background: #111827;
  border-color: #334155;
  color: #cbd5e1;
}

:global(html[data-theme='dark']) .audit-card .audit-action-chip.tone-success {
  background: rgba(22, 101, 52, 0.28);
  border-color: rgba(74, 222, 128, 0.28);
  color: #bbf7d0;
}

:global(html[data-theme='dark']) .audit-card .audit-action-chip.tone-warning {
  background: rgba(133, 77, 14, 0.28);
  border-color: rgba(250, 204, 21, 0.24);
  color: #fde68a;
}

:global(html[data-theme='dark']) .audit-card .audit-action-chip.tone-danger {
  background: rgba(153, 27, 27, 0.3);
  border-color: rgba(248, 113, 113, 0.28);
  color: #fecaca;
}

:global(html[data-theme='dark']) .audit-card .audit-action-chip.tone-neutral {
  background: rgba(51, 65, 85, 0.86);
  border-color: rgba(100, 116, 139, 0.8);
  color: #e2e8f0;
}

:global(html[data-theme='dark']) .audit-card .btn-secondary {
  background: #1e293b;
  border-color: #334155;
  color: #cbd5e1;
}

:global(html[data-theme='dark']) .audit-card .btn-secondary:hover:not(:disabled) {
  background: #334155;
  color: #f8fafc;
}

:global(html[data-theme='dark']) .audit-card .alert-box.error {
  background: rgba(127, 29, 29, 0.28);
  border-color: rgba(248, 113, 113, 0.42);
  color: #fecaca;
}

:global(html[data-theme='dark']) .audit-log-modal-overlay .audit-modal-card,
:global(html[data-theme='dark']) .audit-log-modal-overlay .audit-detail-card,
:global(html[data-theme='dark']) .audit-log-modal-overlay .audit-disclosure {
  background: #111827;
  border-color: #334155;
}

:global(html[data-theme='dark']) .audit-log-modal-overlay .audit-modal-header,
:global(html[data-theme='dark']) .audit-log-modal-overlay .modal-footer {
  border-color: #334155;
  background: #111827;
}

:global(html[data-theme='dark']) .audit-log-modal-overlay .modal-title,
:global(html[data-theme='dark']) .audit-log-modal-overlay .audit-section-title,
:global(html[data-theme='dark']) .audit-log-modal-overlay .audit-detail-value,
:global(html[data-theme='dark']) .audit-log-modal-overlay .meta-value {
  color: #f8fafc;
}

:global(html[data-theme='dark']) .audit-log-modal-overlay .modal-subtitle,
:global(html[data-theme='dark']) .audit-log-modal-overlay .meta-label,
:global(html[data-theme='dark']) .audit-log-modal-overlay .audit-detail-label,
:global(html[data-theme='dark']) .audit-log-modal-overlay .audit-disclosure summary,
:global(html[data-theme='dark']) .audit-log-modal-overlay .audit-action-code {
  color: #94a3b8;
}

:global(html[data-theme='dark']) .audit-log-modal-overlay .audit-action-code,
:global(html[data-theme='dark']) .audit-log-modal-overlay .audit-detail-card.compact {
  background: #0f172a;
  border-color: #334155;
}

:global(html[data-theme='dark']) .audit-log-modal-overlay .audit-disclosure-content {
  border-top-color: #334155;
}

:global(html[data-theme='dark']) .audit-log-modal-overlay .audit-modal-close {
  background: rgba(15, 23, 42, 0.82);
  border-color: #334155;
  color: #94a3b8;
}

:global(html[data-theme='dark']) .audit-log-modal-overlay .audit-modal-close:hover {
  background: rgba(30, 41, 59, 0.96);
  color: #f8fafc;
}

@media (max-width: 900px) {
  .audit-entry-top,
  .results-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .results-toolbar-controls,
  .filters-actions,
  .pagination-actions {
    width: 100%;
  }

  .toolbar-field,
  .toolbar-select {
    width: 100%;
  }

  .audit-entry-time {
    white-space: normal;
  }

  .audit-modal-header {
    flex-direction: column;
  }

  .audit-modal-close {
    align-self: flex-end;
  }
}

@media (max-width: 720px) {
  .audit-card {
    padding: 16px;
  }

  .header-actions,
  .filters-grid {
    grid-template-columns: 1fr;
    width: 100%;
  }

  .header-actions {
    display: grid;
  }

  .header-actions .btn {
    width: 100%;
  }

  .filters-actions-row,
  .pagination-actions {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr;
  }

  .filters-actions-row .btn,
  .pagination-actions .btn {
    width: 100%;
  }

  .audit-entry {
    padding: 16px;
  }

  .audit-entry-title {
    font-size: 16px;
  }

  .audit-modal-body,
  .audit-modal-header,
  .modal-footer {
    padding-left: 16px;
    padding-right: 16px;
  }

  .audit-detail-grid,
  .meta-grid {
    grid-template-columns: 1fr;
  }
}
</style>
