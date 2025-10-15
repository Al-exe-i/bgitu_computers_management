<script>
import FloorSection from "@/components/floor/floorSection.vue";

export default {
  name: "floor",
  components: {FloorSection},
  props: ["officeNumber"],
  data() {
    return {
      testFirstFloorAuds: [
        {number: 104, computersCount: 12, statusClass: "status-working"},
        {number: 105, computersCount: 15, statusClass: "status-working"},
        {number: 106, computersCount: 16, statusClass: "status-working"},
      ]
    }
  },
  computed: {

  }
}
</script>

<template>
  <h1 class="page-title">Схема расположения аудиторий</h1>

  <div class="building-container">
    <div class="building-info">
      <h2 class="building-title">Учебный корпус А</h2>
      <p class="building-description">В корпусе расположены компьютерные классы и лаборатории для практических занятий. Аудитории оборудованы современной техникой и мультимедийным оборудованием.</p>

      <div class="stats-container">
        <div class="stat-card">
          <div class="stat-value" id="totalClassrooms">12</div>
          <div class="stat-label">Всего аудиторий</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" id="totalComputers">153</div>
          <div class="stat-label">Всего компьютеров</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" id="workingComputers">143</div>
          <div class="stat-label">Исправных</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" id="brokenComputers">10</div>
          <div class="stat-label">Неисправных</div>
        </div>
      </div>
    </div>

    <div class="controls-panel">
      <div class="search-box">
        <input type="text" id="searchInput" placeholder="🔍 Поиск по номеру аудитории...">
      </div>
      <div class="filter-buttons">
        <button class="filter-btn active" data-filter="all">Все аудитории</button>
        <button class="filter-btn" data-filter="working">Исправные</button>
        <button class="filter-btn" data-filter="broken">С неисправностями</button>
      </div>
    </div>

    <floor-section :audiences="testFirstFloorAuds" number="1"></floor-section>

    <div class="floor-section" data-floor="2">
      <div class="floor-header">
        <div class="floor-number">2</div>
        <h2 class="floor-title">Второй этаж</h2>
        <div class="collapse-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M6 9l6 6 6-6"/>
          </svg>
        </div>
      </div>

      <div class="classrooms-content">
        <div class="classrooms-grid">
          <div class="classroom-card" data-status="working" data-number="201">
            <div class="classroom-number">201</div>
            <div class="classroom-info">
              <div class="info-item">
                <div class="info-label">Компьютеры</div>
                <div class="info-value computers-count working">16</div>
              </div>
              <div class="info-item">
                <div class="info-label">Статус</div>
                <div class="info-value">
                  <span class="status-indicator status-working"></span>
                  Исправны
                </div>
              </div>
            </div>
          </div>

          <div class="classroom-card" data-status="broken" data-number="202">
            <div class="classroom-number">202</div>
            <div class="classroom-info">
              <div class="info-item">
                <div class="info-label">Компьютеры</div>
                <div class="info-value computers-count">12</div>
              </div>
              <div class="info-item">
                <div class="info-label">Статус</div>
                <div class="info-value">
                  <span class="status-indicator status-broken"></span>
                  1 неисправен
                </div>
              </div>
            </div>
          </div>

          <div class="classroom-card" data-status="working" data-number="203">
            <div class="classroom-number">203</div>
            <div class="classroom-info">
              <div class="info-item">
                <div class="info-label">Компьютеры</div>
                <div class="info-value computers-count working">10</div>
              </div>
              <div class="info-item">
                <div class="info-label">Статус</div>
                <div class="info-value">
                  <span class="status-indicator status-working"></span>
                  Исправны
                </div>
              </div>
            </div>
          </div>

          <div class="classroom-card" data-status="working" data-number="204">
            <div class="classroom-number">204</div>
            <div class="classroom-info">
              <div class="info-item">
                <div class="info-label">Компьютеры</div>
                <div class="info-value computers-count working">8</div>
              </div>
              <div class="info-item">
                <div class="info-label">Статус</div>
                <div class="info-value">
                  <span class="status-indicator status-working"></span>
                  Исправны
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="floor-section" data-floor="3">
      <div class="floor-header">
        <div class="floor-number">3</div>
        <h2 class="floor-title">Третий этаж</h2>
        <div class="collapse-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M6 9l6 6 6-6"/>
          </svg>
        </div>
      </div>

      <div class="classrooms-content">
        <div class="classrooms-grid">
          <div class="classroom-card" data-status="working" data-number="301">
            <div class="classroom-number">301</div>
            <div class="classroom-info">
              <div class="info-item">
                <div class="info-label">Компьютеры</div>
                <div class="info-value computers-count working">20</div>
              </div>
              <div class="info-item">
                <div class="info-label">Статус</div>
                <div class="info-value">
                  <span class="status-indicator status-working"></span>
                  Исправны
                </div>
              </div>
            </div>
          </div>

          <div class="classroom-card" data-status="broken" data-number="302">
            <div class="classroom-number">302</div>
            <div class="classroom-info">
              <div class="info-item">
                <div class="info-label">Компьютеры</div>
                <div class="info-value computers-count">18</div>
              </div>
              <div class="info-item">
                <div class="info-label">Статус</div>
                <div class="info-value">
                  <span class="status-indicator status-broken"></span>
                  4 неисправны
                </div>
              </div>
            </div>
          </div>

          <div class="classroom-card" data-status="working" data-number="303">
            <div class="classroom-number">303</div>
            <div class="classroom-info">
              <div class="info-item">
                <div class="info-label">Компьютеры</div>
                <div class="info-value computers-count working">15</div>
              </div>
              <div class="info-item">
                <div class="info-label">Статус</div>
                <div class="info-value">
                  <span class="status-indicator status-working"></span>
                  Исправны
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

body {
  background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
  min-height: 100vh;
  padding: 20px;
}

.page-title {
  text-align: center;
  font-size: 32px;
  font-weight: 700;
  color: #1e40af;
  margin-bottom: 40px;
  text-shadow: 1px 1px 3px rgba(0,0,0,0.1);
}

.building-container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.building-info {
  background: white;
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  border: 2px solid #f0abfc;
}

.building-title {
  font-size: 24px;
  font-weight: 600;
  color: #7e22ce;
  margin-bottom: 20px;
  text-align: center;
}

.building-description {
  font-size: 16px;
  color: #4b5563;
  line-height: 1.6;
  text-align: center;
  max-width: 800px;
  margin: 0 auto 25px;
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 15px;
  margin-top: 25px;
}

.stat-card {
  background: linear-gradient(135deg, #f0f9ff, #dbeafe);
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  border: 2px solid #93c5fd;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #1e40af;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}

.controls-panel {
  background: white;
  border-radius: 20px;
  padding: 25px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  border: 2px solid #dbeafe;
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  align-items: center;
}

.search-box {
  flex: 1;
  min-width: 250px;
}

.search-box input {
  width: 100%;
  padding: 12px 20px;
  border: 2px solid #93c5fd;
  border-radius: 12px;
  font-size: 16px;
  transition: all 0.3s ease;
}

.search-box input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.filter-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-btn {
  padding: 10px 20px;
  border: 2px solid #93c5fd;
  background: white;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #1e40af;
}

.filter-btn:hover {
  background: #f0f9ff;
}

.filter-btn.active {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: white;
  border-color: #1d4ed8;
}

.floor-section
{
  background: white;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  border: 2px solid #dbeafe;
  overflow: hidden;
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
  flex-shrink: 0;
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

  .page-title {
    font-size: 28px;
  }

  .floor-header {
    flex-wrap: wrap;
  }

  .stats-container {
    grid-template-columns: repeat(2, 1fr);
  }

  .controls-panel {
    flex-direction: column;
  }

  .search-box {
    width: 100%;
  }

  .filter-buttons {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  body {
    padding: 15px;
  }

  .classroom-card {
    padding: 20px;
  }

  .classroom-number {
    font-size: 28px;
  }

  .info-value {
    font-size: 16px;
  }

  .stats-container {
    grid-template-columns: 1fr;
  }
}

/* Animation for initial load */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.floor-section {
  animation: fadeInUp 0.6s ease forwards;
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
</style>