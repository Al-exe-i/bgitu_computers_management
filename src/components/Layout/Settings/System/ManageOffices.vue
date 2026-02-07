<script>
import api from "@/services/api";
import { useAuthStore } from "@/stores/auth";
import { useNotificationsStore } from "@/stores/notifications";
import {useOfficeStore} from "@/stores/offices.js";

export default {
  name: "ManageOffices",
  data() {
    return {
      offices: [],
      loading: true,

      // Модалка
      showModal: false,
      isEditMode: false,
      officeAlreadyExists: false,
      form: {
        id: null,
        address: ''
      }
    };
  },

  computed: {
    authStore() { return useAuthStore(); },
    officeStore() { return useOfficeStore(); },
    offices() { return this.officeStore.list; },
    loading() { return this.officeStore.loading; },
    notify() { return useNotificationsStore(); },
    isSuperuser() { return this.authStore.user?.is_superuser === true; }
  },

  methods: {
    async fetchOffices() {
      await this.officeStore.fetchOffices();
    },

    openCreateModal() {
      this.isEditMode = false;
      this.form = { id: null, address: '' };
      this.showModal = true;
    },

    openEditModal(office) {
      this.isEditMode = true;
      // Копируем данные
      this.form = { id: office.id, address: office.address };
      this.showModal = true;
    },

    closeModal() {
      this.showModal = false;
    },

    async saveOffice() {
      try
      {
        if (this.isEditMode)
        {
          await api.patch(`/offices/${this.form.id}`, { address: this.form.address });
          this.notify.success(`Корпус №${this.form.id} обновлен`);
          this.officeStore.updateOffice({ address: this.form.address });
        }
        else
        {
          // CREATE
          await api.post('/offices', this.form);
          this.officeStore.addOffice(this.form);
          this.notify.success('Корпус создан');
        }
        this.closeModal();
      }
      catch (e)
      {
        const msg = e.response?.data?.detail || "Ошибка сохранения";
        this.notify.error(msg);
      }
    },

    async deleteOffice(office) {
      const confirmText = `ВНИМАНИЕ! Удаление корпуса №${office.id} приведет к удалению ВСЕХ аудиторий и оборудования в нём.\n\nПродолжить?`;

      if (!confirm(confirmText)) return;

      try {
        await api.delete(`/offices/${office.id}`);
        this.officeStore.removeOffice(office.id);
        this.notify.success('Корпус удален');
      } catch (e) {
        this.notify.error('Ошибка удаления.');
      }
    }
  },

  watch: {
    async "form.id"(newVal) {
      if (newVal)
      {
        await api.get(`/offices/${newVal}`).then(res => {
          this.officeAlreadyExists = true;
        }).catch(e => {
          this.officeAlreadyExists = false;
        })
      }
      else
      {
        this.officeAlreadyExists = false;
      }
    }
  },

  mounted() {
    this.fetchOffices();
  }
};

</script>

<template>
  <div class="card">
    <div class="card-header">
      <h2>Корпуса университета</h2>
      <button class="btn-primary" @click="openCreateModal">
        + Добавить корпус
      </button>
    </div>

    <div class="table-wrapper">
      <table class="data-table">
        <thead>
        <tr>
          <th>Номер</th>
          <th>Адрес</th>
          <th>Аудиторий</th>
          <th v-if="isSuperuser">Действия</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="office in offices" :key="office.id">
          <!-- Номер корпуса -->
          <td>
            <span class="office-number">№{{ office.id }}</span>
          </td>

          <!-- Адрес -->
          <td>
            <div class="address-cell">
              <span class="address-text">{{ office.address }}</span>
            </div>
          </td>

          <!-- Кол-во аудиторий -->
          <td>
              <span class="count-badge">
                {{ office.audiences ? office.audiences.length : 0 }}
              </span>
          </td>

          <!-- Действия -->
          <td v-if="isSuperuser">
            <div class="actions-group">
              <!-- Редактировать -->
              <button class="btn-icon edit" title="Изменить адрес" @click="openEditModal(office)">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
              </button>

              <!-- Удалить -->
              <button class="btn-icon delete" title="Удалить" @click="deleteOffice(office)">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
              </button>
            </div>
          </td>
        </tr>
        </tbody>
      </table>

      <div v-if="loading" class="loading-state">Загрузка списка корпусов...</div>
      <div v-else-if="offices.length === 0" class="empty-state">Нет данных</div>
    </div>

    <!-- МОДАЛКА СОЗДАНИЯ / РЕДАКТИРОВАНИЯ -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <h3>{{ isEditMode ? 'Изменить корпус' : 'Новый корпус' }}</h3>

        <form @submit.prevent="saveOffice">
          <!-- Номер (только при создании) -->
          <div class="form-group" v-if="!isEditMode">
            <label>Номер корпуса</label>
            <input
                type="number"
                v-model.number="form.id"
                class="form-input"
                required
                min="1"
                :class="{error: officeAlreadyExists}"
            >
            <p v-if="officeAlreadyExists">Корпус с таким номером уже существует</p>
          </div>

          <!-- Адрес -->
          <div class="form-group">
            <label>Адрес</label>
            <input type="text" v-model="form.address" class="form-input" required placeholder="Введите адрес корпуса">
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="closeModal">Отмена</button>
            <button type="submit" class="btn-primary">Сохранить</button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* Стили карточки и таблицы */
.card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.card-header h2 { font-size: 18px; color: #0f172a; margin: 0; }

.table-wrapper { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; min-width: 500px; }

.data-table th {
  text-align: left;
  padding: 12px 10px;
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  border-bottom: 1px solid #e2e8f0;
}

.data-table td {
  padding: 12px 10px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
  font-size: 14px;
  vertical-align: middle;
}

/* Элементы таблицы */
.office-number { font-weight: 600; color: #0f172a; }
.address-text { color: #64748b; }
.count-badge {
  background: #f1f5f9;
  color: #475569;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

/* Кнопки */
.btn-primary { background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; }
.btn-primary:hover { background: #2563eb; }

.btn-secondary { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; padding: 8px 16px; border-radius: 6px; cursor: pointer; }
.btn-secondary:hover { background: #e2e8f0; }

.actions-group { display: flex; gap: 8px; }
.btn-icon { background: none; border: none; cursor: pointer; padding: 5px; color: #94a3b8; transition: color 0.2s; }
.btn-icon:hover { color: #3b82f6; }
.btn-icon.delete:hover { color: #ef4444; }

.loading-state, .empty-state { padding: 20px; text-align: center; color: #94a3b8; }

/* МОДАЛЬНОЕ ОКНО (Простое) */
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex; justify-content: center; align-items: center;
  z-index: 100;
}
.modal-content {
  background: white; padding: 25px; border-radius: 12px; width: 400px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
}
.modal-content h3 { margin-top: 0; margin-bottom: 20px; font-size: 18px; }

.form-group {
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
}

.form-group p {
  color: #ec1616;
  font-size: 14px;
}

.form-input {
  padding: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
}

.form-input:focus {
  border-color: #3b82f6;
  outline: none;
}

.form-input.error {
  border-color: #ec1616;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 25px;
}
</style>
