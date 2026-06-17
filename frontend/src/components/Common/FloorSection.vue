<script>
import router from "@/router/index.js";
import {useAudienceContext} from "@/stores/officeCtx.js";
import {useAuthStore} from "@/stores/auth.js";

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
    displayMode: {
      type: String,
      default: "cards",
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
        case 5:
          return "Пятый"
        case 6:
          return "Шестой"
        case 7:
          return "Седьмой"
        case 8:
          return "Восьмой"
        case 9:
          return "Девятый"
        case 10:
          return "Десятый"
      }
    },
    handleAudienceClick(audiencePublicId, officeId)
    {
      router.push({
        name: "Audience",
        params: {audiencePublicId: audiencePublicId},
      })
      this.audienceContext.setOffice(officeId)
    },
    getAudienceNumber(audience)
    {
      return audience?.number ?? audience?.id
    },
    audienceStatus(faultyCnt)
    {
      if(faultyCnt === 0)
        return `Всё исправно`
      else
        return `${faultyCnt} неисправно`
    }
  },
  computed: {
    audienceContext()
    {
      return useAudienceContext()
    },

    isAuthenticated()
    {
      return useAuthStore().isAuthenticated
    },

    isCompactMode() {
      return this.displayMode === "compact";
    }
  }
}
</script>

<template>
  <div class="floor-section" :class="{collapsed: this.collapsed}">
    <div class="floor-header" @click="this.collapsed = !this.collapsed">
      <div class="floor-number">{{ this.number }}</div>
      <div class="floor-heading">
        <h2 class="floor-title">{{ this.numberToLiteral(this.number) }} этаж</h2>
      </div>
      <div class="collapse-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M6 9l6 6 6-6"/>
        </svg>
      </div>
    </div>

    <div class="classrooms-content">

      <div class="classrooms-grid" :class="{ 'compact-mode': isCompactMode }">

        <div
          v-for="audience in audiences"
          class="classroom-card"
          :class="{ 'compact-mode': isCompactMode }"
          @click="handleAudienceClick(audience.public_id, audience.office_id)"
        >
          <template v-if="isCompactMode">
            <div class="classroom-number compact-chip">{{ getAudienceNumber(audience) }}</div>

            <div class="classroom-row-copy">
              <div class="classroom-row-title">Аудитория {{ getAudienceNumber(audience) }}</div>
              <div class="classroom-row-meta" v-if="isAuthenticated">
                <span class="classroom-quick-stat">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="4" width="18" height="5" rx="1.5"></rect>
                    <rect x="3" y="10" width="18" height="5" rx="1.5"></rect>
                    <rect x="3" y="16" width="18" height="5" rx="1.5"></rect>
                  </svg>
                  {{ audience.totalHardware }} ед.
                </span>
                <span class="classroom-status-badge" :class="{'status-broken': audience.brokenHardware > 0, 'status-working': audience.brokenHardware === 0}">
                  <span class="status-indicator" :class="{'status-broken': audience.brokenHardware > 0, 'status-working': audience.brokenHardware === 0}"></span>
                  {{ audienceStatus(audience.brokenHardware) }}
                </span>
              </div>
            </div>

            <span class="classroom-row-arrow" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14"></path>
                <path d="m12 5 7 7-7 7"></path>
              </svg>
            </span>
          </template>

          <template v-else>
            <div class="classroom-number">{{ getAudienceNumber(audience) }}</div>
            <div class="classroom-info" v-if="isAuthenticated">
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
          </template>
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
  animation: floorSectionReveal 0.66s cubic-bezier(0.16, 1, 0.3, 1) both;
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

.floor-heading {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.floor-subtitle {
  font-size: 14px;
  color: #64748b;
  font-weight: 600;
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

.classrooms-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 25px;
  padding-top: 1rem;
}

.classrooms-grid.compact-mode {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 0.35rem;
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

.classroom-card.compact-mode {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  text-align: left;
  border-width: 1px;
  border-color: #bfdbfe;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
}

.classroom-card.compact-mode:hover {
  transform: translateX(4px);
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.1);
}

.classroom-number {
  font-size: 36px;
  font-weight: 700;
  color: #1e40af;
  margin-bottom: 15px;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}

.classroom-card.compact-mode .classroom-number {
  margin-bottom: 0;
  text-shadow: none;
}

.compact-chip {
  min-width: 74px;
  min-height: 50px;
  padding: 8px 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: linear-gradient(145deg, #eff6ff, #dbeafe);
  border: 1px solid rgba(147, 197, 253, 0.9);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.classroom-row-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.classroom-row-title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.classroom-row-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.classroom-quick-stat,
.classroom-status-badge {
  min-height: 26px;
  padding: 3px 8px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
}

.classroom-quick-stat {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  color: #475569;
}

.classroom-quick-stat svg {
  width: 13px;
  height: 13px;
  color: #2563eb;
  flex-shrink: 0;
}

.classroom-status-badge {
  border: 1px solid transparent;
}

.classroom-status-badge .status-indicator {
  width: 8px;
  height: 8px;
  margin-right: 0;
}

.classroom-status-badge.status-working {
  background: rgba(220, 252, 231, 0.9);
  border-color: rgba(134, 239, 172, 0.85);
  color: #166534;
}

.classroom-status-badge.status-broken {
  background: rgba(254, 226, 226, 0.92);
  border-color: rgba(252, 165, 165, 0.88);
  color: #b91c1c;
}

.classroom-row-arrow {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: #f8fafc;
  color: #2563eb;
  border: 1px solid #dbeafe;
  flex-shrink: 0;
}

.classroom-row-arrow svg {
  width: 16px;
  height: 16px;
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

@media (max-width: 1024px) {
  .info-value {
    font-size: 15px;
  }
}

/* Responsive design */
@media (max-width: 768px) {
  .classrooms-grid {
    grid-template-columns: 1fr;
  }

  .classrooms-grid.compact-mode {
    gap: 8px;
  }

  .classroom-card.compact-mode {
    grid-template-columns: auto minmax(0, 1fr);
    gap: 10px;
    padding: 10px 11px;
  }

  .classroom-row-arrow {
    display: none;
  }

  .floor-header {
    flex-wrap: wrap;
  }

  .info-value {
    font-size: 15px;
  }
}

@media (max-width: 480px) {
  .classroom-card {
    padding: 20px;
  }

  .classroom-card.compact-mode {
    grid-template-columns: 58px minmax(0, 1fr);
    align-items: center;
    gap: 9px;
    padding: 9px 10px;
  }

  .compact-chip {
    min-width: 0;
    width: 58px;
    min-height: 36px;
    padding: 4px 8px;
    border-radius: 12px;
  }

  .classroom-row-meta {
    flex-direction: row;
    align-items: center;
    gap: 4px 8px;
  }

  .classroom-quick-stat,
  .classroom-status-badge {
    justify-content: flex-start;
    min-height: 20px;
    padding: 0;
    border: none;
    background: transparent;
    font-size: 11px;
    border-radius: 0;
  }

  .classroom-row-title {
    font-size: 14px;
  }

  .classroom-number {
    font-size: 22px;
  }

  .info-value {
    font-size: 14px;
  }

  .classroom-quick-stat svg {
    display: none;
  }

  .classroom-status-badge .status-indicator {
    width: 7px;
    height: 7px;
  }
}

@keyframes floorSectionReveal {
  from {
    opacity: 0;
    transform: translateY(28px) scale(0.985);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .floor-section {
    animation: none !important;
  }
}

</style>
