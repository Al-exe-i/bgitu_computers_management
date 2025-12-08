<script>
import router from "@/router/index.js";
import api from "@/services/api.js";
import {useNotificationsStore} from "@/stores/notifications.js";
import {toRaw} from "vue";

export default {
  name: "CreateInlineAudience",
  data() {
    return {
      rowsCount: 3,
      rowValues: [
        {count: 4, brokenIDs: new Set()},
        {count: 4, brokenIDs: new Set()},
        {count: 4, brokenIDs: new Set()},
      ],
      makeAllRowsSamePressed: false,
      audienceID: null,
      availableForCreationNumbers: null,
      selectedOffice: 1
    }
  },
  methods: {
    router() {
      return router
    },
    makeAllRowsSame(n)
    {
      if(this.makeAllRowsSamePressed)
        return
      this.rowValues.fill(n)
      this.rowValues = this.rowValues.map(obj => {
        return {count: n, brokenIDs: new Set(obj.brokenIDs)}
      })
      this.makeAllRowsSamePressed = true
      setTimeout(()=>{
        this.makeAllRowsSamePressed = false
      }, 1500)
    },
    changeComputerState(rowN, compN)
    {
      if(this.rowValues[rowN].brokenIDs.has(compN))
        this.rowValues[rowN].brokenIDs.delete(compN)
      else
        this.rowValues[rowN].brokenIDs.add(compN)
    },
    resetParams()
    {
      this.rowsCount = 3
      this.rowValues.forEach(row => {
        if(row.brokenIDs.size > 0)
          row.brokenIDs.clear()
      })
    },
    onOfficeChange()
    {
      this.audienceID = this.availableForCreationNumbers[this.selectedOffice][0]
    },
    async sendData()
    {
      let data = {}
      data.id = this.audienceID
      data.type = 0
      data.rows = []
      data.office_id = Number(this.selectedOffice)
      for (let i = 0; i < this.rowValues.length; i++)
      {
        const row_name = `row_${i + 1}`
        data.rows.push(
            {
              name: row_name,
              computers_count: this.rowValues[i].count,
              broken_ids: this.rowValues[i].brokenIDs.size > 0 ? [...toRaw(this.rowValues[i].brokenIDs)] : [],
            }
        )
      }
      await api.post(`/audiences/`, data).then(response => {
        router.push({
          name: "Audience",
          params: {audienceId: data.id}
        })
        this.notify.success("Аудитория создана!")
      }).catch(error => {
        this.notify.error("Не удалось создать аудиторию!")
      })
    }
  },
  async mounted() {
    await api.get(`/audiences/get_available_for_creation/`).then(response => {
      this.availableForCreationNumbers = response.data;
      this.audienceID = this.availableForCreationNumbers[this.selectedOffice][0]
    }).catch(error => {
      this.notify.error(`Не удалось получить доступные для создания аудитории`)
    })
  },
  computed: {
    notify()
    {
      return useNotificationsStore()
    },
    generatedPCs()
    {
      return this.rowValues
          .map(el => {
            const num = Number(el.count);
            return (num >= 1 && num <= 10) ? num : 0;
          })
          .filter(count => count > 0);
    },
    totalComputers()
    {
      let count = 0;
      this.rowValues.forEach(obj => {
        count += obj.count;
      })
      return count;
    },
    totalFaulty()
    {
      let count = 0;
      this.rowValues.forEach(obj => {
        count += obj.brokenIDs.size;
      })
      return count;
    }
  },
  watch: {
    rowsCount: {
      handler(newCount, oldCount)
      {
        const diff = newCount - oldCount;
        if (diff > 0)
        {
          // Добавляем недостающие элементы
          for (let i = 0; i < diff; i++)
          {
            this.rowValues.push({count: 4, brokenIDs: new Set()});
          }
        }
        else if (diff < 0)
        {
          // Удаляем лишние
          this.rowValues.splice(newCount); // оставляем только первые newCount
        }
      },
      immediate: true,
      flush: `pre`
    }
  }
}
</script>

<template>
  <div class="container">
    <div class="header">
      <button @click="router().go(-1)" class="back-btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        Назад к схеме
      </button>
      <h1 class="page-title">Добавление новой аудитории</h1>
      <div style="width: 180px;"></div>
    </div>

    <div class="main-content">
      <!-- Форма слева -->
      <div class="form-panel">
        <h2 class="form-title">Параметры аудитории</h2>

        <div class="form-group">
          <label class="form-label">Номер аудитории</label>
          <select
              v-if="availableForCreationNumbers"
              class="form-select"
              v-model="audienceID"
              required
          >
            <option v-for="(n, i) in availableForCreationNumbers[selectedOffice]" :value="n" :key="i">
              {{ n }}
            </option>
          </select>
          <p class="help-text">Выберите номер аудитории</p>
        </div>

        <div class="form-group">
          <label class="form-label">Корпус</label>
          <select v-if="availableForCreationNumbers" @change="onOfficeChange" class="form-select" v-model="selectedOffice">
            <option v-for="n in Object.keys(availableForCreationNumbers)" :value="n">{{ n }}</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Количество рядов</label>
          <input v-model="rowsCount" type="number" class="form-input" min="1" max="10" required>
          <p class="help-text">От 1 до 10 рядов компьютеров</p>
        </div>

        <div class="rows-container">
          <div v-for="i in rowsCount" :key="i" class="row-input-group">
            <span class="row-label">Ряд {{ i }}:</span>
            <input type="number" v-model.number="rowValues[i - 1].count" class="row-input" min="1" max="10" value="4" placeholder="Кол-во ПК">
            <button
                v-if="i === 1 && rowsCount > 1"
                @click="makeAllRowsSame(rowValues[i - 1].count)"
                class="copy-to-all-btn" :class="{pressed: makeAllRowsSamePressed}">
              <svg v-if="!makeAllRowsSamePressed" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2"></rect>
                <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 6L9 17l-5-5"/>
              </svg>
              {{ !makeAllRowsSamePressed ? `Ко всем` : `Применено!` }}
            </button>
          </div>
        </div>

        <div class="summary-box">
          <div class="summary-title">Сводка</div>
          <div class="summary-item">
            <span class="summary-label">Всего компьютеров:</span>
            <span class="summary-value">{{ this.totalComputers }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Исправных:</span>
            <span class="summary-value">{{ this.totalComputers - this.totalFaulty }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Неисправных:</span>
            <span class="summary-value">{{ this.totalFaulty }}</span>
          </div>
        </div>

        <div class="action-buttons">
          <button @click="resetParams" class="btn btn-secondary">Сбросить</button>
          <button @click="sendData" class="btn btn-primary">Сохранить</button>
        </div>
      </div>

      <!-- Предпросмотр справа -->
      <div class="preview-panel">
        <h2 class="preview-title">Предпросмотр расстановки</h2>
        <p class="preview-subtitle">Нажмите на компьютер, чтобы отметить его как неисправный</p>

        <div class="classroom-preview">
          <div v-for="rowN in rowsCount" class="classroom-row">
            <div
                @click="changeComputerState(rowN - 1, compN)"
                v-for="compN in generatedPCs[rowN - 1]"
                class="computer-item"
                :class="{broken: rowValues[rowN - 1]?.brokenIDs?.has(compN)}">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="3" width="20" height="14" rx="2"></rect>
                <path d="M8 21h8M12 17v4"></path>
              </svg>
              <span class="computer-number">{{ compN }}</span>
            </div>
          </div>
          <div v-if="rowValues.length < 1" class="classroom-empty">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="3" width="20" height="14" rx="2"/>
              <path d="M8 21h8M12 17v4"/>
            </svg>
            <div class="classroom-empty-text">Настройте параметры для предпросмотра</div>
          </div>
        </div>

        <div class="legend">
          <div class="legend-item">
            <div class="legend-color working"></div>
            <div class="legend-text">Исправный</div>
          </div>
          <div class="legend-item">
            <div class="legend-color broken"></div>
            <div class="legend-text">Неисправный</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.container {
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 40px;
  margin-top: 1rem;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  background: white;
  border: 2px solid #3b82f6;
  border-radius: 12px;
  color: #3b82f6;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: #3b82f6;
  color: white;
  transform: translateX(-5px);
}

.back-btn svg {
  width: 20px;
  height: 20px;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: #1e40af;
  text-shadow: 1px 1px 3px rgba(0,0,0,0.1);
}

.main-content {
  display: grid;
  grid-template-columns: 450px 1fr;
  gap: 30px;
  align-items: start;
}

.form-panel {
  background: white;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  border: 2px solid #dbeafe;
  position: sticky;
  top: 20px;
}

.form-title {
  font-size: 24px;
  font-weight: 600;
  color: #1e3a8a;
  margin-bottom: 30px;
  text-align: center;
}

.form-group {
  margin-bottom: 25px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 14px 18px;
  border: 2px solid #d1d5db;
  border-radius: 12px;
  font-size: 16px;
  transition: all 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-select {
  width: 100%;
  border: 2px solid #d1d5db;
  border-radius: 12px;
  font-size: 16px;
  transition: all 0.3s ease;
  background-color: white;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 20px;
  padding: 14px 45px 14px 18px;
}

.form-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-select:hover {
  border-color: #9ca3af;
}

.form-select option {
  padding: 10px;
  font-size: 16px;
  background-color: white;
  color: #111827;
}

.form-select option:hover,
.form-select option:checked {
  background-color: #eff6ff;
  color: #3b82f6;
}

.rows-container {
  margin-top: 20px;
}

.row-input-group {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
  padding: 15px;
  background: #f8fafc;
  border-radius: 12px;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.row-label {
  font-weight: 600;
  color: #64748b;
  min-width: 60px;
}

.row-input {
  flex: 1;
  padding: 10px 14px;
  border: 2px solid #cbd5e1;
  border-radius: 8px;
  font-size: 15px;
}

.row-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.copy-to-all-btn {
  padding: 10px 16px;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.copy-to-all-btn.pressed
{
  background: linear-gradient(135deg, #10b981, #059669);
}

.copy-to-all-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4);
}

.copy-to-all-btn svg {
  width: 16px;
  height: 16px;
}

.summary-box {
  background: linear-gradient(135deg, #f0f9ff, #dbeafe);
  padding: 20px;
  border-radius: 12px;
  margin: 25px 0;
  border: 2px solid #93c5fd;
}

.summary-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e40af;
  margin-bottom: 12px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 14px;
}

.summary-label {
  color: #64748b;
}

.summary-value {
  font-weight: 700;
  color: #1e40af;
}

.help-text {
  font-size: 13px;
  color: #64748b;
  margin-top: 8px;
  line-height: 1.5;
}

.action-buttons {
  display: flex;
  gap: 15px;
  margin-top: 30px;
}

.btn {
  flex: 1;
  padding: 14px 24px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(16, 185, 129, 0.3);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.btn-secondary {
  background: #f1f5f9;
  color: #64748b;
}

.btn-secondary:hover {
  background: #e2e8f0;
}

.preview-panel {
  background: white;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  border: 2px solid #dbeafe;
  min-height: 600px;
}

.preview-title {
  font-size: 24px;
  font-weight: 600;
  color: #1e3a8a;
  margin-bottom: 20px;
  text-align: center;
}

.preview-subtitle {
  text-align: center;
  color: #64748b;
  margin-bottom: 30px;
  font-size: 14px;
}

.classroom-preview {
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  border: 3px dashed #cbd5e1;
  border-radius: 16px;
  padding: 40px;
  min-height: 400px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.classroom-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #94a3b8;
}

.classroom-empty svg {
  width: 80px;
  height: 80px;
  margin-bottom: 20px;
  opacity: 0.5;
}

.classroom-empty-text {
  font-size: 18px;
  font-weight: 500;
}

.classroom-row {
  display: flex;
  gap: 15px;
  justify-content: center;
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.computer-item {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #10b981, #059669);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
  position: relative;
}

.computer-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
}

.computer-item.broken {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
}

.computer-item.broken:hover {
  box-shadow: 0 8px 20px rgba(239, 68, 68, 0.4);
}

.computer-item svg {
  width: 32px;
  height: 32px;
  color: white;
}

.computer-number {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #1e40af;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  border: 2px solid white;
}

.legend {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin-top: 30px;
  padding-top: 30px;
  border-top: 2px solid #e2e8f0;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.legend-color {
  width: 30px;
  height: 30px;
  border-radius: 8px;
}

.legend-color.working {
  background: linear-gradient(135deg, #10b981, #059669);
}

.legend-color.broken {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}

.legend-text {
  font-size: 14px;
  color: #4b5563;
  font-weight: 500;
}

@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }

  .form-panel {
    position: static;
  }

  .computer-item {
    width: 50px;
    height: 50px;
  }

  .computer-item svg {
    width: 26px;
    height: 26px;
  }
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }

  .computer-item {
    width: 40px;
    height: 40px;
  }

  .computer-item svg {
    width: 20px;
    height: 20px;
  }

  .classroom-row {
    gap: 10px;
  }
}
</style>