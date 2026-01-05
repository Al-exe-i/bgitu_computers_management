<script>
import FloorSection from "@/components/Common/FloorSection.vue";
import api from "@/services/api.js";
import router from "@/router/index.js";
import {useNotificationsStore} from "@/stores/notifications.js";
import {toRaw} from "vue";
import LoaderContainer from "@/components/Common/LoaderContainer.vue";
import {useAuthStore} from "@/stores/auth.js";

export default {
  name: "floor",
  components: {LoaderContainer, FloorSection},
  props: ["officeNumber"],
  data() {
    return {
      totalHardware: 0,
      brokenHardware: 0,
      office: null,
      floors: null,
      loading: true,
      filterMode: "all",
      proxyFloors: null,
      searchField: ``,
    }
  },

  computed: {
    notify()
    {
      return useNotificationsStore()
    },

    authStore() {
      return useAuthStore()
    }
  },
  methods: {
    async getOffice(officeNumber)
    {
      await api.get(`/offices/${officeNumber}`).then((response) => {
        this.office = response.data;
        this.arrangeFloors(this.office.audiences)
        this.proxyFloors = this.floors
        this.countTotalHardware()
        this.loading = false
        this.filterMode = "all"
      }).catch(error => {
        router.push({ path: `/` })
        if (error.response.status === 404)
          this.notify.warning("Вы пытаетесь открыть несуществующий корпус")
        else
          this.notify.error("Не удалось загрузить данные")
      })
    },
    countTotalHardware()
    {
      let totalHardware = 0;
      let totalBroken = 0;
      this.office.audiences.forEach((audience) => {
        let audienceTotalHardware = audience.hardware.length;
        let audienceBrokenHardware = 0;
        totalHardware += audienceTotalHardware;
        audience.hardware.forEach((hardware) => {
          if(!hardware.state)
            audienceBrokenHardware++
        })
        totalBroken += audienceBrokenHardware;
        audience.totalHardware = audienceTotalHardware;
        audience.brokenHardware = audienceBrokenHardware;
      })

      this.totalHardware = totalHardware
      this.brokenHardware = totalBroken
    },
    arrangeFloors(audiences)
    {
      this.floors = {}
      audiences.forEach((item) => {
        if(this.floors[item.floor] === undefined)
          this.floors[item.floor] = {number: item.floor, audiences: []}
        this.floors[item.floor].audiences.push(item)
      })
    },
    filterAudiencesByComputerState(data, targetState)
    {
      const result = {};

      Object.keys(structuredClone(toRaw(data))).forEach(floorKey => {
        const office = data[floorKey];

        const validAudiences = office.audiences.filter(audience => {
          // Если ищем исправные (true) все должны быть true
          if (targetState === true)
          {
            return audience.hardware.every(hw => hw.state === true);
          }
          // Если ищем неисправные (false) хотя бы один должен быть false
          else if (targetState === false)
          {
            return audience.hardware.some(hw => hw.state === false);
          }
          return false;
        });

        // Сохраняем этаж, только если остались подходящие аудитории
        if (validAudiences.length > 0)
        {
          result[floorKey] = {
            ...office,
            audiences: validAudiences
          };
        }
      });

      return result;
    },

    setFilterMode(filterMode)
    {
      this.filterMode = filterMode;
    },

    addNewAudience()
    {
      router.push({name: "New Audience"})
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
    },

    filterMode(newFilterMode)
    {
      if(newFilterMode === "all")
      {
        this.proxyFloors = this.floors;
      }
      else if(this.filterMode === "working" || this.filterMode === "broken")
      {
        if(this.filterMode === "working")
        {
          this.proxyFloors = this.filterAudiencesByComputerState(this.floors, true)
        }
        else
        {
          this.proxyFloors = this.filterAudiencesByComputerState(this.floors, false)
        }
      }
    },

    searchField(newVal)
    {
      if(newVal === undefined || newVal === "")
      {
        this.filterMode = "all"
        this.proxyFloors = this.floors;
      }
      else
      {
        const result = {}
        Object.keys(this.proxyFloors).forEach(floorKey => {
          const office = this.proxyFloors[floorKey];

          const validAudiences = office.audiences.filter(audience => {
            return String(audience.id).startsWith(newVal)
          });

          // Сохраняем этаж, только если остались подходящие аудитории
          if (validAudiences.length > 0)
          {
            result[floorKey] = {
              ...office,
              audiences: validAudiences
            };
          }
        });

        this.proxyFloors = result
      }
    }
  }
}
</script>

<template>
  <h1 class="page-title">Список аудиторий</h1>

  <LoaderContainer v-if="loading"/>

  <div class="building-container">
    <div v-if="!loading" class="building-info">
      <h2 class="building-title">Учебный корпус №{{ office.id }}</h2>
      <p class="building-description">Расположен по адресу: {{ office.address }}</p>

      <div v-if="this.authStore.isAuthenticated" class="stats-container">
        <div class="stat-card">
          <div class="stat-value">{{ office.audiences.length }}</div>
          <div class="stat-label">Всего аудиторий</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ totalHardware }}</div>
          <div class="stat-label">Всего оборудования</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ totalHardware - brokenHardware }}</div>
          <div class="stat-label">Исправно</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ this.brokenHardware }}</div>
          <div class="stat-label">Неисправно</div>
        </div>
      </div>
    </div>

    <div v-if="!loading" class="controls-panel">
      <div class="search-box">
        <input v-model="searchField" type="text" id="searchInput" placeholder="🔍 Поиск по номеру аудитории...">
      </div>
      <div class="filter-buttons">
        <button class="filter-btn" @click="setFilterMode(`all`)" :class="{active: this.filterMode === `all`}">Все аудитории</button>
        <button class="filter-btn" @click="setFilterMode(`working`)" :class="{active: this.filterMode === `working`}">Исправные</button>
        <button class="filter-btn" @click="setFilterMode(`broken`)" :class="{active: this.filterMode === `broken`}">С неисправностями</button>
      </div>
    </div>

    <floor-section v-if="floors" v-for="floor in proxyFloors" :audiences="floor.audiences" :number="floor.number"></floor-section>

    <div v-if="!loading && Object.keys(floors).length === 0" class="empty-state">
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z"></path>
      </svg>
      <div class="empty-state-title">Аудиторий пока нет</div>
      <div v-if="authStore.isAuthenticated && authStore?.user?.role === 1" class="empty-state-text">Добавьте первую аудиторию для этого корпуса</div>
      <button v-if="authStore.isAuthenticated && authStore?.user?.role === 1" @click="addNewAudience" class="empty-state-btn">
        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"></path>
        </svg>
        Добавить аудиторию
      </button>
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

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 40px;
  background: rgba(249, 250, 251, 0.8);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 2px dashed #cbd5e1;
}

.empty-state svg {
  width: 80px;
  height: 80px;
  color: #cbd5e1;
  margin: 0 auto 20px;
  display: block;
}

.empty-state-title {
  font-size: 20px;
  font-weight: 700;
  color: #64748b;
  margin-bottom: 8px;
}

.empty-state-text {
  font-size: 15px;
  color: #94a3b8;
  margin-bottom: 24px;
}

.empty-state-btn {
  padding: 12px 28px;
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.empty-state-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

.empty-state-btn svg {
  width: 18px;
  height: 18px;
  margin: 0;
  display: inline;
}


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
  body
  {
    padding: 15px;
  }

}

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