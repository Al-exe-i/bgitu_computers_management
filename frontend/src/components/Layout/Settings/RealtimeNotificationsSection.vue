<script>
import { useAuthStore } from "@/stores/auth";
import { useNotificationsStore } from "@/stores/notifications";
import {
  createNotificationSubscription,
  deleteNotificationSubscription,
  getNotificationAudiencesDictionary,
  getNotificationOfficesDictionary,
  getNotificationSubscriptions
} from "@/services/notifications";

export default {
  name: "RealtimeNotificationsSection",

  props: {
    showHeader: {
      type: Boolean,
      default: true
    }
  },

  data() {
    return {
      subscriptions: [],
      offices: [],
      audiences: [],
      loading: true,
      subscriptionsLoading: false,
      dictionariesLoading: false,
      error: "",
      securityLoading: false,
      mutationKeys: [],
      deletingIds: [],
      form: {
        scope_type: "audience",
        scope_id: null
      },
      eventOptions: [
        {
          value: "hardware_fault",
          label: "Неисправность",
          description: "Когда оборудование стало неисправным."
        },
        {
          value: "hardware_recovered",
          label: "Восстановление",
          description: "Когда оборудование снова исправно."
        },
        {
          value: "audience_changed",
          label: "Изменение аудитории",
          description: "Когда изменили аудиторию или сетку оборудования."
        }
      ]
    };
  },

  computed: {
    authStore() {
      return useAuthStore();
    },

    notify() {
      return useNotificationsStore();
    },

    currentUserId() {
      const userId = this.authStore.user?.id;
      return Number.isFinite(Number(userId)) ? Number(userId) : null;
    },

    securitySubscription() {
      if (!this.currentUserId) return null;

      return this.subscriptions.find((subscription) =>
        subscription.scope_type === "user" &&
        subscription.event_type === "auth_security" &&
        Number(subscription.scope_id) === this.currentUserId
      ) || null;
    },

    hasSecuritySubscription() {
      return !!this.securitySubscription;
    },

    displaySubscriptions() {
      return this.subscriptions.filter((subscription) =>
        !(subscription.scope_type === "user" && subscription.event_type === "auth_security")
      );
    },

    sortedSubscriptions() {
      return [...this.displaySubscriptions].sort((left, right) => {
        const leftTime = new Date(left.created_at || 0).getTime();
        const rightTime = new Date(right.created_at || 0).getTime();

        if (leftTime !== rightTime) return rightTime - leftTime;
        return (right.id || 0) - (left.id || 0);
      });
    },

    scopeOptions() {
      return [
        { value: "audience", label: "Аудитория" },
        { value: "office", label: "Корпус" }
      ];
    },

    activeScopeItems() {
      return this.form.scope_type === "office" ? this.offices : this.audiences;
    },

    scopePlaceholder() {
      if (this.dictionariesLoading) return "Загрузка списка...";
      return this.form.scope_type === "office" ? "Выберите корпус" : "Выберите аудиторию";
    },

    canManageSelectedScopeEvents() {
      return this.form.scope_id !== null && this.form.scope_id !== "";
    },

    selectedScopeLabel() {
      if (!this.canManageSelectedScopeEvents) return "";

      const item = this.activeScopeItems.find(
        (entry) => Number(entry.id) === Number(this.form.scope_id)
      );
      if (!item) return "";

      return this.form.scope_type === "office"
        ? this.getOfficeLabel(item)
        : this.getAudienceLabel(item);
    }
  },

  watch: {
    "form.scope_type"() {
      this.form.scope_id = null;
    }
  },

  methods: {
    getErrorMessage(error, fallbackMessage) {
      const status = error?.response?.status;
      const detail = error?.response?.data?.detail;
      const message = typeof detail === "string" ? detail : "";

      if (!error?.response) {
        return "Не удалось связаться с сервером. Проверьте подключение и повторите попытку.";
      }

      if (status === 401) return "Необходимо повторно войти в систему.";
      if (status === 403) return "Недостаточно прав для управления подписками.";
      if (status === 404) return "Подписка или выбранная область не найдены.";
      if (status === 409 && message.toLowerCase().includes("already exists")) {
        return "Такая подписка уже включена.";
      }
      if (status === 422) return "Проверьте параметры подписки.";

      return message || fallbackMessage;
    },

    formatDateTime(value) {
      if (!value) return "—";

      return new Intl.DateTimeFormat("ru-RU", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      }).format(new Date(value));
    },

    getOfficeLabel(office) {
      return office?.address ? `Корпус №${office.id}, ${office.address}` : `Корпус №${office?.id}`;
    },

    getAudienceLabel(audience) {
      const parts = [`Аудитория №${audience?.id}`];
      if (audience?.office_id) parts.push(`корпус №${audience.office_id}`);
      if (audience?.floor !== undefined && audience?.floor !== null) parts.push(`${audience.floor} этаж`);
      return parts.join(", ");
    },

    getScopeTypeLabel(scopeType) {
      if (scopeType === "office") return "Корпус";
      if (scopeType === "user") return "Аккаунт";
      return "Аудитория";
    },

    getEventTypeLabel(eventType) {
      const labels = {
        audience_changed: "Изменение аудитории",
        hardware_fault: "Неисправность",
        hardware_recovered: "Восстановление",
        auth_security: "Безопасность"
      };
      return labels[eventType] || eventType;
    },

    getSubscriptionScopeLabel(subscription) {
      if (subscription.scope_type === "user") return "Безопасность аккаунта";

      if (subscription.scope_type === "office") {
        const office = this.offices.find((item) => Number(item.id) === Number(subscription.scope_id));
        return office ? this.getOfficeLabel(office) : `Корпус №${subscription.scope_id}`;
      }

      const audience = this.audiences.find((item) => Number(item.id) === Number(subscription.scope_id));
      return audience ? this.getAudienceLabel(audience) : `Аудитория №${subscription.scope_id}`;
    },

    getSubscriptionKey(scopeType, scopeId, eventType) {
      return `${scopeType}:${scopeId}:${eventType}`;
    },

    findSubscription(scopeType, scopeId, eventType) {
      return this.subscriptions.find((subscription) =>
        subscription.scope_type === scopeType &&
        Number(subscription.scope_id) === Number(scopeId) &&
        subscription.event_type === eventType
      ) || null;
    },

    isSelectedScopeEventEnabled(eventType) {
      if (!this.canManageSelectedScopeEvents) return false;
      return !!this.findSubscription(this.form.scope_type, Number(this.form.scope_id), eventType);
    },

    isSelectedScopeEventBusy(eventType) {
      if (!this.canManageSelectedScopeEvents) return false;
      return this.mutationKeys.includes(
        this.getSubscriptionKey(this.form.scope_type, Number(this.form.scope_id), eventType)
      );
    },

    async loadSubscriptions({ silent = false } = {}) {
      this.subscriptionsLoading = true;

      try {
        const response = await getNotificationSubscriptions();
        this.subscriptions = Array.isArray(response.data) ? response.data : [];
        if (!silent) this.error = "";
      } catch (error) {
        if (!silent) {
          const message = this.getErrorMessage(error, "Не удалось загрузить подписки.");
          this.error = message;
          this.notify.error(message);
        }
        throw error;
      } finally {
        this.subscriptionsLoading = false;
      }
    },

    async loadDictionaries({ silent = false } = {}) {
      this.dictionariesLoading = true;

      try {
        const [officesResponse, audiencesResponse] = await Promise.all([
          getNotificationOfficesDictionary(),
          getNotificationAudiencesDictionary()
        ]);

        this.offices = Array.isArray(officesResponse.data)
          ? [...officesResponse.data].sort((left, right) => (left.id || 0) - (right.id || 0))
          : [];

        this.audiences = Array.isArray(audiencesResponse.data)
          ? [...audiencesResponse.data].sort((left, right) => {
              const officeDiff = (left.office_id || 0) - (right.office_id || 0);
              if (officeDiff !== 0) return officeDiff;
              const floorDiff = (left.floor || 0) - (right.floor || 0);
              if (floorDiff !== 0) return floorDiff;
              return (left.id || 0) - (right.id || 0);
            })
          : [];

        if (!silent) this.error = "";
      } catch (error) {
        if (!silent) {
          const message = this.getErrorMessage(error, "Не удалось загрузить справочники.");
          this.error = message;
          this.notify.error(message);
        }
        throw error;
      } finally {
        this.dictionariesLoading = false;
      }
    },

    async initialize() {
      this.loading = true;
      this.error = "";

      try {
        await Promise.all([
          this.loadSubscriptions({ silent: true }),
          this.loadDictionaries({ silent: true })
        ]);
      } catch (error) {
        this.error = this.getErrorMessage(error, "Не удалось загрузить настройки уведомлений.");
      } finally {
        this.loading = false;
      }
    },

    async toggleSecuritySubscription() {
      if (!this.currentUserId || this.securityLoading) return;

      this.securityLoading = true;
      this.error = "";

      try {
        if (this.securitySubscription?.id) {
          const id = this.securitySubscription.id;
          await deleteNotificationSubscription(id);
          this.subscriptions = this.subscriptions.filter((item) => item.id !== id);
          this.notify.info("Уведомления безопасности отключены.");
        } else {
          await createNotificationSubscription({
            scope_type: "user",
            scope_id: this.currentUserId,
            event_type: "auth_security"
          });
          await this.loadSubscriptions({ silent: true });
          this.notify.success("Уведомления безопасности включены.");
        }
      } catch (error) {
        const message = this.getErrorMessage(error, "Не удалось изменить подписку безопасности.");
        this.error = message;
        this.notify.error(message);
      } finally {
        this.securityLoading = false;
      }
    },

    async toggleSelectedScopeEvent(eventType) {
      if (!this.canManageSelectedScopeEvents) return;

      const scopeType = this.form.scope_type;
      const scopeId = Number(this.form.scope_id);
      const loadingKey = this.getSubscriptionKey(scopeType, scopeId, eventType);

      if (this.mutationKeys.includes(loadingKey)) return;

      this.mutationKeys = [...this.mutationKeys, loadingKey];
      this.error = "";

      try {
        const existing = this.findSubscription(scopeType, scopeId, eventType);

        if (existing?.id) {
          await deleteNotificationSubscription(existing.id);
        } else {
          await createNotificationSubscription({
            scope_type: scopeType,
            scope_id: scopeId,
            event_type: eventType
          });
        }

        await this.loadSubscriptions({ silent: true });

        const eventLabel = this.getEventTypeLabel(eventType);
        if (existing?.id) {
          this.notify.info(`Подписка «${eventLabel}» отключена.`);
        } else {
          this.notify.success(`Подписка «${eventLabel}» включена.`);
        }
      } catch (error) {
        const message = this.getErrorMessage(error, "Не удалось обновить подписку.");
        this.error = message;
        this.notify.error(message);
      } finally {
        this.mutationKeys = this.mutationKeys.filter((item) => item !== loadingKey);
      }
    },

    async deleteSubscriptionById(id) {
      if (this.deletingIds.includes(id)) return;

      this.deletingIds = [...this.deletingIds, id];
      this.error = "";

      try {
        await deleteNotificationSubscription(id);
        this.subscriptions = this.subscriptions.filter((item) => item.id !== id);
        this.notify.info("Подписка удалена.");
      } catch (error) {
        const message = this.getErrorMessage(error, "Не удалось удалить подписку.");
        this.error = message;
        this.notify.error(message);
      } finally {
        this.deletingIds = this.deletingIds.filter((item) => item !== id);
      }
    }
  },

  async mounted() {
    await this.initialize();
  }
};
</script>

<template>
  <section class="realtime-notifications-section" :class="{ 'is-embedded': !showHeader }">
    <div v-if="showHeader" class="realtime-notifications-header">
      <h3>Realtime-уведомления</h3>
    </div>

    <div v-if="error" class="rn-alert">
      <span>!</span>
      <p>{{ error }}</p>
    </div>

    <div v-if="loading" class="rn-loading">
      <span class="rn-spinner"></span>
      <span>Загрузка настроек уведомлений...</span>
    </div>

    <template v-else>

      <div class="rn-security-card">
        <div>
          <span class="rn-kicker">Безопасность аккаунта</span>
          <h4>Уведомления о входах и сессиях</h4>
          <p>
            {{ hasSecuritySubscription
              ? "Вы получаете события безопасности в интерфейсе."
              : "Включите, чтобы видеть важные события аккаунта сразу в системе." }}
          </p>
          <small v-if="hasSecuritySubscription && securitySubscription?.created_at">
            Активно с {{ formatDateTime(securitySubscription.created_at) }}
          </small>
        </div>
        <button
          type="button"
          class="rn-toggle"
          :class="{ active: hasSecuritySubscription }"
          :disabled="securityLoading || !currentUserId"
          :aria-pressed="hasSecuritySubscription"
          @click="toggleSecuritySubscription"
        >
          <span v-if="securityLoading" class="rn-spinner small"></span>
          <span v-else></span>
        </button>
      </div>

      <div class="rn-layout">
        <section class="rn-panel">
          <div class="rn-panel-head">
            <div>
              <h4>Активные подписки</h4>
              <p>Что сейчас будет приходить в realtime-уведомления.</p>
            </div>
            <span class="rn-counter">{{ displaySubscriptions.length }}</span>
          </div>

          <div v-if="subscriptionsLoading" class="rn-loading compact">
            <span class="rn-spinner"></span>
            <span>Обновление списка...</span>
          </div>

          <div v-else-if="sortedSubscriptions.length" class="rn-subscriptions">
            <article
              v-for="subscription in sortedSubscriptions"
              :key="subscription.id"
              class="rn-subscription"
            >
              <div>
                <div class="rn-tags">
                  <span>{{ getScopeTypeLabel(subscription.scope_type) }}</span>
                  <span class="accent">{{ getEventTypeLabel(subscription.event_type) }}</span>
                </div>
                <strong>{{ getSubscriptionScopeLabel(subscription) }}</strong>
                <small>{{ formatDateTime(subscription.created_at) }}</small>
              </div>

              <button
                type="button"
                class="rn-delete"
                :disabled="deletingIds.includes(subscription.id)"
                @click="deleteSubscriptionById(subscription.id)"
              >
                <span v-if="deletingIds.includes(subscription.id)" class="rn-spinner small danger"></span>
                <span v-else>×</span>
              </button>
            </article>
          </div>

          <div v-else class="rn-empty">
            <strong>Подписок пока нет</strong>
            <span>Выберите аудиторию или корпус и включите нужные события.</span>
          </div>
        </section>

        <section class="rn-panel">
          <div class="rn-panel-head">
            <div>
              <h4>Добавить подписку</h4>
              <p>Выберите область и тип события.</p>
            </div>
          </div>

          <div class="rn-form">
            <div class="rn-form-group">
              <label>Область</label>
              <div class="rn-segmented">
                <button
                  v-for="option in scopeOptions"
                  :key="option.value"
                  type="button"
                  :class="{ active: form.scope_type === option.value }"
                  @click="form.scope_type = option.value"
                >
                  {{ option.label }}
                </button>
              </div>
            </div>

            <div class="rn-form-group">
              <label>{{ form.scope_type === "office" ? "Корпус" : "Аудитория" }}</label>
              <select
                v-model.number="form.scope_id"
                :disabled="dictionariesLoading || !activeScopeItems.length"
              >
                <option :value="null">{{ scopePlaceholder }}</option>
                <option v-for="item in activeScopeItems" :key="item.id" :value="item.id">
                  {{ form.scope_type === "office" ? getOfficeLabel(item) : getAudienceLabel(item) }}
                </option>
              </select>
            </div>

            <div class="rn-event-grid">
              <label
                v-for="option in eventOptions"
                :key="option.value"
                class="rn-event"
                :class="{
                  active: isSelectedScopeEventEnabled(option.value),
                  disabled: !canManageSelectedScopeEvents,
                  loading: isSelectedScopeEventBusy(option.value)
                }"
              >
                <input
                  type="checkbox"
                  :checked="isSelectedScopeEventEnabled(option.value)"
                  :disabled="!canManageSelectedScopeEvents || isSelectedScopeEventBusy(option.value)"
                  @change="toggleSelectedScopeEvent(option.value)"
                >
                <span class="rn-event-marker">
                  <span v-if="isSelectedScopeEventBusy(option.value)" class="rn-spinner small"></span>
                  <span v-else-if="isSelectedScopeEventEnabled(option.value)">✓</span>
                </span>
                <span>
                  <strong>{{ option.label }}</strong>
                  <em>{{ option.description }}</em>
                </span>
              </label>
            </div>

            <p v-if="selectedScopeLabel" class="rn-note">
              Настройка для: <strong>{{ selectedScopeLabel }}</strong>
            </p>
          </div>
        </section>
      </div>
    </template>
  </section>
</template>

<style scoped>
.realtime-notifications-section {
  --rn-bg: rgba(255, 255, 255, 0.92);
  --rn-bg-strong: rgba(248, 250, 252, 0.96);
  --rn-border: rgba(148, 163, 184, 0.28);
  --rn-text: #0f172a;
  --rn-muted: #64748b;
  --rn-accent: #2563eb;
  --rn-accent-soft: rgba(37, 99, 235, 0.1);
  display: grid;
  gap: 18px;
}

.realtime-notifications-header h3,
.rn-hero-copy h4,
.rn-security-card h4,
.rn-panel-head h4 {
  color: var(--rn-text);
  margin: 0;
}

.realtime-notifications-header p,
.rn-hero-copy p,
.rn-security-card p,
.rn-panel-head p,
.rn-empty span,
.rn-subscription small,
.rn-event em,
.rn-note {
  color: var(--rn-muted);
}

.rn-alert,
.rn-hero,
.rn-security-card,
.rn-panel {
  border: 1px solid var(--rn-border);
  background: var(--rn-bg);
  border-radius: 24px;
  box-shadow: 0 22px 48px rgba(15, 23, 42, 0.08);
}

.rn-alert {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 14px 16px;
  color: #991b1b;
  background: rgba(254, 242, 242, 0.92);
}

.rn-alert span {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 999px;
  background: #ef4444;
  color: #fff;
  font-weight: 800;
}

.rn-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 130px;
  color: var(--rn-muted);
}

.rn-loading.compact {
  min-height: 80px;
}

.rn-spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(37, 99, 235, 0.18);
  border-top-color: var(--rn-accent);
  border-radius: 999px;
  animation: rn-spin 0.8s linear infinite;
}

.rn-spinner.small {
  width: 16px;
  height: 16px;
  border-width: 2px;
}

.rn-hero,
.rn-security-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 20px;
}

.rn-hero {
  background:
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.14), transparent 36%),
    var(--rn-bg);
}

.rn-hero-icon {
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  border-radius: 18px;
  background: linear-gradient(135deg, #2563eb, #0f766e);
  color: #fff;
  flex: 0 0 auto;
}

.rn-hero-icon svg {
  width: 28px;
  height: 28px;
}

.rn-pill,
.rn-kicker,
.rn-counter,
.rn-tags span {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  border-radius: 999px;
  background: var(--rn-accent-soft);
  color: var(--rn-accent);
  font-size: 12px;
  font-weight: 800;
  padding: 5px 10px;
}

.rn-hero-copy,
.rn-security-card > div {
  display: grid;
  gap: 8px;
}

.rn-toggle {
  width: 58px;
  height: 34px;
  border: 1px solid var(--rn-border);
  background: #cbd5e1;
  border-radius: 999px;
  padding: 3px;
  cursor: pointer;
  transition: 0.2s ease;
}

.rn-toggle > span:not(.rn-spinner) {
  display: block;
  width: 26px;
  height: 26px;
  border-radius: 999px;
  background: #fff;
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.18);
  transition: transform 0.2s ease;
}

.rn-toggle.active {
  background: linear-gradient(135deg, #2563eb, #0f766e);
}

.rn-toggle.active > span:not(.rn-spinner) {
  transform: translateX(24px);
}

.rn-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 0.9fr);
  gap: 18px;
}

.rn-panel {
  padding: 18px;
}

.rn-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 16px;
}

.rn-subscriptions,
.rn-form,
.rn-event-grid {
  display: grid;
  gap: 12px;
}

.rn-subscription,
.rn-event,
.rn-empty,
.rn-note {
  border: 1px solid var(--rn-border);
  background: var(--rn-bg-strong);
  border-radius: 18px;
}

.rn-subscription {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 14px;
}

.rn-subscription > div {
  display: grid;
  gap: 8px;
}

.rn-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.rn-tags .accent {
  background: rgba(15, 118, 110, 0.11);
  color: #0f766e;
}

.rn-delete {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 12px;
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
  font-size: 24px;
  cursor: pointer;
}

.rn-empty {
  display: grid;
  gap: 6px;
  padding: 18px;
  text-align: center;
}

.rn-form-group {
  display: grid;
  gap: 8px;
}

.rn-form-group label {
  color: var(--rn-text);
  font-weight: 800;
  font-size: 13px;
}

.rn-segmented {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
  padding: 5px;
  border-radius: 16px;
  background: var(--rn-bg-strong);
  border: 1px solid var(--rn-border);
}

.rn-segmented button,
.rn-form select {
  border: 1px solid transparent;
  border-radius: 12px;
  padding: 10px 12px;
  background: transparent;
  color: var(--rn-text);
}

.rn-segmented button {
  cursor: pointer;
  font-weight: 800;
}

.rn-segmented button.active {
  background: #fff;
  border-color: var(--rn-border);
  color: var(--rn-accent);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
}

.rn-form select {
  width: 100%;
  background: var(--rn-bg-strong);
  border-color: var(--rn-border);
}

.rn-event {
  display: grid;
  grid-template-columns: 34px 1fr;
  gap: 10px;
  padding: 12px;
  cursor: pointer;
  transition: 0.18s ease;
}

.rn-event input {
  display: none;
}

.rn-event.active {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.1), rgba(15, 118, 110, 0.08));
  border-color: rgba(37, 99, 235, 0.32);
}

.rn-event.disabled {
  opacity: 0.62;
  cursor: not-allowed;
}

.rn-event-marker {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 11px;
  background: #e2e8f0;
  color: #fff;
  font-weight: 900;
}

.rn-event.active .rn-event-marker {
  background: linear-gradient(135deg, #2563eb, #0f766e);
}

.rn-event span:last-child {
  display: grid;
  gap: 3px;
}

.rn-event em {
  font-style: normal;
  font-size: 12px;
}

.rn-note {
  padding: 12px;
}

@keyframes rn-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 900px) {
  .rn-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .rn-hero,
  .rn-security-card,
  .rn-panel-head,
  .rn-subscription {
    flex-direction: column;
    align-items: stretch;
  }
}

:global(html[data-theme='dark'] .realtime-notifications-section) {
  --rn-bg: rgba(15, 23, 42, 0.9);
  --rn-bg-strong: rgba(15, 23, 42, 0.96);
  --rn-border: #334155;
  --rn-text: #e2e8f0;
  --rn-muted: #94a3b8;
  --rn-accent: #60a5fa;
  --rn-accent-soft: rgba(37, 99, 235, 0.22);
}

:global(html[data-theme='dark'] .rn-alert) {
  background: rgba(127, 29, 29, 0.22) !important;
  border-color: rgba(248, 113, 113, 0.28) !important;
  color: #fecaca !important;
}

:global(html[data-theme='dark'] .rn-alert span) {
  background: rgba(248, 113, 113, 0.18) !important;
  color: #fecaca !important;
}

:global(html[data-theme='dark'] .rn-hero),
:global(html[data-theme='dark'] .rn-security-card),
:global(html[data-theme='dark'] .rn-panel),
:global(html[data-theme='dark'] .rn-subscription),
:global(html[data-theme='dark'] .rn-empty),
:global(html[data-theme='dark'] .rn-note),
:global(html[data-theme='dark'] .rn-segmented),
:global(html[data-theme='dark'] .rn-event) {
  box-shadow: 0 22px 48px rgba(2, 6, 23, 0.28) !important;
}

:global(html[data-theme='dark'] .rn-toggle) {
  background: rgba(51, 65, 85, 0.92) !important;
  border-color: #475569 !important;
}

:global(html[data-theme='dark'] .rn-toggle > span:not(.rn-spinner)) {
  background: #cbd5e1 !important;
  box-shadow: 0 6px 14px rgba(2, 6, 23, 0.38) !important;
}

:global(html[data-theme='dark'] .rn-toggle.active) {
  background: linear-gradient(135deg, #2563eb, #0f766e) !important;
  border-color: rgba(96, 165, 250, 0.32) !important;
}

:global(html[data-theme='dark'] .rn-tags .accent) {
  background: rgba(20, 184, 166, 0.16) !important;
  color: #5eead4 !important;
}

:global(html[data-theme='dark'] .rn-delete) {
  background: rgba(248, 113, 113, 0.14) !important;
  color: #fca5a5 !important;
}

:global(html[data-theme='dark'] .rn-delete:hover) {
  background: rgba(248, 113, 113, 0.22) !important;
}

:global(html[data-theme='dark'] .rn-segmented button.active) {
  background: rgba(15, 23, 42, 0.98) !important;
  border-color: rgba(96, 165, 250, 0.28) !important;
  color: #93c5fd !important;
  box-shadow: 0 8px 18px rgba(2, 6, 23, 0.34) !important;
}

:global(html[data-theme='dark'] .rn-event.active) {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.24), rgba(15, 118, 110, 0.18)) !important;
  border-color: rgba(96, 165, 250, 0.34) !important;
}

:global(html[data-theme='dark'] .rn-event-marker) {
  background: #334155 !important;
}

:global(html[data-theme='dark'] .rn-form select) {
  background: rgba(15, 23, 42, 0.96) !important;
  border-color: #334155 !important;
  color: #e2e8f0 !important;
}

:global(html[data-theme='dark'] .rn-form select option) {
  background: #0f172a !important;
  color: #e2e8f0 !important;
}
</style>
