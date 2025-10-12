<script>
export default {
  name: "mainDashboard"
}
</script>

<template>
  <div class="dashboard-container">
    <h1 class="dashboard-title">Статистика неисправностей</h1>

    <div class="stats-container">

      <div class="floor-stats">
        <div class="floor-title">
          <div class="floor-icon">
            <span class="floor-number">1</span>
          </div>
          <span>Первый этаж</span>
        </div>
        <div class="breakdowns-title">Количество поломок</div>
        <div id="floor1Breakdowns" class="breakdowns-count">0</div>
        <button id="viewFloor1Btn" class="view-details-btn">Просмотреть детали</button>
      </div>

      <div class="floor-stats">
        <div class="floor-title">
          <div class="floor-icon">
            <span class="floor-number">2</span>
          </div>
          <span>Второй этаж</span>
        </div>
        <div class="breakdowns-title">Количество поломок</div>
        <div id="floor1Breakdowns" class="breakdowns-count">0</div>
        <button id="viewFloor1Btn" class="view-details-btn">Просмотреть детали</button>
      </div>

    </div>
  </div>
</template>

<style scoped>
.dashboard-container {
  padding: 40px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: calc(100vh - 120px);
}

.dashboard-title {
  font-size: 32px;
  font-weight: 700;
  color: #1f2937;
  text-align: center;
  margin-bottom: 40px;
}

.stats-container {
  display: flex;
  gap: 30px;
  justify-content: center;
  flex-wrap: wrap;
  max-width: 800px;
}

.floor-stats
{
  background: white;
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.1);
  text-align: center;
  transition: all 0.3s ease;
  min-width: 290px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.floor-stats:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 35px rgba(0,0,0,0.15);
}

.floor-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.floor-icon {
  width: 40px;
  height: 40px;
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 10px;
}

.floor-number {
  font-size: 24px;
  font-weight: 700;
}

.breakdowns-title {
  font-size: 18px;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 10px;
}

.breakdowns-count {
  font-size: 48px;
  font-weight: 800;
  color: #10b981;
  margin-bottom: 15px;
}

.breakdowns-count.red
{
  color: #ef4444;
}

.view-details-btn {
  background: #3b82f6;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 16px;
  border: none;
  cursor: pointer;
  transition: background 0.3s ease;
  margin-top: 10px;
}

.view-details-btn:hover {
  background: #2563eb;
}

@media (max-width: 768px)
{
  .floor-stats
  {
    min-width: 250px;
  }

}
</style>