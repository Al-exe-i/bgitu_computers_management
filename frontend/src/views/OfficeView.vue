<script>
import FloorSection from "@/components/Common/FloorSection.vue";
import api from "@/services/api.js";
import router from "@/router/index.js";
import {useNotificationsStore} from "@/stores/notifications.js";
import LoaderContainer from "@/components/Common/LoaderContainer.vue";
import {useAuthStore} from "@/stores/auth.js";
import {useThemeStore} from "@/stores/theme.js";

const AUDIENCE_VIEW_MODE_STORAGE_KEY = 'bgitu-office-audience-view-mode';
const DEFAULT_AUDIENCE_VIEW_MODE = 'cards';
const AUDIENCE_VIEW_MODES = new Set(['cards', 'compact']);

function normalizeAudienceViewMode(mode) {
  return AUDIENCE_VIEW_MODES.has(mode) ? mode : DEFAULT_AUDIENCE_VIEW_MODE;
}

function readStoredAudienceViewMode() {
  if (typeof window === 'undefined') return DEFAULT_AUDIENCE_VIEW_MODE;

  try {
    return normalizeAudienceViewMode(window.localStorage.getItem(AUDIENCE_VIEW_MODE_STORAGE_KEY));
  } catch {
    return DEFAULT_AUDIENCE_VIEW_MODE;
  }
}

function storeAudienceViewMode(mode) {
  if (typeof window === 'undefined') return;

  try {
    window.localStorage.setItem(AUDIENCE_VIEW_MODE_STORAGE_KEY, mode);
  } catch {
    // localStorage can be unavailable in private mode; the UI still works without persistence.
  }
}

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
      isStatusDropdownOpen: false,
      proxyFloors: null,
      searchField: ``,
      audienceViewMode: readStoredAudienceViewMode(),
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

    hasHardwareStats() {
      return this.totalHardware > 0
    },

    hardwareHealthPercent() {
      if (!this.totalHardware) return 0
      return Math.round((this.workingHardwareCount / this.totalHardware) * 100)
    },

    statusFilterOptions() {
      return [
        {
          value: 'all',
          label: 'Все аудитории',
          description: 'Без ограничения по состоянию',
          tone: 'all'
        },
        {
          value: 'working',
          label: 'Исправные',
          description: 'Только аудитории без неисправностей',
          tone: 'working'
        },
        {
          value: 'broken',
          label: 'С неисправностями',
          description: 'Есть хотя бы одна проблема',
          tone: 'broken'
        }
      ]
    },

    activeStatusFilterOption() {
      return this.statusFilterOptions.find(option => option.value === this.filterMode) ?? this.statusFilterOptions[0]
    },

    canAddAudience() {
      const user = this.authStore.user;
      return this.authStore.isAuthenticated && user && user.role < 2;
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

          // Проверка по состоянию (Filter Mode)
          let matchesState = true;
          if (this.filterMode === 'working') {
            // Исправные: все компьютеры должны быть true
            // (или если оборудования нет вообще - считаем исправной)
            matchesState = audience.hardware.every(hw => hw.state === true);
          } else if (this.filterMode === 'broken') {
            // Неисправные: хотя бы один комп false
            matchesState = audience.hardware.some(hw => hw.state === false);
          }

          // 2. Проверка по поиску (Search Field)
          let matchesSearch = true;
          if (searchText) {
            matchesSearch = String(audience.number ?? audience.id).toLowerCase().startsWith(searchText);
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

    toggleStatusDropdown()
    {
      this.isStatusDropdownOpen = !this.isStatusDropdownOpen
    },

    selectStatusFilter(filterMode)
    {
      this.setFilterMode(filterMode)
      this.isStatusDropdownOpen = false
    },

    handleStatusDropdownOutside(event)
    {
      const dropdown = this.$refs.statusFilterDropdown
      if (!dropdown) return
      if (!dropdown.contains(event.target)) {
        this.isStatusDropdownOpen = false
      }
    },

    setAudienceViewMode(mode)
    {
      const normalizedMode = normalizeAudienceViewMode(mode);
      this.audienceViewMode = normalizedMode;
      storeAudienceViewMode(normalizedMode);
    },

    addNewAudience()
    {
      router.push({
        name: "New Audience",
        query: { office_id: this.office?.id ?? this.officeNumber },
      })
    }
  },

  mounted()
  {
    document.addEventListener('click', this.handleStatusDropdownOutside)
    this.getOffice(this.officeNumber)
  },

  beforeUnmount() {
    document.removeEventListener('click', this.handleStatusDropdownOutside)
  },

  watch: {
    officeNumber(newOfficeNumber)
    {
      this.getOffice(newOfficeNumber)
    },

    filterMode()
    {
      this.isStatusDropdownOpen = false
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

  <LoaderContainer v-if="loading"/>

  <div class="building-container">
    <div v-if="!loading" class="building-info" :class="{ 'is-dark': themeStore.isDark }">
      <div class="building-hero" :class="{ 'is-public': !authStore.isAuthenticated }">
        <div class="building-identity">
          <div class="building-symbol" aria-hidden="true">
            <div class="building-symbol-backdrop"></div>
            <svg xmlns="http://www.w3.org/2000/svg" width="640" height="640" viewBox="0 0 640 640"><path fill="currentColor" d="M335.9 84.2c-9.8-5.6-21.9-5.6-31.8 0l-224 128c-12.6 7.2-18.8 22-15.1 36S81.5 272 96 272h32v208l-51.2 38.4c-8.1 6-12.8 15.5-12.8 25.6c0 17.7 14.3 32 32 32h448c17.7 0 32-14.3 32-32c0-10.1-4.7-19.6-12.8-25.6L512 480V272h32c14.5 0 27.2-9.8 30.9-23.8s-2.5-28.8-15.1-36l-224-128zM464 272v208h-64V272zm-112 0v208h-64V272zm-112 0v208h-64V272zm80-112c17.7 0 32 14.3 32 32s-14.3 32-32 32s-32-14.3-32-32s14.3-32 32-32"/></svg>
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

            <div class="building-actions">
              <div class="building-floor-meta">
                <svg xmlns="http://www.w3.org/2000/svg" width="1536" height="1536" viewBox="0 0 1536 1536"><path fill="currentColor" d="M33 431q-18-9-25.5-19.5T0 383t7.5-28.5T33 335L670 17q39-19 98-17q59-2 98 17l637 318q18 9 25.5 19.5t7.5 28.5t-7.5 28.5T1503 431L866 749q-39 19-98 17q-59 2-98-17zm0 770q-18-9-25.5-19.5T0 1153t7.5-28.5T33 1105l160-80l477 238q40 19 98 16q58 3 98-16l477-238l160 80q18 9 25.5 19.5t7.5 28.5t-7.5 28.5t-25.5 19.5l-637 318q-40 19-98 16q-58 3-98-16zm0-384q-18-9-25.5-19.5T0 769t7.5-28.5T33 721l160-80l477 238q40 19 98 16q58 3 98-16l477-238l160 80q18 9 25.5 19.5t7.5 28.5t-7.5 28.5T1503 817l-637 318q-40 19-98 16q-58 3-98-16z"/></svg>
                <span>Этажей: {{ floorCount }}</span>
              </div>

              <button v-if="canAddAudience" class="add-classroom-btn add-classroom-btn-compact" @click="addNewAudience()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 5v14M5 12h14"></path>
                </svg>
                Добавить аудиторию
              </button>

            </div>
          </div>
        </div>

        <div v-if="authStore.isAuthenticated" class="building-spotlight">
          <div class="building-spotlight-heading">
            <span
              class="building-spotlight-signal"
              :class="{ 'is-alert': brokenHardware > 0 }"
              aria-hidden="true"
            ></span>
            <span class="building-spotlight-label">Техническое состояние</span>
          </div>

          <template v-if="hasHardwareStats">
            <div class="building-spotlight-main">
              <strong>{{ hardwareHealthPercent }}<small>%</small></strong>
              <span>{{ workingHardwareCount }} из {{ totalHardware }} единиц исправны</span>
            </div>
            <div class="building-spotlight-track" aria-hidden="true">
              <span class="building-spotlight-fill" :style="{ width: `${hardwareHealthPercent}%` }"></span>
            </div>
            <span class="building-spotlight-footnote" :class="{ 'is-alert': brokenHardware > 0 }">
              {{ brokenHardware > 0 ? `Требуют внимания: ${brokenHardware}` : 'Неисправностей не обнаружено' }}
            </span>
          </template>

          <div v-else class="building-spotlight-main is-empty">
            <strong>—</strong>
            <span>Нет оборудования для расчёта</span>
          </div>
        </div>
      </div>

      <div v-if="this.authStore.isAuthenticated" class="building-stats">
        <div class="building-stat">
          <span class="building-stat-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="2048" height="2048" viewBox="0 0 2048 2048"><path fill="currentColor" d="M1664 0v2048H384V0zm-128 128H512v1792h1024zm-192 1024q-26 0-45-19t-19-45t19-45t45-19t45 19t19 45t-19 45t-45 19"/></svg>
          </span>
          <div class="building-stat-copy">
            <div class="building-stat-label">Всего аудиторий</div>
            <div class="building-stat-value">{{ audiencesCount }}</div>
          </div>
        </div>

        <div class="building-stat">
          <span class="building-stat-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M9 18H4v-8h5zm6 0h-5V6h5zm6 0h-5V2h5zm1 4H3v-2h19z"/></svg>
          </span>
          <div class="building-stat-copy">
            <div class="building-stat-label">Всего оборудования</div>
            <div class="building-stat-value">{{ totalHardware }}</div>
          </div>
        </div>

        <div class="building-stat is-success">
          <span class="building-stat-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="8"></circle>
              <path d="m8.8 12.3 2.2 2.2 4.3-4.6"></path>
            </svg>
          </span>
          <div class="building-stat-copy">
            <div class="building-stat-label">Исправно</div>
            <div class="building-stat-value">{{ workingHardwareCount }}</div>
          </div>
        </div>

        <div class="building-stat is-danger">
          <span class="building-stat-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 10.5v3.75m-9.303 3.376C1.83 19.126 2.914 21 4.645 21h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 4.88c-.866-1.501-3.032-1.501-3.898 0L2.697 17.626ZM12 17.25h.007v.008H12v-.008Z"/></svg>
          </span>
          <div class="building-stat-copy">
            <div class="building-stat-label">Неисправно</div>
            <div class="building-stat-value">{{ this.brokenHardware }}</div>
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

      <div ref="statusFilterDropdown" class="status-filter-mobile" :class="{ 'is-dark': themeStore.isDark }">
        <button
          type="button"
          class="status-filter-trigger"
          :class="{ active: isStatusDropdownOpen }"
          @click="toggleStatusDropdown"
        >
          <span class="status-filter-trigger-mark" :class="`is-${activeStatusFilterOption.tone}`" aria-hidden="true">
            <svg v-if="activeStatusFilterOption.value === 'working'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="8"></circle>
              <path stroke-linecap="round" stroke-linejoin="round" d="m8.8 12.3 2.2 2.2 4.3-4.6"></path>
            </svg>
            <svg v-else-if="activeStatusFilterOption.value === 'broken'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9.5v3.3m0 3.1h.01M10.3 4.88 2.95 17.63A2.25 2.25 0 0 0 4.9 21h14.2a2.25 2.25 0 0 0 1.95-3.37L13.7 4.88a1.95 1.95 0 0 0-3.4 0"></path>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path stroke-linecap="round" d="M8 7h11"></path>
              <path stroke-linecap="round" d="M8 12h11"></path>
              <path stroke-linecap="round" d="M8 17h11"></path>
              <circle cx="4.5" cy="7" r="1"></circle>
              <circle cx="4.5" cy="12" r="1"></circle>
              <circle cx="4.5" cy="17" r="1"></circle>
            </svg>
          </span>

          <span class="status-filter-trigger-copy">
            <span class="status-filter-trigger-kicker">Фильтр исправности</span>
            <span class="status-filter-trigger-value">{{ activeStatusFilterOption.label }}</span>
          </span>

          <svg class="status-filter-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>

        <transition name="fade">
          <div v-show="isStatusDropdownOpen" class="status-filter-dropdown">
            <button
              v-for="option in statusFilterOptions"
              :key="option.value"
              type="button"
              class="status-filter-option"
              :class="[{ active: filterMode === option.value }, `is-${option.tone}`]"
              @click="selectStatusFilter(option.value)"
            >
              <span class="status-filter-option-mark" :class="`is-${option.tone}`" aria-hidden="true">
                <svg v-if="option.value === 'working'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="8"></circle>
                  <path stroke-linecap="round" stroke-linejoin="round" d="m8.8 12.3 2.2 2.2 4.3-4.6"></path>
                </svg>
                <svg v-else-if="option.value === 'broken'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 9.5v3.3m0 3.1h.01M10.3 4.88 2.95 17.63A2.25 2.25 0 0 0 4.9 21h14.2a2.25 2.25 0 0 0 1.95-3.37L13.7 4.88a1.95 1.95 0 0 0-3.4 0"></path>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path stroke-linecap="round" d="M8 7h11"></path>
                  <path stroke-linecap="round" d="M8 12h11"></path>
                  <path stroke-linecap="round" d="M8 17h11"></path>
                  <circle cx="4.5" cy="7" r="1"></circle>
                  <circle cx="4.5" cy="12" r="1"></circle>
                  <circle cx="4.5" cy="17" r="1"></circle>
                </svg>
              </span>

              <span class="status-filter-option-copy">
                <span class="status-filter-option-title">{{ option.label }}</span>
                <span class="status-filter-option-subtitle">{{ option.description }}</span>
              </span>

              <span class="status-filter-option-check" aria-hidden="true">
                <svg v-if="filterMode === option.value" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 12.5l4.2 4.2L19 7"></path>
                </svg>
              </span>
            </button>
          </div>
        </transition>
      </div>

      <div class="filter-buttons" :class="{ 'is-dark': themeStore.isDark }">
        <button class="filter-btn" @click="setFilterMode(`all`)" :class="{active: this.filterMode === `all`}">Все аудитории</button>
        <button class="filter-btn" @click="setFilterMode(`working`)" :class="{active: this.filterMode === `working`}">Исправные</button>
        <button class="filter-btn" @click="setFilterMode(`broken`)" :class="{active: this.filterMode === `broken`}">С неисправностями</button>
      </div>

      <div class="view-mode-switch" :class="{ 'is-dark': themeStore.isDark }">
        <button class="mode-btn" :class="{ active: audienceViewMode === 'cards' }" @click="setAudienceViewMode('cards')">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><title>Card SVG Icon</title><path fill="currentColor" d="M17.999 17c1.103 0 2-.897 2-2V5c0-1.103-.897-2-2-2h-12c-1.103 0-2 .897-2 2v10c0 1.103.897 2 2 2zm-12-12h12l.002 10H5.999zm-2 14h16v2h-16z"/></svg>
          Карточки
        </button>
        <button class="mode-btn" :class="{ active: audienceViewMode === 'compact' }" @click="setAudienceViewMode('compact')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8 7h12"></path>
            <path d="M8 12h12"></path>
            <path d="M8 17h12"></path>
            <circle cx="4" cy="7" r="1"></circle>
            <circle cx="4" cy="12" r="1"></circle>
            <circle cx="4" cy="17" r="1"></circle>
          </svg>
          Список
        </button>
      </div>
    </div>

    <floor-section
      v-if="floors"
      v-for="(floor, floorKey, floorIndex) in proxyFloors"
      :key="`floor-${floorKey}`"
      :audiences="floor.audiences"
      :number="floor.number"
      :display-mode="audienceViewMode"
      :style="{ animationDelay: `${0.42 + floorIndex * 0.08}s` }"
    ></floor-section>

    <div
      v-if="!loading && office?.audiences?.length > 0 && proxyFloors && Object.keys(proxyFloors).length === 0"
      class="empty-state filtered-empty-state"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v4m0 4.01l.01-.011M9 3H4v3m0 5v2m16-2v2M15 3h5v3M9 21H4v-3m11 3h5v-3"/></svg>
      <div class="empty-state-title">По выбранным фильтрам аудитории не найдены</div>
      <div class="empty-state-text">Измените параметры поиска или выберите другой фильтр</div>
    </div>

    <div v-if="!loading && Object.keys(floors).length === 0" class="empty-state">
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z"></path>
      </svg>
      <div class="empty-state-title">Аудиторий пока нет</div>
      <div v-if="canAddAudience" class="empty-state-text">Добавьте первую аудиторию для этого корпуса</div>
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

.building-container {
  width: 100%;
  max-width: 1200px;
  min-width: 0;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.building-info {
  width: 100%;
  position: relative;
  overflow: hidden;
  background: #f8fafc;
  border-radius: 20px;
  padding: 0;
  border: 1px solid #d8e0ea;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 18px 45px -36px rgba(15, 23, 42, 0.45);
  margin-top: 1rem;
  transform-origin: top center;
  animation: officeHeroReveal 0.78s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.building-info.is-dark {
  background: #101722 !important;
  border-color: #293548 !important;
  box-shadow: 0 1px 2px rgba(2, 6, 23, 0.35), 0 18px 50px -36px rgba(0, 0, 0, 0.9) !important;
}

.building-hero {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(270px, 0.65fr);
  gap: 0;
  align-items: stretch;
  margin: 0;
}

.building-hero.is-public {
  grid-template-columns: 1fr;
}

.building-identity {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 26px;
  padding: 36px 40px 34px;
  animation: officeContentRise 0.64s cubic-bezier(0.16, 1, 0.3, 1) 0.1s both;
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
  animation: officeSymbolPop 0.7s cubic-bezier(0.18, 1.35, 0.32, 1) 0.16s both;
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
  z-index: 1;
}

.building-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.building-title {
  max-width: 720px;
  font-family: "Segoe UI Variable Display", "Segoe UI", sans-serif;
  font-size: clamp(30px, 3.3vw, 44px);
  line-height: 1.02;
  font-weight: 750;
  color: #0f172a;
  letter-spacing: -0.045em;
}

.building-description {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  width: fit-content;
  max-width: 100%;
  padding: 0;
  border-radius: 0;
  background: transparent;
  border: 0;
  color: #526176;
  font-size: 15px;
  line-height: 1.45;
}

.building-description-icon {
  width: 17px;
  height: 17px;
  flex-shrink: 0;
  color: #2563eb;
  margin-top: 0;
}

.building-description-icon svg {
  width: 100%;
  height: 100%;
}

.building-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px;
  margin-top: 4px;
}

.building-floor-meta {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 0;
  padding: 0 16px 0 0;
  border-radius: 0;
  background: transparent;
  border: 0;
  border-right: 1px solid #d6dde7;
  color: #526176;
  font-size: 13px;
  font-weight: 650;
}

.building-floor-meta svg {
  width: 15px;
  height: 15px;
  color: #2563eb;
  flex-shrink: 0;
}

.building-info .add-classroom-btn-compact {
  min-height: 40px;
  padding: 9px 14px;
  border: 1px solid #1d4ed8;
  border-radius: 9px;
  background: #2563eb;
  color: #ffffff;
  font-size: 13px;
  font-weight: 650;
  box-shadow: none;
  transition: background-color 0.18s ease, border-color 0.18s ease;
}

.building-info .add-classroom-btn-compact:hover {
  transform: none;
  border-color: #1e40af;
  background: #1d4ed8;
  box-shadow: none;
}

.building-spotlight {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 14px;
  padding: 32px 30px;
  border-radius: 0;
  border: 0;
  border-left: 1px solid #d8e0ea;
  background: #eef3f8;
  color: #0f172a;
  box-shadow: none;
  animation: officeSpotlightReveal 0.62s cubic-bezier(0.16, 1, 0.3, 1) 0.2s both;
}

.building-spotlight::before {
  display: none;
}

.building-spotlight-heading {
  display: flex;
  align-items: center;
  gap: 8px;
}

.building-spotlight-signal {
  width: 7px;
  height: 7px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #16a36a;
  box-shadow: 0 0 0 4px rgba(22, 163, 106, 0.1);
}

.building-spotlight-signal.is-alert {
  background: #e5484d;
  box-shadow: 0 0 0 4px rgba(229, 72, 77, 0.1);
}

.building-spotlight-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #526176;
}

.building-spotlight-main {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 7px;
  line-height: 1;
}

.building-spotlight-main strong {
  font-family: "Segoe UI Variable Display", "Segoe UI", sans-serif;
  font-size: clamp(38px, 4vw, 50px);
  font-weight: 720;
  letter-spacing: -0.055em;
}

.building-spotlight-main strong small {
  margin-left: 2px;
  font-size: 0.48em;
  font-weight: 650;
  letter-spacing: -0.02em;
  color: #526176;
}

.building-spotlight-main span {
  font-size: 13px;
  line-height: 1.35;
  font-weight: 550;
  color: #526176;
}

.building-spotlight-main.is-empty {
  gap: 8px;
}

.building-spotlight-track {
  position: relative;
  height: 4px;
  overflow: hidden;
  border-radius: 999px;
  background: #d4dde8;
}

.building-spotlight-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #16a36a;
  box-shadow: none;
  transform-origin: left center;
  animation: officeProgressGrow 0.82s cubic-bezier(0.16, 1, 0.3, 1) 0.54s both;
}

.building-spotlight-footnote {
  font-size: 12px;
  line-height: 1.3;
  font-weight: 600;
  color: #16845a;
}

.building-spotlight-footnote.is-alert {
  color: #c8373c;
}

.building-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0;
  position: relative;
  z-index: 1;
  border-top: 1px solid #d8e0ea;
}

.building-stat {
  display: grid;
  grid-template-columns: 26px minmax(0, 1fr);
  align-items: center;
  gap: 11px;
  min-width: 0;
  min-height: 84px;
  padding: 17px 22px;
  border: 0;
  border-right: 1px solid #d8e0ea;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  animation: officeMetricReveal 0.58s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.building-stat:last-child {
  border-right: 0;
}

.building-stat:nth-child(1) {
  animation-delay: 0.24s;
}

.building-stat:nth-child(2) {
  animation-delay: 0.31s;
}

.building-stat:nth-child(3) {
  animation-delay: 0.38s;
}

.building-stat:nth-child(4) {
  animation-delay: 0.45s;
}

.building-stat-icon {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 0;
  background: transparent;
  color: #4f6b91;
  border: 0;
}

.building-stat-icon svg {
  width: 18px;
  height: 18px;
}

.building-stat-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.building-stat-value {
  order: -1;
  font-family: "Segoe UI Variable Display", "Segoe UI", sans-serif;
  font-size: 25px;
  font-weight: 720;
  line-height: 1;
  color: #0f172a;
  letter-spacing: -0.035em;
}

.building-stat-label {
  overflow: hidden;
  color: #68778c;
  font-size: 10px;
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: 0.075em;
  text-overflow: ellipsis;
  text-transform: uppercase;
  white-space: nowrap;
}

.building-stat.is-success .building-stat-icon {
  color: #16845a;
}

.building-stat.is-danger .building-stat-icon {
  color: #c8373c;
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
.building-info.is-dark .building-stat-value {
  color: #f8fafc;
}

.building-info.is-dark .building-description {
  color: #aebbd0 !important;
  background: transparent;
  border: 0;
}

.building-info.is-dark .building-floor-meta {
  background: transparent;
  border-color: #334156;
  color: #aebbd0;
}

.building-info.is-dark .building-floor-meta svg,
.building-info.is-dark .building-description-icon {
  color: #7aa7f8;
}

.building-info.is-dark .building-stats {
  border-color: #293548;
}

.building-info.is-dark .building-stat {
  background: transparent !important;
  border-color: #293548 !important;
  color: #edf2f8 !important;
  box-shadow: none !important;
}

.building-info.is-dark .building-stat-icon {
  background: transparent;
  border: 0;
  color: #84a9df;
}

.building-info.is-dark .building-stat-label {
  color: #8291a7 !important;
}

.building-info.is-dark .building-stat.is-success .building-stat-icon {
  color: #56c596;
}

.building-info.is-dark .building-stat.is-danger .building-stat-icon {
  color: #ff8b8f;
}

.building-info.is-dark .building-spotlight {
  background: #0b111b;
  border-color: #293548;
  color: #f8fafc;
  box-shadow: none;
}

.building-info.is-dark .building-spotlight-label {
  color: #8291a7;
}

.building-info.is-dark .building-spotlight-main span,
.building-info.is-dark .building-spotlight-main strong small {
  color: #9eacc0;
}

.building-info.is-dark .building-spotlight-footnote {
  color: #56c596;
}

.building-info.is-dark .building-spotlight-footnote.is-alert {
  color: #ff8b8f;
}

.building-info.is-dark .building-spotlight-track {
  background: #263244;
}

.building-info.is-dark .add-classroom-btn-compact {
  border-color: #4679d8;
  background: #2e63c7;
}

.building-info.is-dark .add-classroom-btn-compact:hover {
  border-color: #5b8ce7;
  background: #3970d2;
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
  animation: officePanelReveal 0.62s cubic-bezier(0.16, 1, 0.3, 1) 0.34s both;
  position: relative;
  z-index: 1;
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

.status-filter-mobile {
  display: none;
  position: relative;
}

.status-filter-trigger {
  width: 100%;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border: 1px solid rgba(203, 213, 225, 0.92);
  border-radius: 16px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(241, 245, 249, 0.96)),
    linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(14, 165, 233, 0.08));
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
  cursor: pointer;
  transition: border-color 0.25s ease, box-shadow 0.25s ease, transform 0.25s ease;
}

.status-filter-trigger:hover {
  transform: translateY(-1px);
  border-color: rgba(147, 197, 253, 0.95);
  box-shadow: 0 14px 28px rgba(37, 99, 235, 0.12);
}

.status-filter-trigger.active {
  border-color: rgba(96, 165, 250, 0.95);
  box-shadow: 0 16px 32px rgba(37, 99, 235, 0.16);
}

.status-filter-trigger-mark,
.status-filter-option-mark {
  min-width: 34px;
  width: 34px;
  height: 34px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.status-filter-trigger-mark svg,
.status-filter-option-mark svg,
.status-filter-option-check svg,
.status-filter-chevron {
  width: 18px;
  height: 18px;
}

.status-filter-trigger-mark.is-all,
.status-filter-option-mark.is-all {
  background: linear-gradient(135deg, rgba(226, 232, 240, 0.96), rgba(241, 245, 249, 0.98));
  color: #475569;
}

.status-filter-trigger-mark.is-working,
.status-filter-option-mark.is-working {
  background: linear-gradient(135deg, rgba(220, 252, 231, 0.98), rgba(240, 253, 244, 0.98));
  color: #16a34a;
}

.status-filter-trigger-mark.is-broken,
.status-filter-option-mark.is-broken {
  background: linear-gradient(135deg, rgba(254, 226, 226, 0.98), rgba(255, 241, 242, 0.98));
  color: #dc2626;
}

.status-filter-trigger-copy,
.status-filter-option-copy {
  min-width: 0;
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: flex-start;
}

.status-filter-trigger-kicker {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #64748b;
}

.status-filter-trigger-value,
.status-filter-option-title {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.status-filter-option-subtitle {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
  color: #64748b;
}

.status-filter-chevron {
  flex-shrink: 0;
  color: #64748b;
  transition: transform 0.25s ease, color 0.25s ease;
}

.status-filter-trigger.active .status-filter-chevron {
  color: #2563eb;
  transform: rotate(180deg);
}

.status-filter-dropdown {
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  right: 0;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-radius: 18px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  background: rgba(255, 255, 255, 0.97);
  backdrop-filter: blur(18px);
  box-shadow: 0 22px 44px rgba(15, 23, 42, 0.14);
  z-index: 20;
}

.status-filter-option {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: none;
  border-radius: 14px;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease;
}

.status-filter-option:hover {
  background: rgba(241, 245, 249, 0.92);
  transform: translateY(-1px);
}

.status-filter-option.active.is-all {
  background: linear-gradient(135deg, rgba(241, 245, 249, 0.96), rgba(248, 250, 252, 0.98));
}

.status-filter-option.active.is-working {
  background: linear-gradient(135deg, rgba(220, 252, 231, 0.82), rgba(240, 253, 244, 0.92));
}

.status-filter-option.active.is-broken {
  background: linear-gradient(135deg, rgba(254, 226, 226, 0.84), rgba(255, 241, 242, 0.94));
}

.status-filter-option-check {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: #2563eb;
}

.status-filter-mobile.is-dark .status-filter-trigger {
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(30, 41, 59, 0.94));
  border-color: rgba(71, 85, 105, 0.95);
  box-shadow: 0 14px 28px rgba(2, 6, 23, 0.28);
}

.status-filter-mobile.is-dark .status-filter-trigger:hover {
  border-color: rgba(96, 165, 250, 0.5);
}

.status-filter-mobile.is-dark .status-filter-trigger-value,
.status-filter-mobile.is-dark .status-filter-option-title {
  color: #f8fafc;
}

.status-filter-mobile.is-dark .status-filter-trigger-kicker,
.status-filter-mobile.is-dark .status-filter-option-subtitle,
.status-filter-mobile.is-dark .status-filter-chevron {
  color: #94a3b8;
}

.status-filter-mobile.is-dark .status-filter-dropdown {
  background: rgba(15, 23, 42, 0.97);
  border-color: rgba(51, 65, 85, 0.95);
  box-shadow: 0 22px 44px rgba(2, 6, 23, 0.38);
}

.status-filter-mobile.is-dark .status-filter-option:hover {
  background: rgba(30, 41, 59, 0.92);
}

.status-filter-mobile.is-dark .status-filter-option.active.is-all {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.96), rgba(51, 65, 85, 0.96));
}

.status-filter-mobile.is-dark .status-filter-option.active.is-working {
  background: linear-gradient(135deg, rgba(20, 83, 45, 0.48), rgba(21, 128, 61, 0.26));
}

.status-filter-mobile.is-dark .status-filter-option.active.is-broken {
  background: linear-gradient(135deg, rgba(127, 29, 29, 0.42), rgba(153, 27, 27, 0.22));
}

.view-mode-switch {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px;
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.92);
  border: 1px solid rgba(191, 219, 254, 0.9);
}

.mode-btn {
  min-height: 40px;
  padding: 10px 14px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: transparent;
  color: #475569;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.25s ease;
}

.mode-btn svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.mode-btn:hover {
  color: #1d4ed8;
  background: rgba(239, 246, 255, 0.9);
}

.mode-btn.active {
  background: linear-gradient(145deg, #3b82f6, #1d4ed8);
  border-color: rgba(29, 78, 216, 0.22);
  color: #ffffff;
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.18);
}

.add-classroom-btn {
  padding: 15px 30px;
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
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

.add-classroom-btn-compact {
  min-height: 40px;
  padding: 10px 16px;
  font-size: 14px;
  border-radius: 999px;
  box-shadow: 0 8px 18px rgba(16, 185, 129, 0.2);
}

.add-classroom-btn-compact svg {
  width: 16px;
  height: 16px;
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

.view-mode-switch.is-dark {
  background: #1e293b;
  border-color: #475569;
}

.view-mode-switch.is-dark .mode-btn {
  color: #cbd5e1;
}

.view-mode-switch.is-dark .mode-btn:hover {
  background: #334155;
  color: #e2e8f0;
}

.view-mode-switch.is-dark .mode-btn.active {
  background: linear-gradient(145deg, #2563eb, #1d4ed8);
  color: #ffffff;
  box-shadow: none;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 40px;
  background: rgba(249, 250, 251, 0.8);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 2px dashed #cbd5e1;
  animation: officePanelReveal 0.62s cubic-bezier(0.16, 1, 0.3, 1) 0.34s both;
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

@media (max-width: 1024px) {
  .building-hero {
    grid-template-columns: 1fr;
  }

  .building-spotlight {
    border-left: 0;
    border-top: 1px solid #d8e0ea;
  }

  .building-info.is-dark .building-spotlight {
    border-top-color: #293548;
  }

  .building-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .building-stat:nth-child(2) {
    border-right: 0;
  }

  .building-stat:nth-child(-n + 2) {
    border-bottom: 1px solid #d8e0ea;
  }

  .building-info.is-dark .building-stat:nth-child(-n + 2) {
    border-bottom-color: #293548 !important;
  }
}


@media (max-width: 768px) {
  .page-title {
    font-size: 28px;
  }

  .building-info {
    padding: 0;
    border-radius: 17px;
  }

  .building-hero {
    grid-template-columns: 1fr;
    gap: 0;
  }

  .building-identity {
    flex-direction: row;
    align-items: center;
    gap: 20px;
    padding: 28px 26px 26px;
  }

  .building-symbol {
    width: 92px;
    height: 92px;
    border-radius: 24px;
  }

  .building-title {
    font-size: 32px;
  }

  .building-description {
    width: fit-content;
  }

  .building-spotlight {
    padding: 24px 26px;
    border-radius: 0;
  }

  .building-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .controls-panel {
    flex-direction: column;
    align-items: stretch;
  }

  .search-box {
    width: 100%;
  }

  .status-filter-mobile {
    display: block;
    width: 100%;
  }

  .filter-buttons {
    display: none;
  }

  .view-mode-switch {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 4px;
    padding: 6px;
  }

  .mode-btn {
    min-height: 36px;
    min-width: 0;
    padding: 8px 8px;
    justify-content: center;
    font-size: 13px;
    gap: 6px;
    white-space: nowrap;
  }

  .mode-btn svg {
    width: 14px;
    height: 14px;
  }

  .add-classroom-btn {
    width: 100%;
  }

  .add-classroom-btn-compact {
    width: auto;
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
    padding: 0;
  }

  .building-identity {
    align-items: flex-start;
    gap: 15px;
    padding: 22px 18px 20px;
  }

  .building-copy {
    gap: 9px;
  }

  .building-title {
    font-size: clamp(23px, 7vw, 27px);
    line-height: 1.06;
  }

  .building-description {
    align-items: flex-start;
    font-size: 13px;
  }

  .building-actions {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .building-floor-meta {
    width: auto;
    justify-content: flex-start;
    padding: 0;
    border-right: 0;
  }

  .building-spotlight-main strong {
    font-size: 38px;
  }

  .building-spotlight {
    padding: 20px 18px;
  }

  .building-spotlight-main {
    gap: 6px;
  }

  .building-stat {
    grid-template-columns: 20px minmax(0, 1fr);
    gap: 8px;
    min-height: 72px;
    padding: 12px 13px;
  }

  .building-stat-icon,
  .building-stat-icon svg {
    width: 16px;
    height: 16px;
  }

  .building-stat-value {
    font-size: 22px;
  }

  .building-stat-label {
    font-size: 9px;
    letter-spacing: 0.045em;
    text-overflow: clip;
    white-space: normal;
  }

  .view-mode-switch {
    padding: 4px;
    border-radius: 14px;
  }

  .status-filter-trigger {
    padding: 8px 10px;
    border-radius: 14px;
  }

  .status-filter-trigger-mark,
  .status-filter-option-mark {
    min-width: 32px;
    width: 32px;
    height: 32px;
    border-radius: 11px;
  }

  .status-filter-trigger-value,
  .status-filter-option-title {
    font-size: 13px;
  }

  .status-filter-option-subtitle {
    font-size: 10px;
  }

  .status-filter-dropdown {
    padding: 7px;
    border-radius: 16px;
  }

  .status-filter-option {
    padding: 9px 10px;
    border-radius: 12px;
  }

  .mode-btn {
    min-height: 34px;
    padding: 6px 8px;
    justify-content: center;
    font-size: 12px;
    border-radius: 10px;
  }

  .mode-btn svg {
    display: none;
  }

  .add-classroom-btn-compact {
    width: 100%;
    justify-content: center;
    min-height: 36px;
    padding: 8px 12px;
    font-size: 13px;
    border-radius: 14px;
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

@keyframes officeHeroReveal {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes officeContentRise {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes officeSymbolPop {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.82) rotate(-3deg);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1) rotate(0);
  }
}

@keyframes officeSpotlightReveal {
  from {
    opacity: 0;
    transform: translateX(12px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes officeProgressGrow {
  from {
    transform: scaleX(0);
  }
  to {
    transform: scaleX(1);
  }
}

@keyframes officeMetricReveal {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes officePanelReveal {
  from {
    opacity: 0;
    transform: translateY(22px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .building-info,
  .building-identity,
  .building-symbol,
  .building-spotlight,
  .building-spotlight-fill,
  .building-stat,
  .controls-panel,
  .empty-state {
    animation: none !important;
  }
}
</style>
