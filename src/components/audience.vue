<script>
import api from "@/services/api.js";
import {useAuthStore} from "@/stores/auth.js";

export default {
  name: "audience",
  props: ["audienceId"],
  data() {
    return {
      audience: null,
      descriptionShown: false,
      descriptionEditModalShow: false,
    }
  },
  methods: {
    async getAudience()
    {
      await api.get(`/audiences/${this.audienceId}`).then((response) => {
        this.audience = response.data;
      })
    },
    showHideDescription()
    {
      this.descriptionShown = !this.descriptionShown;
    },
    showHideDescriptionEditModal(shown)
    {
      this.descriptionEditModalShow = shown;
    }
  },
  mounted()
  {
    this.getAudience();
  },
  computed: {
    authStore()
    {
      return useAuthStore()
    }
  }
}
</script>

<template>
  <div class="main-content">
    <div v-if="audience" class="container">
      <div class="page-header">
        <h2 id="floorTitle" class="floor-title">Аудитория №{{ audienceId }}</h2>
        <p class="floor-subtitle">Управление и мониторинг компьютерных классов</p>
      </div>

      <!-- Statistics -->
      <div class="stats-grid">

        <div class="stat-card">
          <div class="stat-label">Всего компьютеров</div>
          <div class="stat-value">24</div>
        </div>

        <div class="stat-card working">
          <div class="stat-label">Исправных</div>
          <div class="stat-value">21</div>
        </div>

        <div class="stat-card broken">
          <div class="stat-label">Неисправных</div>
          <div class="stat-value">3</div>
        </div>

      </div>

      <!-- Ориентиры расположения -->
      <div class="collapsible-section">
        <div class="collapsible-header">
          <h3 class="collapsible-title">Ориентиры расположения рядов</h3>
          <div class="collapsible-actions">
            <button v-if="authStore.user" class="edit-btn">
              <svg @click="showHideDescriptionEditModal(true)" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
              </svg>
            </button>
            <svg @click="this.showHideDescription" class="expand-icon" :class="{expanded: descriptionShown}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>
          </div>
        </div>
        <div class="collapsible-content" :class="{expanded: descriptionShown}">
          <div class="location-info">
            <p class="location-text">{{ audience.description ? audience.description : 'Описание отсутствует' }}</p>
          </div>
        </div>
      </div>

      <!-- Компьютеры -->
      <div id="computerRows" class="computer-rows">

      </div>

      <div v-if="authStore.user" :class="{active: descriptionEditModalShow}" class="modal">
        <div class="modal-content">
          <h2 class="modal-title">Редактирование ориентиров</h2>
          <div class="form-group">
            <label for="locationTextarea" class="form-label">Описание расположения</label>
            <textarea class="form-textarea" placeholder="Опишите, относительно каких объектов расположены ряды..."></textarea>
          </div>
          <div class="modal-buttons">
            <button class="modal-btn save-btn">Сохранить</button>
            <button @click="showHideDescriptionEditModal(false)" class="modal-btn cancel-btn">Отмена</button>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* Main Content */
.main-content {
  padding: 40px 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.floor-title {
  font-size: 32px;
  font-weight: 800;
  color: #1f2937;
  margin-bottom: 12px;
}

.floor-subtitle {
  font-size: 16px;
  color: #6b7280;
}

/* Stats Cards */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0,0,0,0.12);
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 36px;
  font-weight: 800;
  color: #1f2937;
}

.stat-card.working .stat-value {
  color: #10b981;
}

.stat-card.broken .stat-value {
  color: #ef4444;
}

/* Collapsible Sections */
.collapsible-section {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  margin-bottom: 24px;
  overflow: hidden;
}

.collapsible-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  cursor: pointer;
  transition: background 0.2s ease;
  user-select: none;
}

.collapsible-header:hover {
  background: #f9fafb;
}

.collapsible-title {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.collapsible-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.edit-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f3f4f6;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.edit-btn:hover {
  background: #3b82f6;
  transform: scale(1.1);
}

.edit-btn:hover svg {
  color: white;
}

.edit-btn svg {
  width: 20px;
  height: 20px;
  color: #4b5563;
  transition: color 0.2s ease;
}

.expand-icon {
  width: 24px;
  height: 24px;
  color: #6b7280;
  transition: transform 0.3s ease;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.collapsible-content {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  transition: all 0.3s ease;
  border-top: 1px solid #e5e7eb;
}

.collapsible-content.expanded {
  max-height: 600px;
  opacity: 1;
  padding: 24px;
}

.location-info {
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  padding: 20px;
  background: #f8fafc;
}

.location-text {
  font-size: 16px;
  color: #4b5563;
  line-height: 1.8;
}

/* Computer Rows */
.computer-rows {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.row-container {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  padding: 28px;
}

.row-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.row-number {
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 800;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.row-title {
  font-size: 26px;
  font-weight: 700;
  color: #1f2937;
}

.computers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 20px;
}

.computer-card {
  background: linear-gradient(135deg, #dcfce7, #bbf7d0);
  border: 3px solid #86efac;
  border-radius: 16px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.computer-card.broken {
  background: linear-gradient(135deg, #fee2e2, #fecaca);
  border-color: #fca5a5;
}

.computer-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 12px 30px rgba(0,0,0,0.15);
}

.computer-icon {
  width: 70px;
  height: 70px;
  margin: 0 auto 16px;
  background: #22c55e;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.computer-card:hover .computer-icon {
  transform: scale(1.1) rotate(5deg);
}

.computer-icon.broken {
  background: #ef4444;
}

.computer-icon svg {
  width: 36px;
  height: 36px;
  color: white;
}

.computer-number {
  font-size: 17px;
  font-weight: 700;
  margin-bottom: 8px;
  color: #1f2937;
}

.computer-status {
  font-size: 14px;
  font-weight: 600;
  color: #16a34a;
}

.computer-status.broken {
  color: #dc2626;
}

.status-dot {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(34, 197, 94, 0.1);
  }
}

.status-dot.broken {
  background: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2);
}

/* Modals */
.modal {
  display: none;
  position: fixed;
  z-index: 1000;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0,0,0,0.6);
  align-items: center;
  justify-content: center;
  padding: 20px;
  backdrop-filter: blur(4px);
}

.modal.active {
  display: flex;
}

.modal-content {
  background: white;
  border-radius: 20px;
  padding: 32px;
  width: 100%;
  max-width: 540px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  animation: modalAppear 0.3s ease;
}

@keyframes modalAppear {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.modal-title {
  font-size: 26px;
  font-weight: 800;
  color: #1f2937;
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #374151;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-input, .form-textarea {
  width: 100%;
  padding: 14px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 16px;
  transition: all 0.3s ease;
  font-family: inherit;
}

.form-input:focus, .form-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
}

.form-textarea {
  min-height: 120px;
  resize: vertical;
}

.modal-buttons {
  display: flex;
  gap: 12px;
  margin-top: 28px;
}

.modal-btn {
  flex: 1;
  padding: 14px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 16px;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.save-btn {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.save-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.cancel-btn {
  background: #f3f4f6;
  color: #4b5563;
}

.cancel-btn:hover {
  background: #e5e7eb;
}

.status-badge {
  display: inline-block;
  padding: 10px 20px;
  border-radius: 100px;
  font-weight: 700;
  font-size: 15px;
  margin-bottom: 20px;
}

.status-badge.working {
  background: #dcfce7;
  color: #16a34a;
}

.status-badge.broken {
  background: #fee2e2;
  color: #dc2626;
}

.action-btns {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.action-btn {
  flex: 1;
  padding: 14px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 16px;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.fix-btn {
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: white;
  box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
}

.fix-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(34, 197, 94, 0.4);
}

.fix-btn:disabled {
  background: #d1d5db;
  cursor: not-allowed;
  opacity: 0.5;
  transform: none;
  box-shadow: none;
}

.break-btn {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.break-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
}

.break-btn:disabled {
  background: #d1d5db;
  cursor: not-allowed;
  opacity: 0.5;
  transform: none;
  box-shadow: none;
}

.close-btn {
  width: 100%;
  background: #f3f4f6;
  color: #4b5563;
  padding: 14px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 16px;
  border: none;
  cursor: pointer;
  margin-top: 16px;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: #e5e7eb;
}

/* Responsive */
@media (max-width: 768px) {
  body {
    padding: 0;
  }

  .header-container {
    flex-wrap: wrap;
    padding: 12px 16px;
  }

  .logo-container {
    order: 1;
    flex: 1;
  }

  .auth-container {
    order: 2;
  }

  .floor-switch {
    order: 3;
    width: 100%;
    justify-content: center;
    margin-top: 12px;
  }

  .main-content {
    padding: 24px 12px;
  }

  .floor-title {
    font-size: 26px;
  }

  .computers-grid {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 12px;
  }

  .modal-content {
    padding: 24px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
}
</style>