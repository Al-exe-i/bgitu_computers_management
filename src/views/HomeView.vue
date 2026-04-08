<script>
import router from "@/router/index.js";
import api from "@/services/api.js";
import {useNotificationsStore} from "@/stores/notifications.js";
import ErrorContainer from "@/components/Common/ErrorContainer.vue";
import LoaderContainer from "@/components/Common/LoaderContainer.vue";
import {getWsUrl} from "@/config/api.js";

export default {
  name: "HomeView",
  components: {LoaderContainer, ErrorContainer},
  data()
  {
    return {
      offices: [],
      loading: true,
      error: false,
      errorMsg: "",

      // WebSocket
      ws: null,
      wsReconnectAttempts: 0,
      maxReconnectAttempts: 3,
      reconnectDelay: 1000,
    }
  },

  methods: {
    handleOfficeClick(n)
    {
      router.push({
        name: "Office",
        params: { officeNumber: n }}
      )
    },

    async fetchOfficesData() {
      try {
        // Получаем список всех корпусов
        const res = await api.get('/offices/all_short'); // Ожидаем [{id: 1, address: '...'}, ...]
        const officesList = res.data;

        //  Для каждого корпуса запрашиваем статистику поломок
        // (Оптимизация: лучше сделать 1 запрос на бэкенд /offices/stats, но пока так)
        const statsPromises = officesList.map(office =>
            api.get(`/offices/faulty_computers/${office.id}`)
                .then(r => ({ ...office, faultyCount: r.data.count }))
                .catch(() => ({ ...office, faultyCount: 0 })) // Если ошибка, считаем 0
        );

        this.offices = await Promise.all(statsPromises);
        this.loading = false;

        // Подключаем сокет только после первой успешной загрузки
        if (!this.ws) this.connectWebSocket();

      }
      catch (err)
      {
        this.loading = false;
        this.error = true;
        this.errorMsg = "Не удалось загрузить список корпусов";
        console.error(err);
      }
    },

    connectWebSocket()
    {
      if (this.ws)
      {
        this.ws.onclose = null;
        this.ws.close();
      }

      this.ws = new WebSocket(getWsUrl())

      this.ws.onopen = () => {
        this.wsConnected = true;
        this.wsError = false;
        this.wsReconnectAttempts = 0;
        this.reconnectDelay = 1000;
      };

      this.ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg?.audience_updated)
        {
          this.fetchOfficesData();
        }
      };

      this.ws.onclose = (event) => {
        this.wsConnected = false;

        // Попытка переподключения
        if (this.wsReconnectAttempts < this.maxReconnectAttempts) {
          this.wsReconnectAttempts++;
          const delay = this.reconnectDelay * this.wsReconnectAttempts; // экспоненциально

          this.notify.warning(`Соединение потеряно. Переподключение №${this.wsReconnectAttempts} через ${delay / 1000} с...`);

          setTimeout(() => {
            this.connectWebSocket();
          }, delay);
        }
        else
        {
          // Не удалось восстановить
          this.wsError = true;
          this.notify.error("Не удалось восстановить соединение с сервером")
          this.error = true;
        }
      };
    },
    closeWebSocket()
    {
      if(this.ws)
      {
        this.ws.onclose = null;
        this.wsConnected = false;
        this.ws.close()
      }
    }
  },

  mounted() {
    this.fetchOfficesData()
  },

  computed: {
    notify()
    {
      return useNotificationsStore()
    }
  },

  beforeUnmount() {
    this.closeWebSocket();
  }

}
</script>

<template>
  <div class="dashboard-container">

    <LoaderContainer v-if="loading" />
    <ErrorContainer
        v-else-if="error" :errorText="errorMsg"
        container-title="Не удалось загрузить данные"
        error-title="Произошла ошибка при попытке загрузить статистику неисправностей. Проверьте подключение к интернету и повторите попытку."
    />

    <template v-else>
      <h1 class="dashboard-title">Выберите корпус</h1>

      <div class="stats-container">

        <!-- Карточка корпуса -->
        <div
            v-for="(office, index) in offices"
            :key="office.id"
            class="office-stats"
            :style="{ animationDelay: `${index * 0.15}s` }"
        >
          <div class="office-title">
            <div class="office-icon">
              <span class="office-number">{{ office.id }}</span>
            </div>
            <span class="office-number">Корпус №{{ office.id }}</span>
          </div>

          <div class="breakdowns-title">Неисправностей</div>

          <!-- Счетчик CSS (var(--target-num)) -->
          <div
              class="breakdowns-count"
              :class="{ red: office.faultyCount > 0 }"
              :style="{ '--target-num': office.faultyCount }"
          ></div>

          <button @click="handleOfficeClick(office.id)" class="view-details-btn">
            Просмотреть детали
          </button>
        </div>

      </div>
    </template>
  </div>
</template>

<style scoped>
.dashboard-container {
  padding: 40px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: calc(100vh - 120px);
  overflow-x: hidden;
}

.dashboard-title {
  font-size: 32px;
  font-weight: 700;
  color: #1f2937;
  text-align: center;
  margin-bottom: 40px;
  animation: upToDownAppear 1.2s ease-in-out;
}

@keyframes upToDownAppear {
  0%
  {
    opacity: 0;
    transform: translateY(-10vh);
  }
  100%
  {
    opacity: 1;
    transform: translateY(0);
  }
}

.stats-container {
  display: flex;
  justify-content: center;
  gap: 30px;
  overflow-x: auto;
  max-width: 100%;
  width: 100%;
  padding: 20px 20px 40px 20px;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
}

.office-stats
{
  background: white;
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.1);
  text-align: center;
  transition: all 0.3s ease;

  display: flex;
  flex-direction: column;
  align-items: center;

  min-width: 300px; /* Минимальная ширина */
  flex: 0 0 auto;   /* Запрещаем сжиматься */
  scroll-snap-align: center; /* Центрирование при скролле */

  opacity: 0; /* Скрыто до начала анимации */
  animation-name: popIn; /* Новая универсальная анимация */
  animation-duration: 0.8s;
  animation-timing-function: cubic-bezier(0.34, 1.56, 0.64, 1);
  animation-fill-mode: forwards;
}

.office-stats:hover {
  transform: translateY(-5px) !important;
  box-shadow: 0 12px 35px rgba(0,0,0,0.15);
}

@keyframes popIn {
  0% {
    opacity: 0;
    transform: translateY(50px) scale(0.9);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.office-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.office-icon {
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

.office-number {
  font-size: 24px;
  font-weight: 700;
}

.breakdowns-title {
  font-size: 18px;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 10px;
}

@property --num {
  syntax: "<integer>";
  initial-value: 0;
  inherits: false;
}

.breakdowns-count {
  font-size: 48px;
  font-weight: 800;
  color: #10b981;
  margin-bottom: 15px;

  transition: --num .5s linear;
  --num: var(--target-num);

  counter-reset: num var(--num);
}

.breakdowns-count::after {
  content: counter(num);
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

@media (max-width: 1024px) {
  .stats-container {
    justify-content: start;
  }
}

@media (max-width: 768px)
{
  .dashboard-title
  {
    font-size: 24px;
    margin-bottom: 20px;
  }

  .office-stats {
    min-width: 80vw;
  }

  .stats-container {
    padding-left: 20px;
    gap: 15px;
    justify-content: start;
  }

}
</style>