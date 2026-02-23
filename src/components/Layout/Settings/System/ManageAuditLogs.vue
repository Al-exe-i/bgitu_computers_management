<script>
import api from "@/services/api";
import { useNotificationsStore } from "@/stores/notifications";
import { useAuthStore } from "@/stores/auth";

const AUDIT_ENDPOINT = "/admin/audit-log";

export default {
  name: "ManageAuditLogs",

  data() {
    return {
      logs: [],
      loading: false,
      error: null,

      // пагинация
      page: 1,
      pageSize: 50,
      hasMore: true,

      // фильтры
      filters: {
        q: "",
        action: "",
        entity_type: "",
        entity_id: "",
        user_id: "",
      },

      // debounce
      _timer: null,

      // details modal
      showDetails: false,
      selected: null,
    };
  },

  computed: {
    notify() { return useNotificationsStore(); },
    authStore() { return useAuthStore(); },
  },

  methods: {
    normalizeItems(resData) {
      if (Array.isArray(resData)) return { items: resData, total: null };
      if (resData?.items && Array.isArray(resData.items)) return { items: resData.items, total: resData.total ?? null };
      return { items: [], total: null };
    },

    buildParams() {
      const offset = (this.page - 1) * this.pageSize;
      const params = { limit: this.pageSize, offset };

      Object.entries(this.filters).forEach(([k, v]) => {
        const val = (v ?? "").toString().trim();
        if (val !== "") params[k] = val;
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

        const params = this.buildParams();
        const res = await api.get(AUDIT_ENDPOINT, { params });
        const { items } = this.normalizeItems(res.data);

        if (reset) this.logs = items;
        else this.logs.push(...items);

        this.hasMore = items.length === this.pageSize;
      } catch (e) {
        const msg = e.response?.data?.detail || "Не удалось загрузить журнал";
        this.error = msg;
        this.notify.error(msg);
      } finally {
        this.loading = false;
      }
    },

    applyFilters() {
      clearTimeout(this._timer);
      this._timer = setTimeout(() => {
        this.fetchLogs({ reset: true });
      }, 300);
    },

    clearFilters() {
      this.filters = {
        q: "", action: "", entity_type: "", entity_id: "",
        user_id: ""
      };
      this.fetchLogs({ reset: true });
    },

    loadMore() {
      if (!this.hasMore || this.loading)
        return;
      this.page += 1;
      this.fetchLogs({ reset: false });
    },

    openDetails(item) {
      this.selected = item;
      this.showDetails = true;
      document.body.style.overflow = 'hidden'; // Блокируем скролл фона
    },

    closeDetails() {
      this.showDetails = false;
      this.selected = null;
      document.body.style.overflow = '';
    },

    fmtTs(value) {
      if (!value)
        return "—";
      const d = new Date(value);
      if (Number.isNaN(d.getTime()))
        return value;
      return new Intl.DateTimeFormat('ru-RU', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit', second: '2-digit'
      }).format(d);
    },

    safeJson(obj) {
      try {
        return JSON.stringify(obj ?? {}, null, 2);
      }
      catch {
        return String(obj);
      }
    },

    getUserLabel(item) {
      if (item?.user?.email) return item.user.email;
      if (item?.user_id != null) return `ID ${item.user_id}`;
      return "—";
    },

    getEntityLabel(item) {
      const type = item?.entity_type ?? "—";
      const id = item?.entity_id ?? "—";
      return id !== "—" ? `${type} #${id}` : type;
    },

    getMethodBadgeClass(method) {
      const m = (method || "").toUpperCase();
      const map = {
        'GET': 'badge-get',
        'POST': 'badge-post',
        'PUT': 'badge-put',
        'PATCH': 'badge-put',
        'DELETE': 'badge-delete',
      };
      return map[m] || 'badge-default';
    }
  },

  watch: {
    filters: {
      deep: true,
      handler() { this.applyFilters(); }
    }
  },

  mounted() {
    this.fetchLogs({ reset: true });
  },

  beforeUnmount() {
    clearTimeout(this._timer);
    document.body.style.overflow = '';
  }
};
</script>

<template>
  <div class="audit-card">
    <!-- Header -->
    <div class="card-header">
      <div>
        <h2 class="section-title">Журнал действий</h2>
        <p class="section-subtitle">Отслеживание активности пользователей и изменений в системе</p>
      </div>

      <div class="header-actions">
        <button class="btn btn-secondary" @click="clearFilters">Сбросить фильтры</button>
        <button class="btn btn-primary" @click="fetchLogs({ reset: true })" :disabled="loading">
          <svg v-if="loading" class="spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a10 10 0 0 1 10 10"></path></svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
          Обновить
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-section">
      <div class="search-bar">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <input class="form-input search-input" v-model="filters.q" placeholder="Глобальный поиск (payload, путь, действие)..." />
      </div>

      <div class="filters-grid">
        <div class="filter-group">
          <label>Действие (Action)</label>
          <input class="form-input" v-model="filters.action" placeholder="Напр. user.login"/>
        </div>
        <div class="filter-group">
          <label>Сущность (Entity)</label>
          <input class="form-input" v-model="filters.entity_type" placeholder="Напр. office"/>
        </div>
        <div class="filter-group">
          <label>ID сущности</label>
          <input class="form-input" v-model="filters.entity_id" placeholder="ID"/>
        </div>
        <div class="filter-group">
          <label>ID пользователя</label>
          <input class="form-input" v-model="filters.user_id" placeholder="UUID / ID"/>
        </div>
      </div>
    </div>

    <div v-if="error" class="alert-box error">{{ error }}</div>

    <!-- Table -->
    <div class="table-container">
      <table class="data-table">
        <thead>
        <tr>
          <th>Время</th>
          <th>Пользователь</th>
          <th>Действие</th>
          <th>Сущность</th>
          <th>Запрос</th>
          <th>IP адрес</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="item in logs" :key="item.id" @click="openDetails(item)" class="clickable-row">
          <td class="whitespace-nowrap">{{ fmtTs(item.created_at || item.createdAt) }}</td>
          <td class="font-medium">{{ getUserLabel(item) }}</td>
          <td><span class="code-badge">{{ item.action || "—" }}</span></td>
          <td>{{ getEntityLabel(item) }}</td>
          <td>
            <div class="request-cell">
              <span :class="['method-badge', getMethodBadgeClass(item.method)]">{{ item.method || "ANY" }}</span>
              <span class="path-text" :title="item.path">{{ item.path || "—" }}</span>
            </div>
          </td>
          <td><span class="ip-text">{{ item.ip || "—" }}</span></td>
        </tr>
        </tbody>
      </table>

      <!-- Empty / Loading States -->
      <div v-if="loading && logs.length === 0" class="state-container">
        <div class="spinner-large"></div>
        <p>Загрузка логов...</p>
      </div>
      <div v-else-if="logs.length === 0" class="state-container empty">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>
        <p>Записей по заданным фильтрам не найдено</p>
      </div>

      <div v-if="hasMore && logs.length > 0" class="load-more-wrapper">
        <button class="btn btn-secondary load-more-btn" @click="loadMore" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          {{ loading ? 'Загрузка...' : 'Показать следующие записи' }}
        </button>
      </div>
    </div>

    <!-- Details Modal -->
    <transition name="modal">
      <div v-if="showDetails && selected" class="modal-overlay" @click.self="closeDetails">
        <div class="modal-card">
          <div class="modal-header">
            <h3 class="modal-title">Детали события: <code>{{ selected.action }}</code></h3>
            <button class="close-btn" @click="closeDetails">✕</button>
          </div>

          <div class="modal-body">
            <div class="meta-grid">
              <div class="meta-item">
                <span class="meta-label">Время</span>
                <span class="meta-value">{{ fmtTs(selected.created_at || selected.createdAt) }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">Пользователь</span>
                <span class="meta-value font-medium">{{ getUserLabel(selected) }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">Сущность</span>
                <span class="meta-value">{{ getEntityLabel(selected) }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">IP Адрес</span>
                <span class="meta-value">{{ selected.ip || "—" }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">Метод</span>
                <span :class="['method-badge', getMethodBadgeClass(selected.method)]">{{ selected.method || "—" }}</span>
              </div>
              <div class="meta-item col-span-full">
                <span class="meta-label">Путь (URL)</span>
                <span class="meta-value path-text">{{ selected.path || "—" }}</span>
              </div>
              <div class="meta-item col-span-full">
                <span class="meta-label">User-Agent</span>
                <span class="meta-value text-muted">{{ selected.user_agent || selected.userAgent || "—" }}</span>
              </div>
            </div>

            <div class="payload-section">
              <h4 class="meta-label">Данные (Payload)</h4>
              <div class="code-block-wrapper">
                <pre class="code-block">{{ safeJson(selected.payload) }}</pre>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" @click="closeDetails">Закрыть</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
/* --- Base Variables & Layout --- */
.audit-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
  padding: 24px;
  font-family: system-ui, -apple-system, sans-serif;
  color: #0f172a;
}

/* --- Header --- */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}
.section-title { margin: 0 0 4px 0; font-size: 24px; font-weight: 600; }
.section-subtitle { margin: 0; font-size: 14px; color: #64748b; }
.header-actions { display: flex; gap: 12px; }

/* --- Filters --- */
.filters-section {
  background: #f8fafc;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 24px;
  border: 1px solid #e2e8f0;
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
.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}
.filter-group { display: flex; flex-direction: column; gap: 4px; }
.filter-group label { font-size: 12px; font-weight: 500; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
.form-input {
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 13px;
  background: #fff;
  transition: all 0.2s;
  box-sizing: border-box;
  color: #0f172a;
}
.form-input:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15); }

/* --- Table --- */
.table-container {
  overflow-x: auto;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 13px;
}
.data-table th {
  background: #f8fafc;
  padding: 12px 16px;
  font-weight: 600;
  color: #475569;
  border-bottom: 2px solid #e2e8f0;
  position: sticky;
  top: 0;
  z-index: 10;
}
.data-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
  color: #334155;
}
.clickable-row { cursor: pointer; transition: background-color 0.15s; }
.clickable-row:hover { background-color: #f1f5f9; }

/* --- Typografy & Badges in Table --- */
.whitespace-nowrap { white-space: nowrap; }
.font-medium { font-weight: 500; color: #0f172a; }
.text-muted { color: #64748b; }
.ip-text { font-family: ui-monospace, monospace; color: #475569; font-size: 12px; }

.code-badge {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: ui-monospace, monospace;
  font-size: 12px;
  color: #334155;
}

.request-cell { display: flex; align-items: center; gap: 8px; }
.path-text {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: ui-monospace, monospace;
  font-size: 12px;
  color: #475569;
}

.method-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
}
.badge-get { background: #dcfce7; color: #166534; }
.badge-post { background: #dbeafe; color: #1e40af; }
.badge-put { background: #fef9c3; color: #854d0e; }
.badge-delete { background: #fee2e2; color: #991b1b; }
.badge-default { background: #f1f5f9; color: #475569; }

/* --- Buttons --- */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}
.btn svg { width: 16px; height: 16px; }
.btn-primary { background: #0f172a; color: white; }
.btn-primary:hover:not(:disabled) { background: #334155; }
.btn-secondary { background: #f1f5f9; color: #0f172a; border: 1px solid #e2e8f0; }
.btn-secondary:hover:not(:disabled) { background: #e2e8f0; }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }

.load-more-wrapper { padding: 16px; text-align: center; background: #fafafa; border-top: 1px solid #e2e8f0; }
.load-more-btn { width: 100%; max-width: 300px; }

/* --- States (Loading/Empty/Error) --- */
.state-container { padding: 40px 20px; text-align: center; color: #64748b; display: flex; flex-direction: column; align-items: center; gap: 12px;}
.state-container.empty svg { width: 48px; height: 48px; color: #cbd5e1; }
.alert-box { padding: 12px 16px; border-radius: 6px; margin-bottom: 20px; font-size: 14px; }
.alert-box.error { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; }

.spinner, .spinner-large {
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top-color: currentColor;
  animation: spin 0.8s linear infinite;
}
.spinner { width: 16px; height: 16px; }
.spinner-large { width: 32px; height: 32px; border-width: 3px; border-top-color: #3b82f6; }
@keyframes spin { to { transform: rotate(360deg); } }

/* --- Modal --- */
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000; padding: 20px;
}
.modal-card {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}
.modal-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e2e8f0;
  display: flex; justify-content: space-between; align-items: center;
}
.modal-title { margin: 0; font-size: 18px; display: flex; gap: 8px; align-items: center; }
.modal-title code { background: #f1f5f9; padding: 4px 8px; border-radius: 6px; font-size: 14px; color: #3b82f6; }
.close-btn { background: none; border: none; font-size: 20px; color: #94a3b8; cursor: pointer; transition: color 0.2s; padding: 4px; }
.close-btn:hover { color: #0f172a; }

.modal-body {
  padding: 24px;
  overflow-y: auto;
}
.meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.col-span-full { grid-column: 1 / -1; }
.meta-item { display: flex; flex-direction: column; gap: 4px; }
.meta-label { font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
.meta-value { font-size: 14px; color: #0f172a; word-break: break-word; }

.payload-section { border-top: 1px solid #e2e8f0; padding-top: 20px; }
.code-block-wrapper { margin-top: 8px; background: #0f172a; border-radius: 8px; padding: 16px; }
.code-block {
  margin: 0;
  color: #e2e8f0;
  font-family: ui-monospace, monospace;
  font-size: 13px;
  overflow-x: auto;
  max-height: 400px;
  line-height: 1.5;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e2e8f0;
  display: flex; justify-content: flex-end;
  background: #f8fafc;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
}

/* Modal Animations */
.modal-enter-active, .modal-leave-active { transition: opacity 0.3s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-active .modal-card { animation: modal-slide-in 0.3s ease-out; }
.modal-leave-active .modal-card { animation: modal-slide-in 0.3s ease-out reverse; }
@keyframes modal-slide-in {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>
