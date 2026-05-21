<script>
import {toRaw} from "vue";

export default {
  name: "row",
  emits: ['openComputerModal',],
  props: {
    row: {
      type: Object,
      required: true
    },
  },
  data() {
    return {
      rowNumber: null,
      collapsed: false,
    }
  },
  methods: {
    toggleCollapsed() {
      this.collapsed = !this.collapsed;
    },
    openComputerModal(computer) {
      const currentComputer = toRaw(computer);
      this.$emit('openComputerModal', currentComputer);
    }
  },
  mounted() {
    this.rowNumber = this.row.name.slice(4)
  }
}
</script>

<template>
  <div class="row-container" :class="{collapsed: collapsed}">
    <div class="row-header">
      <div class="row-number">{{ rowNumber }}</div>
      <h2 class="row-title">Ряд {{ rowNumber }}</h2>
      <div class="collapse-icon" @click="toggleCollapsed">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path data-v-6feae890="" d="M6 9l6 6 6-6"></path>
        </svg>
      </div>
    </div>

    <div class="computers-grid">
      <div v-if="row" v-for="computer in row.computers" class="computer-card" :class="{broken: !computer.state}" @click="openComputerModal(computer)">
        <div class="computer-icon" :class="{broken: !computer.state}">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
          </svg>
        </div>
        <p class="computer-number">Компьютер №{{ Number(computer.name.split(`_`)[1]) }}</p>
        <p class="computer-status" :class="{broken: !computer.state}">{{ computer.state ? 'Исправен' : 'Неисправен' }}</p>
        <div class="status-dot" :class="{broken: !computer.state}"></div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.row-container {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  padding: 28px;
  opacity: 0;
  transform: translateY(30px);
  animation: fadeInUpRow 0.6s ease forwards;
}

.row-container:nth-child(1) {
  animation-delay: 0.1s;
}

.row-container:nth-child(2) {
  animation-delay: 0.2s;
}

.row-container:nth-child(3) {
  animation-delay: 0.3s;
}

.row-container:nth-child(4) {
  animation-delay: 0.4s;
}

.row-container:nth-child(5) {
  animation-delay: 0.5s;
}

.row-container:nth-child(6) {
  animation-delay: 0.6s;
}

.row-container:nth-child(7) {
  animation-delay: 0.7s;
}

@keyframes fadeInUpRow {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.row-container.collapsed .row-header
{
  margin-bottom: 0;
}

.row-container.collapsed .computers-grid
{
  display: none;
}

.row-container.collapsed .collapse-icon svg
{
  transform: rotate(-90deg);
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
  cursor: pointer;
}

.collapse-icon svg {
  width: 24px;
  height: 24px;
  transition: transform 0.3s ease;
}

.computers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.computer-card::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient( 45deg, transparent, rgba(255, 255, 255, 0.4), transparent );
  transform: rotate(45deg) translateX(-100%);
  transition: transform 0.6s ease;
}

.computer-card {
  background: linear-gradient(135deg, rgba(220, 252, 231, 0.9), rgba(187, 247, 208, 0.9));
  backdrop-filter: blur(10px);
  border: 2px solid rgba(134, 239, 172, 0.5);
  border-radius: 20px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  opacity: 0;
  transform: scale(0.8);
  animation: popIn 0.4s ease forwards;
  overflow: hidden;
}

@keyframes popIn {
  0% {
    opacity: 0;
    transform: scale(0.8) translateY(20px);
  }
  60% {
    transform: scale(1.05) translateY(-5px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.computer-card:nth-child(1) { animation-delay: 0.05s; }
.computer-card:nth-child(2) { animation-delay: 0.1s; }
.computer-card:nth-child(3) { animation-delay: 0.15s; }
.computer-card:nth-child(4) { animation-delay: 0.2s; }
.computer-card:nth-child(5) { animation-delay: 0.25s; }
.computer-card:nth-child(6) { animation-delay: 0.3s; }
.computer-card:nth-child(7) { animation-delay: 0.35s; }
.computer-card:nth-child(8) { animation-delay: 0.4s; }

.computer-card.broken {
  background: linear-gradient(135deg, rgba(254, 226, 226, 0.9), rgba(254, 202, 202, 0.9));
  border-color: #fca5a5;
}

.computer-card.broken:hover
{
  border-color: rgba(252, 165, 165, 0.8);
}

.computer-card:hover::before {
  transform: rotate(45deg) translateX(100%);
}

.computer-card:hover {
  transform: translateY(-12px) scale(1.03);
  box-shadow: 0 20px 40px rgba(0,0,0,0.15);
  border-color: rgba(134, 239, 172, 0.8);
}

.computer-card:hover .computer-icon {
  transform: scale(1.15);
  box-shadow: 0 12px 32px rgba(16, 185, 129, 0.4);
}

.computer-card.broken:hover .computer-icon
{
  box-shadow: 0 12px 32px rgba(239, 68, 68, 0.3);
}

.computer-icon {
  width: 76px;
  height: 76px;
  margin: 0 auto 18px;
  background: linear-gradient(135deg, #10b981, #059669);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3);
  position: relative;
  z-index: 1;
}

.computer-icon.broken {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  box-shadow: 0 8px 20px rgba(239, 68, 68, 0.3);
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

/* Responsive */
@media (max-width: 768px) {
  .computers-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
  }

  .computer-card:hover {
    transform: translateY(-4px) scale(1.02);
  }
}
</style>