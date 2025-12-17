<script>
import {useAuthStore} from "@/stores/auth.js";
import router from "@/router/index.js";
import {useAudienceContext} from "@/stores/officeCtx.js";

export default {
  name: "floorSection",
  props: {
    number: {
      type: Number,
      required: true
    },
    audiences: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      collapsed: false,
    }
  },
  methods: {
    numberToLiteral(number)
    {
      number = Number(number);
      switch (number) {
        case 1:
          return "Первый"
        case 2:
          return "Второй"
        case 3:
          return "Третий"
        case 4:
          return "Четвёртый"
      }
    },
    handleAudienceClick(audienceId, officeId)
    {
      router.push({
        name: "Audience",
        params: {audienceId: audienceId},
      })
      this.audienceContext.setOffice(officeId)
    },
    audienceStatus(faultyCnt)
    {
      if(faultyCnt === 0)
        return `Всё исправно`
      else
        return `${faultyCnt} неисправно`
    },
    addNewAudience() {
      router.push({name: "New Audience"})
    }
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
  }
}
</script>

<template>
  <div class="floor-section" :class="{collapsed: this.collapsed}">
    <div class="floor-header">
      <div class="floor-number">{{ this.number }}</div>
      <h2 class="floor-title">{{ this.numberToLiteral(this.number) }} этаж</h2>
      <div @click="this.collapsed = !this.collapsed" class="collapse-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M6 9l6 6 6-6"/>
        </svg>
      </div>
    </div>
    <button v-if="authStore.isAuthenticated && authStore?.user.role < 2" class="add-classroom-btn" @click="addNewAudience()">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 5v14M5 12h14"></path>
      </svg>
      Добавить аудиторию
    </button>

    <div class="classrooms-content">

      <div class="classrooms-grid">

        <div v-for="audience in audiences" class="classroom-card" @click="handleAudienceClick(audience.id, audience.office_id)">
          <div class="classroom-number">{{ audience.id }}</div>
          <div class="classroom-info">
            <div class="info-item">
              <div class="info-label">Оборудование</div>
              <div class="info-value computers-count">{{ audience.totalHardware }}</div>
            </div>
            <div class="info-item">
              <div class="info-label">Статус</div>
              <div class="info-value">
                <span class="status-indicator" :class="{'status-broken': audience.brokenHardware > 0, 'status-working': audience.brokenHardware === 0}"></span>
                {{ audienceStatus(audience.brokenHardware) }}
              </div>
            </div>
          </div>
        </div>

      </div>

    </div>

  </div>
</template>

<style scoped>
.floor-section
{
  background: white;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  border: 2px solid #dbeafe;
  overflow: hidden;
}

.floor-section:nth-child(2) {
  animation-delay: 0.1s;
}

.floor-section:nth-child(3) {
  animation-delay: 0.2s;
}

.floor-section:nth-child(4) {
  animation-delay: 0.3s;
}

.floor-header {
  display: flex;
  align-items: center;
  padding: 30px;
  cursor: pointer;
  transition: all 0.3s ease;
  user-select: none;
}

.floor-header:hover {
  background: #f8fafc;
}

.floor-number {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 700;
  margin-right: 20px;
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
  position: relative;
}

.floor-number::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  padding: 2px;
  background: linear-gradient(135deg, #275fe2, #3f85f6);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0.3;
}

.floor-title {
  font-size: 28px;
  font-weight: 600;
  color: #1e3a8a;
  flex: 1;
}

.collapse-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f1f5f9;
  transition: all 0.3s ease;
}

.collapse-icon svg {
  width: 24px;
  height: 24px;
  transition: transform 0.3s ease;
}

.add-classroom-btn {
  margin: 0 30px 20px;
  padding: 15px 30px;
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
}

.add-classroom-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(16, 185, 129, 0.3);
}

.add-classroom-btn svg {
  width: 20px;
  height: 20px;
}

.floor-section.collapsed .collapse-icon svg {
  transform: rotate(-90deg);
}

.classrooms-content {
  max-height: 2000px;
  overflow: hidden;
  transition: max-height 0.5s ease, padding 0.5s ease, opacity 0.3s ease;
  padding: 0 30px 30px;
  opacity: 1;
}

.floor-section.collapsed .classrooms-content {
  max-height: 0;
  padding: 0 30px;
  opacity: 0;
}

.floor-section.collapsed .add-classroom-btn
{
  display: none;
}

.classrooms-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 25px;
  padding-top: 1rem;
}

.classroom-card {
  background: white;
  border-radius: 16px;
  padding: 25px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 3px solid #93c5fd;
  position: relative;
  overflow: hidden;
}

.classroom-card.hidden {
  display: none;
}

.classroom-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 15px 35px rgba(0,0,0,0.15);
  border-color: #3b82f6;
}

.classroom-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
}

.classroom-number {
  font-size: 36px;
  font-weight: 700;
  color: #1e40af;
  margin-bottom: 15px;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}

.classroom-info {
  display: flex;
  justify-content: space-around;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e2e8f0;
}

.info-item {
  text-align: center;
}

.info-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
  margin-bottom: 5px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-size: 18px;
  font-weight: 600;
  color: #1e40af;
}

.computers-count.working {
  color: #059669;
}

.computers-count.broken {
  color: #dc2626;
}

.status-indicator {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 8px;
}

.status-working {
  background: #10b981;
}

.status-broken {
  background: #ef4444;
}

/* Responsive design */
@media (max-width: 768px) {
  .classrooms-grid {
    grid-template-columns: 1fr;
  }

  .floor-header {
    flex-wrap: wrap;
  }

  .add-classroom-btn
  {
    margin: 0 auto;
    padding: 10px 3rem;
  }
}

@media (max-width: 480px) {
  .classroom-card {
    padding: 20px;
  }

  .classroom-number {
    font-size: 28px;
  }

  .info-value {
    font-size: 16px;
  }
}


</style>