<script>
import FloorSection from "@/components/floor/floorSection.vue";
import api from "@/services/api.js";

export default {
  name: "floor",
  components: {FloorSection},
  props: ["officeNumber"],
  data() {
    return {
      totalComputers: 0,
      faultyComputers: 0,
      office: null,
      floors: null,
      testFirstFloorAuds: [
        {number: 104, computersCount: 12, statusClass: "status-working"},
        {number: 105, computersCount: 15, statusClass: "status-broken"},
        {number: 106, computersCount: 16, statusClass: "status-working"},
      ],
      testSecondFloorAuds: [
        {number: 204, computersCount: 11, statusClass: "status-working"},
        {number: 205, computersCount: 9, statusClass: "status-working"},
        {number: 206, computersCount: 10, statusClass: "status-working"},
      ]
    }
  },
  computed: {

  },
  methods: {
    async getOffice(officeNumber)
    {
      let response = await api.get(`/offices/${officeNumber}`).then();
      this.office = response.data
      this.countTotalComputers(this.office.audiences)
      this.arrangeFloors(this.office.audiences)
    },
    arrangeFloors(audiences)
    {
      this.floors = {}
      audiences.forEach((item) => {
        let audFloor = Math.floor(item.id / 100)
        if(this.floors[audFloor] === undefined)
        {
          this.floors[audFloor] = {number: audFloor, audiences: []}
        }
        this.floors[audFloor].audiences.push(item)
      })
    },
    countTotalComputers(audiences)
    {
      this.totalComputers = this.faultyComputers = 0
      audiences.forEach((audience) =>
      {
        let currentTotal = 0;
        let currentFaulty = 0;
        audience.rows.forEach((row) =>
        {
          row.computers.forEach((computer) =>
          {
            if(!computer.state)
            {
              this.faultyComputers++
              currentFaulty++;
            }
          })
          this.totalComputers += row.computers.length;
          currentTotal += row.computers.length;
        })
        audience.computersCount = currentTotal;
        audience.faultyComputers = currentFaulty;
      })
    }
  },
  mounted()
  {
    this.getOffice(this.officeNumber)
  },
  watch: {
    officeNumber(newOfficeNumber)
    {
      this.getOffice(newOfficeNumber)
    }
  }
}
</script>

<template>
  <h1 class="page-title">Схема расположения аудиторий</h1>

  <div class="building-container">
    <div v-if="office" class="building-info">
      <h2 class="building-title">Учебный корпус №{{ office.id }}</h2>
      <p class="building-description">Расположен по адресу: {{ office.address }}</p>

      <div class="stats-container">
        <div class="stat-card">
          <div class="stat-value" id="totalClassrooms">{{ office.audiences.length }}</div>
          <div class="stat-label">Всего аудиторий</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" id="totalComputers">{{ totalComputers }}</div>
          <div class="stat-label">Всего компьютеров</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" id="workingComputers">{{ totalComputers - faultyComputers }}</div>
          <div class="stat-label">Исправных</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" id="brokenComputers">{{ this.faultyComputers }}</div>
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

    <floor-section v-for="floor in floors" :audiences="floor.audiences" :number="floor.number"></floor-section>



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


/* Responsive design */
@media (max-width: 768px) {
  .page-title {
    font-size: 28px;
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
</style>