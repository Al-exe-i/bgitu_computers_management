<script>
import api from "@/services/api";
import { useAuthStore } from "@/stores/auth";
import { useNotificationsStore } from "@/stores/notifications";
import { useOfficeStore } from "@/stores/offices"; // Убрали .js, так современнее

export default {
  name: "ManageOffices",

  data() {
    return {
      showModal: false,
      isEditMode: false,
      isSaving: false, // Защита от двойного клика при сохранении
      processingIds: [], // ID корпусов, которые прямо сейчас удаляются

      form: {
        id: null,
        address: ''
      }
    };
  },

  computed: {
    authStore() { return useAuthStore(); },
    officeStore() { return useOfficeStore(); },
    notify() { return useNotificationsStore(); },

    offices() { return this.officeStore.list || []; },
    loading() { return this.officeStore.loading; },
    isSuperuser() { return this.authStore.user?.is_superuser === true; },

    // Идеальный юзкейс для computed! Vue сам пересчитает это значение,
    // если изменится form.id или список offices. Никаких watch не нужно.
    officeAlreadyExists() {
      if (this.isEditMode || !this.form.id) return false;
      return this.offices.some(o => o.id === this.form.id);
    }
  },

  methods: {
    async fetchOffices() {
      await this.officeStore.fetchOffices();
    },

    openCreateModal() {
      this.isEditMode = false;
      this.form = { id: null, address: '' };
      this.showModal = true;
      this.addModalListeners();
    },

    openEditModal(office) {
      this.isEditMode = true;
      // Делаем копию данных, чтобы случайно не мутировать объект в таблице до сохранения
      this.form = { id: office.id, address: office.address };
      this.showModal = true;
      this.addModalListeners();
    },

    closeModal() {
      this.showModal = false;
      this.removeModalListeners();
    },

    addModalListeners() {
      document.addEventListener('keydown', this.handleEscape);
      document.body.style.overflow = 'hidden'; // Блокируем скролл фона
    },

    removeModalListeners() {
      document.removeEventListener('keydown', this.handleEscape);
      document.body.style.overflow = '';
    },

    handleEscape(e) {
      if (e.key === 'Escape') this.closeModal();
    },

    async saveOffice() {
      // Двойная защита на уровне логики
      if (this.officeAlreadyExists && !this.isEditMode) return;

      this.isSaving = true;
      try {
        if (this.isEditMode) {
          await api.patch(`/offices/${this.form.id}`, { address: this.form.address });
          this.officeStore.updateOffice({ id: this.form.id, address: this.form.address });
          this.notify.success(`Корпус №${this.form.id} успешно обновлен`);
        } else {
          await api.post('/offices', this.form);
          this.officeStore.addOffice(this.form);
          this.notify.success(`Корпус №${this.form.id} создан`);
        }
        this.closeModal();
      } catch (e) {
        const msg = e.response?.data?.detail || "Произошла ошибка при сохранении корпуса";
        this.notify.error(msg);
      } finally {
        this.isSaving = false;
      }
    },

    async deleteOffice(office) {
      const confirmText = `ВНИМАНИЕ!\nУдаление корпуса №${office.id} приведет к безвозвратному удалению ВСЕХ привязанных к нему аудиторий и оборудования.\n\nВы уверены, что хотите продолжить?`;
      if (!confirm(confirmText)) return;

      // Блокируем строку на время удаления
      this.processingIds.push(office.id);

      try {
        await api.delete(`/offices/${office.id}`);
        this.officeStore.removeOffice(office.id);
        this.notify.success(`Корпус №${office.id} успешно удален`);
      } catch (e) {
        this.notify.error(e.response?.data?.detail || 'Ошибка при удалении корпуса');
      } finally {
        // Разблокируем строку
        this.processingIds = this.processingIds.filter(id => id !== office.id);
      }
    }
  },

  mounted() {
    this.fetchOffices();
  },

  beforeUnmount() {
    this.removeModalListeners();
  }
};
</script>

<template>
  <div class="card">
    <!-- Шапка -->
    <div class="card-header">
      <div>
        <h2 class="section-title">Корпуса университета</h2>
        <p class="section-subtitle">Управление корпусами</p>
      </div>
      <button v-if="isSuperuser" class="btn btn-primary" @click="openCreateModal">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="4" y="2" width="16" height="20" rx="2" ry="2"></rect><path d="M9 22v-4h6v4"></path><path d="M8 6h.01"></path><path d="M16 6h.01"></path><path d="M12 6h.01"></path><path d="M12 10h.01"></path><path d="M12 14h.01"></path><path d="M16 10h.01"></path><path d="M16 14h.01"></path><path d="M8 10h.01"></path><path d="M8 14h.01"></path>
        </svg>
        Добавить
      </button>
    </div>

    <!-- Таблица -->
    <div class="table-wrapper">
      <table class="data-table">
        <thead>
        <tr>
          <th width="100">Номер</th>
          <th>Адрес здания</th>
          <th width="140">Аудиторий</th>
          <th v-if="isSuperuser" width="100" class="text-right">Действия</th>
        </tr>
        </thead>
        <tbody>
        <!-- Спиннер загрузки -->
        <tr v-if="loading">
          <td :colspan="isSuperuser ? 4 : 3" class="text-center py-8">
            <div class="spinner-large mx-auto"></div>
            <p class="text-muted mt-2">Загрузка списка корпусов...</p>
          </td>
        </tr>

        <!-- Пустое состояние -->
        <tr v-else-if="offices.length === 0">
          <td :colspan="isSuperuser ? 4 : 3" class="text-center py-8 empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"></rect><path d="M9 22v-4h6v4"></path></svg>
            <p class="text-muted mt-2">Корпуса пока не добавлены.</p>
          </td>
        </tr>

        <!-- Данные -->
        <tr v-else v-for="office in offices" :key="office.id" class="table-row">
          <td>
            <span class="office-number">{{ office.id }}</span>
          </td>

          <td>
            <div class="address-cell">
              <span class="address-text">{{ office.address }}</span>
            </div>
          </td>

          <td>
            <!-- Подсвечиваем серым, если аудиторий нет, и зеленым, если есть -->
            <span class="badge-count" :class="{ 'is-empty': !office.audiences_count }">
                {{ office.audiences_count || 0 }} шт.
              </span>
          </td>

          <td v-if="isSuperuser" class="text-right">
            <div class="actions-group">
              <button
                  class="action-btn edit"
                  title="Редактировать"
                  :disabled="processingIds.includes(office.id)"
                  @click="openEditModal(office)"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
              </button>

              <button
                  class="action-btn delete"
                  title="Удалить"
                  :disabled="processingIds.includes(office.id)"
                  @click="deleteOffice(office)"
              >
                <span v-if="processingIds.includes(office.id)" class="spinner-small text-danger"></span>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
              </button>
            </div>
          </td>
        </tr>
        </tbody>
      </table>
    </div>

    <!-- МОДАЛКА (с Vue анимацией) -->
    <transition name="modal">
      <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
        <div class="modal-content">

          <div class="modal-header">
            <h3>{{ isEditMode ? 'Редактирование корпуса' : 'Новый корпус' }}</h3>
            <button class="close-btn" @click="closeModal" title="Закрыть">✕</button>
          </div>

          <form @submit.prevent="saveOffice" class="modal-body">

            <!-- Показываем номер всегда. Но при редактировании блокируем его -->
            <div class="form-group">
              <label>Номер корпуса <span v-if="!isEditMode" class="required">*</span></label>
              <input
                  type="number"
                  v-model.number="form.id"
                  class="form-input"
                  :class="{ 'error': officeAlreadyExists, 'disabled': isEditMode }"
                  :disabled="isEditMode"
                  required
                  min="1"
                  placeholder="Например: 1"
              >
              <!-- Красивая подсказка об ошибке -->
              <span v-if="officeAlreadyExists" class="error-text">Корпус с таким номером уже существует</span>
              <span v-else-if="isEditMode" class="hint-text">Номер корпуса изменить нельзя</span>
            </div>

            <!-- Адрес -->
            <div class="form-group">
              <label>Адрес здания <span class="required">*</span></label>
              <input
                  type="text"
                  v-model="form.address"
                  class="form-input"
                  required
                  placeholder="г. Москва, ул. Пушкина, д. 1"
              >
            </div>

            <div class="modal-actions">
              <button type="button" class="btn btn-secondary" @click="closeModal" :disabled="isSaving">Отмена</button>
              <button type="submit" class="btn btn-primary" :disabled="officeAlreadyExists || isSaving">
                <span v-if="isSaving" class="spinner-small spinner-white"></span>
                {{ isSaving ? 'Сохранение...' : 'Сохранить' }}
              </button>
            </div>
          </form>

        </div>
      </div>
    </transition>

  </div>
</template>

<style scoped>
/* --- Базовая структура --- */
.card {
  background: #ffffff;
  padding: 24px;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
  font-family: system-ui, -apple-system, sans-serif;
  color: #0f172a;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.section-title {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
}

.section-subtitle {
  margin: 0;
  font-size: 14px;
  color: #64748b;
}

/* --- Утилиты --- */
.text-muted {
  color: #64748b;
}

.text-danger {
  color: #ef4444;
}

.text-right {
  text-align: right;
}

.text-center {
  text-align: center;
}

.py-8 {
  padding-top: 2rem !important;
  padding-bottom: 2rem !important;
}

.mx-auto {
  margin-left: auto;
  margin-right: auto;
}

.mt-2 {
  margin-top: 8px;
}

.required {
  color: #ef4444;
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
  min-width: 500px;
  text-align: left;
}

.data-table th {
  padding: 14px 16px;
  background: #f8fafc;
  color: #475569;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  border-bottom: 2px solid #e2e8f0;
}

.data-table td {
  padding: 14px 16px;
  border-bottom: 1px solid #e2e8f0;
  font-size: 14px;
  vertical-align: middle;
}

.table-row {
  transition: background-color 0.15s ease;
}

.table-row:hover {
  background-color: #f1f5f9;
}

.table-row:last-child td {
  border-bottom: none;
}

.office-number {
  font-weight: 700;
  color: #0f172a;
  background: #f1f5f9;
  padding: 4px 8px;
  border-radius: 6px;
  font-family: ui-monospace, monospace;
}

.address-text {
  color: #334155;
  font-weight: 500;
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

.badge-count.is-empty {
  background: #f1f5f9;
  color: #64748b;
  font-weight: 500;
}

/* --- Кнопки --- */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn svg {
  width: 18px;
  height: 18px;
}

.btn-primary {
  background: #0f172a;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #334155;
  transform: translateY(-1px);
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;
}

.btn-secondary:hover:not(:disabled) {
  background: #e2e8f0;
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

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
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #94a3b8;
  transition: all 0.2s ease;
}

.action-btn svg {
  width: 18px;
  height: 18px;
}

.action-btn.edit:hover:not(:disabled) {
  background: #eff6ff;
  color: #3b82f6;
}

.action-btn.delete:hover:not(:disabled) {
  background: #fee2e2;
  color: #ef4444;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* --- Модальное окно --- */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 440px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  color: #94a3b8;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: 0.2s;
}

.close-btn:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}

.form-input {
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

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.form-input.error {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15);
}

.form-input.disabled {
  background: #f8fafc;
  color: #94a3b8;
  cursor: not-allowed;
  border-color: #e2e8f0;
}

.error-text {
  font-size: 12px;
  color: #ef4444;
  margin-top: 2px;
}

.hint-text {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 2px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 28px;
}

/* --- Спиннеры и Пустое состояние --- */
.empty-state svg {
  width: 48px;
  height: 48px;
  color: #cbd5e1;
}

.spinner-large {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(59, 130, 246, 0.2);
  border-radius: 50%;
  border-top-color: #3b82f6;
  animation: spin 0.8s linear infinite;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(148, 163, 184, 0.3);
  border-radius: 50%;
  border-top-color: currentColor;
  animation: spin 0.8s linear infinite;
}

.spinner-white {
  border-color: rgba(255, 255, 255, 0.3);
  border-top-color: white;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* --- Анимации Vue --- */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-content {
  animation: modal-slide-in 0.3s ease-out;
}

.modal-leave-active .modal-content {
  animation: modal-slide-in 0.3s ease-out reverse;
}

@keyframes modal-slide-in {
  from {
    transform: translateY(20px) scale(0.95);
    opacity: 0;
  }
  to {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}

/* --- Адаптив --- */
@media (max-width: 480px) {
  .card-header {
    flex-direction: column;
    align-items: stretch;
  }

  .btn-primary {
    width: 100%;
  }
}
</style>
