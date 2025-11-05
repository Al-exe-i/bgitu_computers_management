<script>
import api from "@/services/api.js";
import {useAuthStore} from "@/stores/auth.js";
import RowSection from "@/components/Common/RowSection.vue";
import router from "@/router/index.js";
import {useAudienceContext} from "@/stores/officeCtx.js";

export default {
  name: "AudienceView",
  components: {Row: RowSection},
  props: ["audienceId", "officeId"],
  data() {
    return {
      audience: null,
      descriptionShown: false,
      descriptionEditModalShow: false,
      description: "",
      showStats: false,
      totalComputers: 0,
      faultyComputers: 0,
      selectedComputer: null,
      computerModalShow: false,
      floorNumber: null,
    }
  },
  methods: {
    async getAudience()
    {
      await api.get(`/audiences/${this.audienceId}`).then((response) => {
        this.audience = response.data;
        this.audienceContext.setOffice(this.audience.office_id)
        this.description = response.data.description;
        this.floorNumber = this.extractFloor(this.audience.id);
        this.getStats()
      }).catch((error) => {
        //show notification error
        router.push(`/`)
      })
    },
    async updateDescription()
    {
      if(this.authStore.isAuthenticated)
      {
        await api.patch(`/audiences/update/${this.audienceId}`, {"description": this.description}).then((response) => {
          this.descriptionEditModalShow = false;
        })
      }
    },
    getStats()
    {
      if(this.audience)
      {
        this.audience.rows.forEach((row) => {
          this.totalComputers += row.computers.length;
          row.computers.forEach((computer) => {
            if(!computer.state)
              this.faultyComputers++
          })
        })
      }
    },
    showHideDescription()
    {
      this.descriptionShown = !this.descriptionShown;
    },
    showHideDescriptionEditModal(shown)
    {
      this.descriptionEditModalShow = shown;
    },
    openComputerModal(computer)
    {
      if(this.authStore.isAuthenticated)
      {
        this.selectedComputer = {...computer};
        this.computerModalShow = true;
      }
    },
    extractComputerNumber(computerObj)
    {
      if(computerObj)
        return Number(computerObj.name.split("_")[1])
      else
        return '';
    },
    extractComputerRow(computerObj)
    {
      if(computerObj)
        return Number(computerObj.name.split("_")[0].slice(2));
      else
        return '';
    },
    extractFloor()
    {
      if (this.audience)
      {
        if(this.audience.id === 257)
          return 1
        else
          return Math.floor(this.audience.id / 100)
      }
    },
    async setComputerState(state)
    {
      if(this.selectedComputer)
      {
        let description = state === true ? null : this.selectedComputer.description
        await api.patch(
            `/computers/${this.selectedComputer.id}`, {"state": state, "description": description}).then((response) => {
          this.selectedComputer.state = state;
          let targetRow = this.audience.rows.find(row => row.id === this.selectedComputer.row_id)
          let targetComputer = targetRow.computers.find(computer => computer.id === this.selectedComputer.id)
          targetComputer.state = state
          targetComputer.description = description
          if(state === true)
            this.selectedComputer.description = null
        }).catch((error) => {
          //show error popup
        })
      }
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
    },
    audienceContext()
    {
      return useAudienceContext()
    }
  },
  beforeUnmount() {
    this.audienceContext.clear()
  }
}
</script>

<template>
  <div class="main-content">
    <div v-if="audience" class="container">
      <div class="page-header">
        <h2 id="floorTitle" class="audience-title">Аудитория №{{ audienceId }}</h2>
        <div class="stats-switcher-container">
          <label class="switch">
            <input type="checkbox" v-model="showStats">
            <span class="slider"></span>
          </label>
          <p class="floor-subtitle">Показывать статистику аудитории</p>
        </div>

      </div>

      <!-- Statistics -->
      <div class="stats-grid" v-show="showStats" v-if="audience">

        <div class="stat-card">
          <div class="stat-label">Всего компьютеров</div>
          <div class="stat-value">{{ totalComputers }}</div>
        </div>

        <div class="stat-card working">
          <div class="stat-label">Исправных</div>
          <div class="stat-value">{{ totalComputers - faultyComputers }}</div>
        </div>

        <div class="stat-card broken">
          <div class="stat-label">Неисправных</div>
          <div class="stat-value">{{ faultyComputers }}</div>
        </div>

      </div>

      <!-- Описание -->
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
            <p class="location-text">{{ description ? description : 'Описание отсутствует' }}</p>
          </div>
        </div>
      </div>

      <!-- Компьютеры -->
      <div v-if="audience" id="computerRows" class="computer-rows">
        <Row @open-computer-modal="openComputerModal" v-for="row in audience.rows" :row="row"></Row>
      </div>

      <div v-if="authStore.user" :class="{active: descriptionEditModalShow}" class="modal">
        <div class="modal-content">
          <h2 class="modal-title">Редактирование ориентиров</h2>
          <div class="form-group">
            <label for="locationTextarea" class="form-label">Описание расположения</label>
            <textarea v-model="description" class="form-textarea" placeholder="Опишите, относительно каких объектов расположены ряды..."></textarea>
          </div>
          <div class="modal-buttons">
            <button @click="updateDescription" class="modal-btn save-btn">Сохранить</button>
            <button @click="showHideDescriptionEditModal(false)" class="modal-btn cancel-btn">Отмена</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Модальное окно для управления компьютером -->
  <div v-if="selectedComputer" class="modal" :class="{active: computerModalShow}">
    <div class="modal-content">
      <h2 class="modal-title">Компьютер №{{ extractComputerNumber(selectedComputer) }} (Ряд {{ extractComputerRow(selectedComputer) }})</h2>
      <div id="currentStatus">
        <div
            class="status-badge"
            :class="{working: selectedComputer.state, broken: !selectedComputer.state}"
            v-if="selectedComputer">
            Текущий статус: {{ selectedComputer.state ? 'исправен' : 'неисправен' }}
        </div>
      </div>
      <div class="form-group">
        <label for="comment" class="form-label">Комментарий</label>
        <textarea v-model="selectedComputer.description" :disabled="!selectedComputer.state" class="form-textarea" placeholder="Опишите проблему или состояние компьютера..."></textarea>
      </div>
      <div class="action-btns">
        <button :disabled="selectedComputer.state" @click="setComputerState(true)" class="action-btn fix-btn">Исправен</button>
        <button :disabled="!selectedComputer.state" @click="setComputerState(false)" class="action-btn break-btn">Неисправен</button>
      </div>
      <button @click="computerModalShow = false; selectedComputer = null" class="close-btn">Закрыть</button>
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

.audience-title {
  font-size: 32px;
  font-weight: 800;
  color: #1e40af;
  margin-bottom: 12px;
  animation: leftToRightAppear .7s ease-in-out;
}

@keyframes leftToRightAppear {
  0%
  {
    opacity: 0;
    transform: translateX(-10vw);
  }
  100%
  {
    opacity: 1;
    transform: translateX(0);
  }
}

.floor-subtitle {
  font-size: 1.3rem;
  color: #6b7280;
}

/* Stats Cards */
.stats-switcher-container
{
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  animation: rightToLeftAppear .7s ease-in-out;
}

@keyframes rightToLeftAppear {
  0%
  {
    opacity: 0;
    transform: translateX(10vw);
  }
  100%
  {
    opacity: 1;
    transform: translateX(0);
  }
}

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
  animation: fadeIn .6s ease-in-out;
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
  animation: fadeIn .7s ease-in-out;
}

@keyframes fadeIn {
  0%
  {
    opacity: 0;
  }
  100%
  {
    opacity: 1;
  }
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

.form-textarea {
  width: 100%;
  padding: 14px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 16px;
  transition: all 0.3s ease;
  font-family: inherit;
}

.form-textarea:focus {
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
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 16px 28px;
  border-radius: 100px;
  font-weight: 700;
  font-size: 16px;
  margin-bottom: 28px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.status-badge.working {
  background: linear-gradient(135deg, #d1fae5, #a7f3d0);
  color: #065f46;
  border: 2px solid #6ee7b7;
}

.status-badge.broken {
  background: linear-gradient(135deg, #fee2e2, #fecaca);
  color: #991b1b;
  border: 2px solid #fca5a5;
}

.action-btns {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.action-btn {
  flex: 1;
  padding: 18px;
  border-radius: 16px;
  font-weight: 800;
  font-size: 16px;
  border: none;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.fix-btn {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.4);
}

.fix-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(34, 197, 94, 0.4);
}

.fix-btn:disabled {
  background: linear-gradient(135deg, #d1d5db, #9ca3af);
  cursor: not-allowed;
  opacity: 0.6;
  transform: none;
  box-shadow: none;
}

.break-btn {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
  box-shadow: 0 8px 24px rgba(239, 68, 68, 0.4);
}

.break-btn:hover:not(:disabled) {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(239, 68, 68, 0.5);
}

.break-btn:disabled {
  background: linear-gradient(135deg, #d1d5db, #9ca3af);
  cursor: not-allowed;
  opacity: 0.6;
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

.switch {
  font-size: 17px;
  position: relative;
  display: inline-block;
  width: 3.5em;
  height: 2em;

  input:checked + .slider {
    background-color: #007bff;
    border: 1px solid #007bff;
  }

  input:focus + .slider {
    box-shadow: 0 0 1px #007bff;
  }

  input:checked + .slider:before {
    transform: translateX(1.4em);
    background-color: #fff;
  }
}

/* Hide default HTML checkbox */
.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

/* The slider */
.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #fff;
  border: 1px solid #adb5bd;
  transition: .4s;
  border-radius: 30px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 1.4em;
  width: 1.4em;
  border-radius: 20px;
  left: 0.27em;
  bottom: 0.25em;
  background-color: #adb5bd;
  transition: .4s;
}

/* Responsive */
@media (max-width: 768px) {
  body {
    padding: 0;
  }

  .main-content {
    padding: 24px 12px;
  }

  .audience-title {
    font-size: 26px;
  }

  .modal-content {
    padding: 24px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .floor-subtitle
  {
    font-size: 1rem;
  }

  .switch {
    font-size: 14px; /* Slightly smaller base size */
    width: 3.2em;
    height: 1.8em;
  }

  .slider {
    border-radius: 28px;
  }

  .slider:before {
    height: 1.25em;
    width: 1.25em;
    left: 0.25em;
    bottom: 0.23em;
  }

  .switch input:checked + .slider:before {
    transform: translateX(1.2em);
  }
}
</style>