<script>
import api from "@/services/api";
import { useAuthStore } from "@/stores/auth";
import { useNotificationsStore } from "@/stores/notifications";
import { useOfficeStore } from "@/stores/offices";

export default {
  name: "ManageAudiences",

  data() {
    return {
      // Глобальная загрузка при первом открытии
      loading: true,
      audiences: [],

      // Сюда будем складывать ID аудиторий, которые прямо сейчас удаляются сервером.
      // Это нужно, чтобы крутить спиннер только на одной кнопке, а не блокировать весь экран.
      deletingIds: [],

      filters: {
        office_id: null,
        floor: null,
        q: "",
      },
    };
  },

  computed: {
    authStore() { return useAuthStore(); },
    officeStore() { return useOfficeStore(); },
    notify() { return useNotificationsStore(); },

    offices() {
      return this.officeStore.list || [];
    },

    isAdmin() {
      return this.authStore.user?.role === 1;
    },

    officesMap() {
      // Превращаем массив корпусов в Map для мгновенного поиска по ID (O(1) вместо O(N))
      const m = new Map();
      for (const o of this.offices) {
        m.set(o.id, o);
      }
      return m;
    },

    filteredAudiences() {
      const q = (this.filters.q || "").trim().toLowerCase();

      return (this.audiences || []).filter(a => {
        // Если выбран конкретный корпус, отсекаем чужие
        if (this.filters.office_id && a.office_id !== this.filters.office_id) return false;

        // Внимательно проверяем этаж (он может быть 0, поэтому строгая проверка на null и пустую строку)
        if (this.filters.floor !== null && this.filters.floor !== "" && a.floor !== this.filters.floor) return false;

        // Поиск по строке (ищем сразу везде: ID, описание, корпус, этаж)
        if (q) {
          const hay = `${a.id} ${a.description || ""} ${a.office_id} ${a.floor}`.toLowerCase();
          if (!hay.includes(q)) return false;
        }

        return true;
      });
    },
  },

  methods: {
    officeLabel(office_id) {
      const o = this.officesMap.get(office_id);
      return o ? `№${o.id} — ${o.address}` : `Корпус №${office_id}`;
    },

    async fetchAll() {
      this.loading = true;
      try {
        await this.officeStore.fetchOffices();
        const res = await api.get("/audiences");
        this.audiences = res.data || [];
      } catch (e) {
        this.notify.error("Ошибка загрузки аудиторий. Попробуйте обновить страницу.");
      } finally {
        this.loading = false;
      }
    },

    goToGrid(a) {
      this.$router.push({ name: 'ChangeAudience', params: { id: a.id } });
    },

    goToCreate() {
      this.$router.push({ name: 'New Audience' });
    },

    async deleteAudience(a) {
      if (!confirm(`Удалить аудиторию №${a.id}?\n\nВнимание: всё привязанное оборудование также будет безвозвратно удалено.`)) {
        return;
      }

      // Добавляем ID в массив удаляемых (чтобы показать спиннер на кнопке)
      this.deletingIds.push(a.id);

      try {
        await api.delete(`/audiences/${a.id}`);
        // Реактивно выкидываем удаленную аудиторию из списка без перезагрузки всей страницы
        this.audiences = this.audiences.filter(x => x.id !== a.id);
        this.notify.success(`Аудитория №${a.id} успешно удалена`);
      } catch (e) {
        const msg = e.response?.data?.detail || "Произошла ошибка при удалении";
        this.notify.error(msg);
      } finally {
        // Убираем ID из массива удаляемых (возвращаем кнопку в нормальное состояние)
        this.deletingIds = this.deletingIds.filter(id => id !== a.id);
      }
    },
  },

  mounted() {
    this.fetchAll();
  },
};
</script>

<template>
  <div class="card">
    <!-- Шапка компонента -->
    <div class="card-header">
      <div>
        <h2 class="section-title">Аудитории</h2>
        <p class="section-subtitle">Управление аудиториями</p>
      </div>
      <button v-if="isAdmin" class="btn btn-primary" @click="goToCreate">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        Добавить
      </button>
    </div>

    <!-- Блок фильтрации -->
    <div class="filters-container">
      <div class="filter-group">
        <select class="form-select" v-model.number="filters.office_id">
          <option :value="null">Все корпуса</option>
          <option v-for="o in offices" :key="o.id" :value="o.id">
            {{ officeLabel(o.id) }}
          </option>
        </select>
      </div>

      <div class="filter-group floor-input">
        <input class="form-input" type="number" placeholder="Этаж" v-model.number="filters.floor" min="0" />
      </div>

      <div class="filter-group search-input">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <input class="form-input with-icon" type="text" placeholder="Поиск по номеру или описанию..." v-model="filters.q" />
      </div>
    </div>

    <!-- Таблица данных -->
    <div class="table-wrapper">
      <table class="data-table">
        <thead>
        <tr>
          <th width="80">№</th>
          <th>Корпус</th>
          <th width="80">Этаж</th>
          <th>Сетка (Ш×В)</th>
          <th width="140">Оборудование</th>
          <th v-if="isAdmin" width="100" class="text-right">Действия</th>
        </tr>
        </thead>

        <tbody>
        <!-- Если список пуст или грузится, скрываем строки, чтобы не мелькали пустые рамки -->
        <template v-if="!loading && filteredAudiences.length > 0">
          <tr v-for="a in filteredAudiences" :key="a.id" class="table-row">
            <td><span class="aud-number">{{ a.id }}</span></td>
            <td>
              <div class="office-cell">
                <span class="office-name">{{ officeLabel(a.office_id) }}</span>
              </div>
            </td>
            <td><span class="badge-neutral">{{ a.floor }}</span></td>
            <td class="text-muted">{{ a.width }} × {{ a.height }}</td>
            <td>
              <!-- Опциональная цепочка ?. спасает от падения, если hardware вдруг придет null -->
              <span class="badge-count" :class="{ 'is-empty': !(a.hardware?.length) }">
                  {{ a.hardware?.length || 0 }} шт.
                </span>
            </td>

            <td v-if="isAdmin" class="text-right">
              <div class="actions-group">
                <button class="action-btn edit" title="Редактировать" @click="goToGrid(a)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                </button>

                <!-- Умная кнопка удаления: блокируется и крутит спиннер, если удаляется ИМЕННО ЭТА строка -->
                <button
                    class="action-btn delete"
                    title="Удалить"
                    @click="deleteAudience(a)"
                    :disabled="deletingIds.includes(a.id)"
                >
                  <span v-if="deletingIds.includes(a.id)" class="spinner-small"></span>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
              </div>
            </td>
          </tr>
        </template>
        </tbody>
      </table>

      <!-- Состояние загрузки -->
      <div v-if="loading" class="state-container">
        <div class="spinner-large"></div>
        <p>Загрузка аудиторий...</p>
      </div>

      <!-- Состояние "Ничего не найдено" -->
      <div v-else-if="filteredAudiences.length === 0" class="state-container empty">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
        <p>Аудитории не найдены.</p>
        <span class="state-hint">Попробуйте изменить параметры фильтрации.</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* --- Базовая карточка --- */
.card {
  background: #ffffff;
  padding: 24px;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
  font-family: system-ui, -apple-system, sans-serif;
  color: #0f172a;
}

/* --- Шапка --- */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 16px;
  flex-wrap: wrap;
}
.section-title { margin: 0 0 4px 0; font-size: 20px; font-weight: 600; }
.section-subtitle { margin: 0; font-size: 14px; color: #64748b; }

/* --- Фильтры (Адаптивные) --- */
.filters-container {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  background: #f8fafc;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.filter-group { flex: 1; min-width: 200px; position: relative; }
.floor-input { flex: 0 1 120px; min-width: 100px; }
.search-input { flex: 2; min-width: 250px; }

.search-icon {
  position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
  width: 16px; height: 16px; color: #94a3b8;
}

.form-input, .form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  color: #0f172a;
  background: #ffffff;
  transition: all 0.2s ease;
  box-sizing: border-box;
}
.form-input.with-icon { padding-left: 36px; }

.form-input:focus, .form-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.form-select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg width='12' height='8' viewBox='0 0 12 8' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1.5L6 6.5L11 1.5' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
  padding-right: 36px;
}

/* --- Таблица --- */
.table-wrapper {
  overflow-x: auto;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 700px;
  text-align: left;
}

.data-table th {
  padding: 14px 16px;
  background: #f8fafc;
  color: #475569;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid #e2e8f0;
}

.data-table td {
  padding: 14px 16px;
  border-bottom: 1px solid #e2e8f0;
  font-size: 14px;
  vertical-align: middle;
}

.table-row { transition: background-color 0.15s ease; }
.table-row:hover { background-color: #f1f5f9; }
.table-row:last-child td { border-bottom: none; }

.text-muted { color: #64748b; }
.text-right { text-align: right; }

.aud-number {
  font-weight: 700;
  color: #0f172a;
  background: #f1f5f9;
  padding: 4px 8px;
  border-radius: 6px;
  font-family: ui-monospace, monospace;
}

.badge-neutral {
  background: #e2e8f0;
  color: #334155;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 500;
  font-size: 13px;
}

.badge-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #dcfce7;
  color: #166534;
  padding: 4px 10px;
  border-radius: 999px;
  font-weight: 600;
  font-size: 12px;
}
.badge-count.is-empty { background: #f1f5f9; color: #64748b; font-weight: 500; }

/* --- Кнопки действий --- */
.actions-group {
  display: inline-flex;
  gap: 4px;
  justify-content: flex-end;
}

.action-btn {
  background: none;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #94a3b8;
  transition: all 0.2s ease;
}
.action-btn svg { width: 18px; height: 18px; }

.action-btn.edit:hover { background: #eff6ff; color: #3b82f6; }
.action-btn.delete:hover:not(:disabled) { background: #fee2e2; color: #ef4444; }
.action-btn.delete:disabled { opacity: 0.5; cursor: not-allowed; }

.btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 18px; border-radius: 8px;
  font-size: 14px; font-weight: 500; border: none; cursor: pointer;
  transition: all 0.2s ease;
}
.btn svg { width: 18px; height: 18px; }
.btn-primary { background: #0f172a; color: white; }
.btn-primary:hover { background: #334155; transform: translateY(-1px); }

/* --- Состояния (Спиннеры и Пустота) --- */
.state-container {
  padding: 60px 20px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #64748b;
}

.state-container.empty svg { width: 48px; height: 48px; color: #cbd5e1; }
.state-container p { margin: 0; font-size: 15px; font-weight: 500; color: #334155; }
.state-hint { font-size: 13px; color: #94a3b8; }

.spinner-large {
  width: 32px; height: 32px;
  border: 3px solid rgba(59, 130, 246, 0.2);
  border-radius: 50%;
  border-top-color: #3b82f6;
  animation: spin 0.8s linear infinite;
}

.spinner-small {
  width: 16px; height: 16px;
  border: 2px solid rgba(239, 68, 68, 0.2);
  border-radius: 50%;
  border-top-color: #ef4444;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
