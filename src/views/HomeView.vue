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
      faultyOfficeOne: 0,
      faultyOfficeTwo: 0,
      loading: true,
      error: false,
      errorMsg: "",
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
    async fetchFaulty()
    {
      Promise.all([
        api.get('/offices/faulty_computers/1'),
        api.get('/offices/faulty_computers/2')
      ])
          .then(([response1, response2]) => {
            this.faultyOfficeOne = response1.data.count;
            this.faultyOfficeTwo = response2.data.count;
            this.loading = false;
            this.connectWebSocket()
          })
          .catch(err => {
            this.loading = false;
            this.error = true
            this.errorMsg = `${err.code}: ${err.message}`;
            this.notify.error("Не удалось загрузить данные");
          });
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
          this.fetchFaulty();
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
    this.fetchFaulty()
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
    <h1 v-if="!loading && !error" class="dashboard-title">Статистика неисправностей</h1>

    <LoaderContainer v-if="loading"/>

    <div v-if="!loading && !error" class="stats-container">

      <div class="office-stats left-animated">
        <div class="office-title">
          <div class="office-icon">
            <span class="office-number">1</span>
          </div>
          <span>Первый корпус</span>
        </div>
        <div class="breakdowns-title">Количество поломок</div>
        <div
            class="breakdowns-count"
            :class="{red: faultyOfficeOne > 0}"
            :style="{ '--target-num': faultyOfficeOne }">
        </div>
        <button @click="handleOfficeClick(1)" class="view-details-btn">Просмотреть детали</button>
      </div>

      <div class="office-stats right-animated">
        <div class="office-title">
          <div class="office-icon">
            <span class="office-number">2</span>
          </div>
          <span>Второй корпус</span>
        </div>
        <div class="breakdowns-title">Количество поломок</div>
        <div
            class="breakdowns-count"
            :class="{red: faultyOfficeTwo > 0}"
            :style="{ '--target-num': faultyOfficeTwo }">
        </div>
        <button @click="handleOfficeClick(2)" class="view-details-btn">Просмотреть детали</button>
      </div>
    </div>
    <ErrorContainer
        v-if="error"
        container-title="Не удалось загрузить данные"
        error-title="Произошла ошибка при попытке загрузить статистику неисправностей. Проверьте подключение к интернету и повторите попытку."
        :error-text="errorMsg"
    />
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
  gap: 30px;
  justify-content: center;
  flex-wrap: wrap;
  max-width: 800px;
}

.office-stats
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

  animation-duration: 1.2s;
  animation-timing-function: cubic-bezier(0.68, -0.55, 0.265, 1.55);
  animation-fill-mode: forwards;
}

.office-stats:hover {
  transform: translateY(-5px) !important;
  box-shadow: 0 12px 35px rgba(0,0,0,0.15);
}

.left-animated
{
  animation-name: slideFromLeft;
}

.right-animated
{
  animation-name: slideFromRight;
}

@keyframes slideFromLeft {
  0% {
    transform: translateX(-20vw) scale(0);
    opacity: 0;
  }

  100% {
    transform: translateX(0) scale(1);
    opacity: 1;
  }
}

@keyframes slideFromRight {
  0% {
    transform: translateX(20vw) scale(0);
    opacity: 0;
  }

  100% {
    transform: translateX(0) scale(1);
    opacity: 1;
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

@media (max-width: 768px)
{
  .office-stats
  {
    min-width: 250px;
  }

}
</style>