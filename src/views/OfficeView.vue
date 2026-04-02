<script>
import FloorSection from "@/components/Common/FloorSection.vue";
import api from "@/services/api.js";
import router from "@/router/index.js";
import {useNotificationsStore} from "@/stores/notifications.js";
import LoaderContainer from "@/components/Common/LoaderContainer.vue";
import {useAuthStore} from "@/stores/auth.js";
import {useThemeStore} from "@/stores/theme.js";

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
    },

    themeStore() {
      return useThemeStore()
    },

    audiencesCount() {
      return this.office?.audiences?.length ?? 0
    },

    floorCount() {
      return this.floors ? Object.keys(this.floors).length : 0
    },

    workingHardwareCount() {
      return Math.max(this.totalHardware - this.brokenHardware, 0)
    },

    hardwareHealthPercent() {
      if (!this.totalHardware) return 0
      return Math.round((this.workingHardwareCount / this.totalHardware) * 100)
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

    applyFilters() {
      if (!this.floors) return;

      const result = {};
      const searchText = this.searchField.toLowerCase().trim();

      // Проходим по каждому этажу из ИСХОДНЫХ данных (this.floors)
      Object.keys(this.floors).forEach(floorKey => {
        const originalFloor = this.floors[floorKey];

        // Фильтруем аудитории на этаже
        const validAudiences = originalFloor.audiences.filter(audience => {

          // 1. Проверка по состоянию (Filter Mode)
          let matchesState = true;
          if (this.filterMode === 'working') {
            // Исправные: все компьютеры должны быть true
            // (или если техники нет вообще - считаем исправной)
            matchesState = audience.hardware.every(hw => hw.state === true);
          } else if (this.filterMode === 'broken') {
            // Неисправные: хотя бы один комп false
            matchesState = audience.hardware.some(hw => hw.state === false);
          }

          // 2. Проверка по поиску (Search Field)
          let matchesSearch = true;
          if (searchText) {
            matchesSearch = String(audience.id).toLowerCase().startsWith(searchText);
          }

          // Аудитория должна пройти ОБЕ проверки
          return matchesState && matchesSearch;
        });

        // Если на этаже остались аудитории после фильтрации, добавляем его в результат
        if (validAudiences.length > 0) {
          result[floorKey] = {
            ...originalFloor,
            audiences: validAudiences
          };
        }
      });

      this.proxyFloors = result;
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

    filterMode()
    {
      this.applyFilters();
    },

    searchField()
    {
      this.applyFilters();
    }
  }
}
</script>

<template>
  <h1 class="page-title">Список аудиторий</h1>

  <LoaderContainer v-if="loading"/>

  <div class="building-container">
    <div v-if="!loading" class="building-info" :class="{ 'is-dark': themeStore.isDark }">
      <div class="building-hero">
        <div class="building-identity">
          <div class="building-symbol" aria-hidden="true">
            <div class="building-symbol-backdrop"></div>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 21h18"></path>
              <path d="M6 21V7l6-4l6 4v14"></path>
              <path d="M9 10h.01M9 13h.01M9 16h.01M15 10h.01M15 13h.01M15 16h.01"></path>
              <path d="M11 21v-4h2v4"></path>
            </svg>
            <span class="building-symbol-number">{{ office.id }}</span>
          </div>

          <div class="building-copy">
            <h2 class="building-title">Учебный корпус №{{ office.id }}</h2>

            <div class="building-description">
              <span class="building-description-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 21s-6-5.2-6-11a6 6 0 1 1 12 0c0 5.8-6 11-6 11"></path>
                  <circle cx="12" cy="10" r="2.4"></circle>
                </svg>
              </span>
              <span>{{ office.address }}</span>
            </div>

            <div class="building-pills">
              <div class="building-pill">
                <svg xmlns="http://www.w3.org/2000/svg" width="1536" height="1536" viewBox="0 0 1536 1536"><path fill="currentColor" d="M33 431q-18-9-25.5-19.5T0 383t7.5-28.5T33 335L670 17q39-19 98-17q59-2 98 17l637 318q18 9 25.5 19.5t7.5 28.5t-7.5 28.5T1503 431L866 749q-39 19-98 17q-59 2-98-17zm0 770q-18-9-25.5-19.5T0 1153t7.5-28.5T33 1105l160-80l477 238q40 19 98 16q58 3 98-16l477-238l160 80q18 9 25.5 19.5t7.5 28.5t-7.5 28.5t-25.5 19.5l-637 318q-40 19-98 16q-58 3-98-16zm0-384q-18-9-25.5-19.5T0 769t7.5-28.5T33 721l160-80l477 238q40 19 98 16q58 3 98-16l477-238l160 80q18 9 25.5 19.5t7.5 28.5t-7.5 28.5T1503 817l-637 318q-40 19-98 16q-58 3-98-16z"/></svg>
                <span>Этажей: {{ floorCount }}</span>
              </div>

            </div>
          </div>
        </div>

        <div v-if="authStore.isAuthenticated" class="building-spotlight">
          <span class="building-spotlight-label">Состояние оборудования</span>
          <div class="building-spotlight-main">
            <strong>{{ workingHardwareCount }}</strong>
            <span>/ {{ totalHardware }}</span>
          </div>
          <p class="building-spotlight-text">единиц оборудования исправны сейчас</p>
          <div class="building-spotlight-track" aria-hidden="true">
            <span class="building-spotlight-fill" :style="{ width: `${hardwareHealthPercent}%` }"></span>
          </div>
          <span class="building-spotlight-footnote">{{ hardwareHealthPercent }}% работоспособности</span>
        </div>
      </div>

      <div v-if="this.authStore.isAuthenticated" class="stats-container">
        <div class="stat-card">
          <span class="stat-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="2048" height="2048" viewBox="0 0 2048 2048"><path fill="currentColor" d="M1664 0v2048H384V0zm-128 128H512v1792h1024zm-192 1024q-26 0-45-19t-19-45t19-45t45-19t45 19t19 45t-19 45t-45 19"/></svg>
          </span>
          <div class="stat-copy">
            <div class="stat-label">Всего аудиторий</div>
            <div class="stat-value">{{ audiencesCount }}</div>
          </div>
        </div>

        <div class="stat-card">
          <span class="stat-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M9 18H4v-8h5zm6 0h-5V6h5zm6 0h-5V2h5zm1 4H3v-2h19z"/></svg>
          </span>
          <div class="stat-copy">
            <div class="stat-label">Всего оборудования</div>
            <div class="stat-value">{{ totalHardware }}</div>
          </div>
        </div>

        <div class="stat-card stat-card-success">
          <span class="stat-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="8"></circle>
              <path d="m8.8 12.3 2.2 2.2 4.3-4.6"></path>
            </svg>
          </span>
          <div class="stat-copy">
            <div class="stat-label">Исправно</div>
            <div class="stat-value">{{ workingHardwareCount }}</div>
          </div>
        </div>

        <div class="stat-card stat-card-danger">
          <span class="stat-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 10.5v3.75m-9.303 3.376C1.83 19.126 2.914 21 4.645 21h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 4.88c-.866-1.501-3.032-1.501-3.898 0L2.697 17.626ZM12 17.25h.007v.008H12v-.008Z"/></svg>
          </span>
          <div class="stat-copy">
            <div class="stat-label">Неисправно</div>
            <div class="stat-value">{{ this.brokenHardware }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!loading && office.audiences.length > 0" class="controls-panel">
      <div class="search-box">
        <span class="search-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="7"></circle>
            <path stroke-linecap="round" d="m20 20-3.5-3.5"></path>
          </svg>
        </span>
        <input v-model="searchField" type="text" id="searchInput" placeholder="Поиск по номеру аудитории...">
      </div>
      <div class="filter-buttons" :class="{ 'is-dark': themeStore.isDark }">
        <button class="filter-btn" @click="setFilterMode(`all`)" :class="{active: this.filterMode === `all`}">Все аудитории</button>
        <button class="filter-btn" @click="setFilterMode(`working`)" :class="{active: this.filterMode === `working`}">Исправные</button>
        <button class="filter-btn" @click="setFilterMode(`broken`)" :class="{active: this.filterMode === `broken`}">С неисправностями</button>
      </div>
    </div>

    <floor-section v-if="floors" v-for="floor in proxyFloors" :audiences="floor.audiences" :number="floor.number"></floor-section>

    <div
      v-if="!loading && office?.audiences?.length > 0 && proxyFloors && Object.keys(proxyFloors).length === 0"
      class="empty-state filtered-empty-state"
    >
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3.75h16.5m-16.5 0v16.5m16.5-16.5v16.5M8.25 8.25h7.5m-7.5 4.5h7.5m-7.5 4.5h4.5"></path>
      </svg>
      <div class="empty-state-title">По выбранным фильтрам аудитории не найдены</div>
      <div class="empty-state-text">Измените параметры поиска или выберите другой фильтр</div>
    </div>

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
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at top right, rgba(56, 189, 248, 0.16), transparent 34%),
    radial-gradient(circle at left bottom, rgba(37, 99, 235, 0.12), transparent 32%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.98));
  border-radius: 28px;
  padding: 32px;
  border: 1px solid rgba(191, 219, 254, 0.85);
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
}

.building-info::before,
.building-info::after {
  content: "";
  position: absolute;
  border-radius: 999px;
  pointer-events: none;
}

.building-info::before {
  width: 240px;
  height: 240px;
  right: -110px;
  top: -120px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.16), transparent 68%);
}

.building-info::after {
  width: 220px;
  height: 220px;
  left: -90px;
  bottom: -120px;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.14), transparent 70%);
}

.building-info.is-dark {
  background:
    radial-gradient(circle at top right, rgba(14, 165, 233, 0.18), transparent 34%),
    radial-gradient(circle at left bottom, rgba(37, 99, 235, 0.18), transparent 30%),
    linear-gradient(145deg, rgba(15, 23, 42, 0.96), rgba(17, 24, 39, 0.98));
  border-color: rgba(51, 65, 85, 0.92);
  box-shadow: 0 20px 50px rgba(2, 6, 23, 0.36);
}

.building-hero {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(250px, 0.9fr);
  gap: 28px;
  align-items: stretch;
  margin-bottom: 24px;
}

.building-identity {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 22px;
}

.building-symbol {
  position: relative;
  width: 112px;
  height: 112px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 30px;
  color: #2563eb;
  background: linear-gradient(145deg, rgba(219, 234, 254, 0.96), rgba(239, 246, 255, 0.9));
  border: 1px solid rgba(191, 219, 254, 0.9);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.building-symbol-backdrop {
  position: absolute;
  inset: 10px;
  border-radius: 24px;
  border: 1px dashed rgba(59, 130, 246, 0.16);
}

.building-symbol svg {
  width: 42px;
  height: 42px;
  position: relative;
  z-index: 1;
}

.building-symbol-number {
  position: absolute;
  right: 10px;
  bottom: 10px;
  min-width: 30px;
  height: 30px;
  padding: 0 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #2563eb;
  color: #ffffff;
  font-size: 13px;
  font-weight: 800;
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.24);
}

.building-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.building-title {
  font-size: clamp(28px, 3vw, 40px);
  line-height: 1.05;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.03em;
}

.building-description {
  display: inline-flex;
  align-items: flex-start;
  gap: 12px;
  width: fit-content;
  max-width: 100%;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(226, 232, 240, 0.9);
  color: #334155;
  font-size: 16px;
  line-height: 1.55;
}

.building-description-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: #0ea5e9;
  margin-top: 2px;
}

.building-description-icon svg {
  width: 100%;
  height: 100%;
}

.building-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.building-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 9px 14px;
  border-radius: 999px;
  background: rgba(248, 250, 252, 0.92);
  border: 1px solid rgba(226, 232, 240, 0.92);
  color: #475569;
  font-size: 14px;
  font-weight: 600;
}

.building-pill svg {
  width: 16px;
  height: 16px;
  color: #2563eb;
  flex-shrink: 0;
}

.building-spotlight {
  position: relative;
  overflow: hidden;
  z-index: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 12px;
  padding: 22px;
  border-radius: 24px;
  border: 1px solid rgba(191, 219, 254, 0.92);
  background:
    radial-gradient(circle at top right, rgba(56, 189, 248, 0.2), transparent 42%),
    radial-gradient(circle at left bottom, rgba(34, 197, 94, 0.12), transparent 34%),
    linear-gradient(160deg, rgba(255, 255, 255, 0.96), rgba(239, 246, 255, 0.94));
  color: #0f172a;
  box-shadow: 0 16px 34px rgba(37, 99, 235, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.building-spotlight::before {
  content: "";
  position: absolute;
  inset: 10px;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.74);
  pointer-events: none;
}

.building-spotlight-label {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #2563eb;
}

.building-spotlight-main {
  display: flex;
  align-items: baseline;
  gap: 8px;
  line-height: 1;
}

.building-spotlight-main strong {
  font-size: clamp(32px, 3vw, 42px);
  font-weight: 800;
}

.building-spotlight-main span {
  font-size: 18px;
  font-weight: 700;
  color: #64748b;
}

.building-spotlight-text {
  font-size: 14px;
  line-height: 1.5;
  color: #475569;
}

.building-spotlight-track {
  position: relative;
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(191, 219, 254, 0.46);
}

.building-spotlight-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #22c55e, #38bdf8 58%, #2563eb);
  box-shadow: 0 4px 12px rgba(56, 189, 248, 0.24);
}

.building-spotlight-footnote {
  font-size: 12px;
  font-weight: 700;
  color: #2563eb;
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
  position: relative;
  z-index: 1;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(226, 232, 240, 0.92);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
}

.stat-icon {
  width: 42px;
  height: 42px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: rgba(219, 234, 254, 0.88);
  color: #2563eb;
  border: 1px solid rgba(191, 219, 254, 0.9);
}

.stat-icon svg {
  width: 20px;
  height: 20px;
}

.stat-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 800;
  line-height: 1;
  color: #0f172a;
}

.stat-label {
  font-size: 13px;
  font-weight: 700;
  color: #64748b;
}

.stat-card-success .stat-icon {
  background: rgba(220, 252, 231, 0.9);
  border-color: rgba(134, 239, 172, 0.9);
  color: #16a34a;
}

.stat-card-danger .stat-icon {
  background: rgba(254, 226, 226, 0.92);
  border-color: rgba(252, 165, 165, 0.92);
  color: #dc2626;
}

.building-info.is-dark .building-symbol {
  background: linear-gradient(145deg, rgba(15, 23, 42, 0.94), rgba(30, 41, 59, 0.92));
  border-color: rgba(51, 65, 85, 0.9);
  color: #7dd3fc;
}

.building-info.is-dark .building-symbol-backdrop {
  border-color: rgba(125, 211, 252, 0.14);
}

.building-info.is-dark .building-title,
.building-info.is-dark .stat-value {
  color: #f8fafc;
}

.building-info.is-dark .building-description,
.building-info.is-dark .stat-card {
  background: rgba(15, 23, 42, 0.74);
  border-color: rgba(51, 65, 85, 0.9);
  box-shadow: none;
}

.building-info.is-dark .building-description {
  color: #cbd5e1;
}

.building-info.is-dark .building-pill {
  background: rgba(15, 23, 42, 0.74);
  border-color: rgba(51, 65, 85, 0.92);
  color: #cbd5e1;
}

.building-info.is-dark .building-pill svg,
.building-info.is-dark .building-description-icon {
  color: #7dd3fc;
}

.building-info.is-dark .stat-icon {
  background: rgba(30, 41, 59, 0.92);
  border-color: rgba(51, 65, 85, 0.92);
  color: #93c5fd;
}

.building-info.is-dark .stat-card-success .stat-icon {
  background: rgba(20, 83, 45, 0.5);
  border-color: rgba(34, 197, 94, 0.28);
  color: #86efac;
}

.building-info.is-dark .stat-card-danger .stat-icon {
  background: rgba(127, 29, 29, 0.46);
  border-color: rgba(248, 113, 113, 0.28);
  color: #fca5a5;
}

.building-info.is-dark .stat-label {
  color: #94a3b8;
}

.building-info.is-dark .building-spotlight {
  background: linear-gradient(160deg, rgba(2, 6, 23, 0.96), rgba(15, 23, 42, 0.98));
  border-color: rgba(51, 65, 85, 0.9);
  color: #f8fafc;
  box-shadow: inset 0 1px 0 rgba(148, 163, 184, 0.08);
}

.building-info.is-dark .building-spotlight::before {
  border-color: rgba(148, 163, 184, 0.08);
}

.building-info.is-dark .building-spotlight-label,
.building-info.is-dark .building-spotlight-footnote {
  color: rgba(191, 219, 254, 0.9);
}

.building-info.is-dark .building-spotlight-main span {
  color: rgba(226, 232, 240, 0.78);
}

.building-info.is-dark .building-spotlight-text {
  color: rgba(226, 232, 240, 0.84);
}

.building-info.is-dark .building-spotlight-track {
  background: rgba(148, 163, 184, 0.14);
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
  position: relative;
}

.search-icon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  color: var(--text-secondary);
  pointer-events: none;
}

.search-icon svg {
  width: 100%;
  height: 100%;
}

.search-box input {
  width: 100%;
  padding: 12px 20px 12px 46px;
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

.filter-buttons.is-dark .filter-btn {
  background: #1e293b;
  border-color: #475569;
  color: #e2e8f0;
}

.filter-buttons.is-dark .filter-btn:hover {
  background: #334155;
  border-color: #64748b;
}

.filter-buttons.is-dark .filter-btn.active {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #e2e8f0;
  border-color: #2563eb;
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

.filtered-empty-state {
  margin-top: -8px;
}


@media (max-width: 768px) {
  .page-title {
    font-size: 28px;
  }

  .building-info {
    padding: 22px;
    border-radius: 24px;
  }

  .building-hero {
    grid-template-columns: 1fr;
    gap: 18px;
  }

  .building-identity {
    flex-direction: column;
    align-items: flex-start;
  }

  .building-symbol {
    width: 92px;
    height: 92px;
    border-radius: 24px;
  }

  .building-title {
    font-size: 30px;
  }

  .building-description {
    width: 100%;
  }

  .building-spotlight {
    padding: 18px;
    border-radius: 20px;
  }

  .stats-container {
    grid-template-columns: 1fr;
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

  .building-container {
    gap: 28px;
  }

  .building-info {
    padding: 18px;
  }

  .building-title {
    font-size: 26px;
  }

  .building-pills {
    width: 100%;
  }

  .building-pill {
    width: 100%;
    justify-content: flex-start;
  }

  .building-spotlight-main strong {
    font-size: 34px;
  }

  .stat-card {
    padding: 14px 15px;
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
