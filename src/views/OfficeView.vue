<script>
import FloorSection from "@/components/Common/FloorSection.vue";
import api from "@/services/api.js";
import router from "@/router/index.js";
import {useNotificationsStore} from "@/stores/notifications.js";
import {toRaw} from "vue";
import LoaderContainer from "@/components/Common/LoaderContainer.vue";

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
      filtered: false,
      proxyFloors: null,
    }
  },
  computed: {
    notify()
    {
      return useNotificationsStore()
    }
  },
  methods: {
    async getOffice(officeNumber)
    {
      await api.get(`/offices/${officeNumber}`).then((response) => {
        this.office = response.data;
        this.arrangeFloors(this.office.audiences)
        this.countTotalHardware()
        this.loading = false
        this.filtered = false
        this.filterMode = "all"
        if (this.office.audiences.length === 0)
        {
          this.notify.info("В этом корпусе нет аудиторий. Вы были перенаправлены на страницу добавления аудитории")
          router.push({name: "New Audience"})
        }
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
          // Если ищем исправные (true) все ПК должны быть true
          if (targetState === true)
          {
            return audience.rows.every(row =>
                row.computers.every(pc => pc.state === true)
            );
          }
          // Если ищем неисправные (false) хотя бы один ПК должен быть false
          else if (targetState === false)
          {
            return audience.rows.some(row =>
                row.computers.some(pc => pc.state === false)
            );
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
        this.filtered = false;
      }
      else if(this.filterMode === "working" || this.filterMode === "broken")
      {
        this.filtered = true;
        if(this.filterMode === "working")
        {
          this.proxyFloors = this.filterAudiencesByComputerState(this.floors, true)
        }
        else
        {
          this.proxyFloors = this.filterAudiencesByComputerState(this.floors, false)
        }
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

      <div class="stats-container">
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
        <input type="text" id="searchInput" placeholder="🔍 Поиск по номеру аудитории...">
      </div>
      <div class="filter-buttons">
        <button class="filter-btn" @click="setFilterMode(`all`)" :class="{active: this.filterMode === `all`}">Все аудитории</button>
        <button class="filter-btn" @click="setFilterMode(`working`)" :class="{active: this.filterMode === `working`}">Исправные</button>
        <button class="filter-btn" @click="setFilterMode(`broken`)" :class="{active: this.filterMode === `broken`}">С неисправностями</button>
      </div>
    </div>

    <floor-section v-if="!filtered" v-for="floor in floors" :audiences="floor.audiences" :number="floor.number"></floor-section>
    <floor-section v-if="filtered" v-for="floor in proxyFloors" :audiences="floor.audiences" :number="floor.number"></floor-section>



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