<script>
import api from "@/services/api";
import { useAuthStore } from "@/stores/auth";
import { useNotificationsStore } from "@/stores/notifications";
import { useOfficeStore } from "@/stores/offices.js";
import router from "@/router/index.js";

export default {
  name: "ManageAudiences",

  data() {
    return {
      loading: true,
      audiences: [],

      // фильтры
      filters: {
        office_id: null,
        floor: null,
        q: "",
      },

    };
  },

  computed: {
    authStore() {
      return useAuthStore();
    },

    officeStore() {
      return useOfficeStore();
    },

    notify() {
      return useNotificationsStore();
    },

    offices() {
      return this.officeStore.list || [];
    },

    isAdmin() {
      return this.authStore.user?.role === 1;
    },

    officesMap() {
      const m = new Map();
      for (const o of this.offices) m.set(o.id, o);
      return m;
    },

    filteredAudiences() {
      const q = (this.filters.q || "").trim().toLowerCase();

      return (this.audiences || []).filter(a => {
        if (this.filters.office_id && a.office_id !== this.filters.office_id) return false;
        if (this.filters.floor !== null && this.filters.floor !== "" && a.floor !== this.filters.floor) return false;

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
      return o ? `№${o.id} — ${o.address}` : `№${office_id}`;
    },

    async fetchAll() {
      this.loading = true;
      try {
        await this.officeStore.fetchOffices();
        const res = await api.get("/audiences");
        this.audiences = res.data || [];
      } catch (e) {
        this.notify.error("Ошибка загрузки аудиторий");
      } finally {
        this.loading = false;
      }
    },

    goToGrid(a) {
      router.push({ name: 'ChangeAudience', params: { id: a.id } });
    },

    goToCreate() {
      router.push({ name: 'New Audience' });
    },

    async deleteAudience(a) {
      const confirmText =
          `Удалить аудиторию ${a.id}?\n` +
          `Оборудование удалится каскадно (как в описании эндпоинта).`;

      if (!confirm(confirmText)) return;

      try {
        await api.delete(`/audiences/${a.id}`);
        this.audiences = this.audiences.filter(x => x.id !== a.id);
        this.notify.success("Аудитория удалена");
      } catch (e) {
        const msg = e.response?.data?.detail || "Ошибка удаления";
        this.notify.error(msg);
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
    <div class="card-header">
      <h2>Аудитории</h2>
      <button class="btn-primary" @click="goToCreate">
        + Добавить аудиторию
      </button>
    </div>

    <div class="filters">
      <select class="form-select" v-model.number="filters.office_id">
        <option :value="null">Все корпуса</option>
        <option v-for="o in offices" :key="o.id" :value="o.id">
          {{ officeLabel(o.id) }}
        </option>
      </select>

      <input class="form-input" type="number" placeholder="Этаж" v-model.number="filters.floor" min="0" />

      <input class="form-input" type="text" placeholder="Поиск (номер/описание)" v-model="filters.q" />
    </div>

    <div class="table-wrapper">
      <table class="data-table">
        <thead>
        <tr>
          <th>№</th>
          <th>Корпус</th>
          <th>Этаж</th>
          <th>Сетка</th>
          <th>Оборудования</th>
          <th v-if="isAdmin">Действия</th>
        </tr>
        </thead>

        <tbody>
        <tr v-for="a in filteredAudiences" :key="a.id">
          <td><span class="aud-number">№{{ a.id }}</span></td>
          <td class="muted">{{ officeLabel(a.office_id) }}</td>
          <td>{{ a.floor }}</td>
          <td>{{ a.width }} × {{ a.height }}</td>
          <td>
            <span class="count-badge">{{ a.hardware ? a.hardware.length : 0 }}</span>
          </td>

          <td v-if="isAdmin">
            <div class="actions-group">
              <button class="btn-icon" title="Редактировать" @click="goToGrid(a)">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
              </button>

              <button class="btn-icon delete" title="Удалить" @click="deleteAudience(a)">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
              </button>
            </div>
          </td>
        </tr>
        </tbody>
      </table>

      <div v-if="loading" class="loading-state">Загрузка списка аудиторий...</div>
      <div v-else-if="filteredAudiences.length === 0" class="empty-state">Нет данных</div>
    </div>

  </div>
</template>

<style scoped>
.card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }

.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; gap: 12px; }
.card-header h2 { font-size: 18px; color: #0f172a; margin: 0; }

.filters { display: grid; grid-template-columns: 1fr 120px 1fr; gap: 10px; margin-bottom: 14px; }

.table-wrapper { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; min-width: 700px; }

.data-table th {
  text-align: left; padding: 12px 10px; color: #64748b; font-size: 12px; font-weight: 600;
  text-transform: uppercase; border-bottom: 1px solid #e2e8f0;
}
.data-table td { padding: 12px 10px; border-bottom: 1px solid #f1f5f9; color: #334155; font-size: 14px; vertical-align: middle; }

.aud-number { font-weight: 600; color: #0f172a; }
.muted { color: #64748b; }

.count-badge { display: inline-block; padding: 4px 8px; border-radius: 999px; background: #f1f5f9; color: #334155; font-size: 12px; }

.actions-group { display: flex; gap: 8px; }

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px;
  color: #94a3b8;
  transition: color 0.2s;
}

.btn-icon:hover {
  color: #3b82f6;
}

.btn-icon.delete:hover {
  color: #ef4444;
}

.loading-state, .empty-state { padding: 12px; color: #64748b; }

.form-input, .form-select
{
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  outline: none;
}

.form-select:focus, .form-input:focus {
  border-color: #3b82f6;
}

.form-select {
  background-color: #fff;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  transition: border-color 0.2s;
  background-image: url("data:image/svg+xml,%3Csvg width='12' height='8' viewBox='0 0 12 8' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%236b7280' stroke-width='2' fill='none'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
}

.form-input.error {
  border-color: #ef4444;
}

.btn-primary { background: #3b82f6; color: white; border: none; padding: 10px 12px; border-radius: 10px; cursor: pointer; }
.btn-secondary { background: #f1f5f9; color: #0f172a; border: 1px solid #e2e8f0; padding: 10px 12px; border-radius: 10px; cursor: pointer; }
</style>
