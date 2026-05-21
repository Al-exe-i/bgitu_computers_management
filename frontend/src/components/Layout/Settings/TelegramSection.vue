<script>
import { useAuthStore } from "@/stores/auth";
import { useNotificationsStore } from "@/stores/notifications";
import {
  createTelegramLinkToken,
  createTelegramSubscription as createTelegramSubscriptionRequest,
  deleteTelegramSubscription as deleteTelegramSubscriptionRequest,
  getTelegramAudiencesDictionary,
  getTelegramOfficesDictionary,
  getTelegramStatus,
  getTelegramSubscriptions,
  unlinkTelegramAccount
} from "@/services/telegram";

export default {
  name: "TelegramSection",

  props: {
    showHeader: {
      type: Boolean,
      default: true
    }
  },

  data() {
    return {
      telegramStatus: null,
      telegramSubscriptions: [],
      offices: [],
      audiences: [],
      telegramLoading: true,
      subscriptionsLoading: false,
      dictionariesLoading: false,
      telegramError: "",
      linkPending: false,
      linkActionLoading: false,
      unlinkLoading: false,
      securitySubscriptionLoading: false,
      linkPollTimer: null,
      lastLinkInfo: null,
      subscriptionMutationKeys: [],
      deletingSubscriptionIds: [],
      subscriptionForm: {
        scope_type: "audience",
        scope_id: null,
        delivery_mode: "immediate"
      }
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

    isTelegramConnected() {
      return !!this.telegramStatus?.telegram_id_confirmed;
    },

    isTelegramAwaitingConfirmation() {
      return !this.isTelegramConnected && (
        this.linkPending ||
        (!!this.telegramStatus?.telegram_id && !this.telegramStatus?.telegram_id_confirmed)
      );
    },

    telegramStatusClass() {
      if (this.isTelegramConnected) return "is-connected";
      if (this.isTelegramAwaitingConfirmation) return "is-pending";
      return "is-idle";
    },

    telegramStatusLabel() {
      if (this.isTelegramConnected) return "Telegram подключён";
      if (this.isTelegramAwaitingConfirmation) return "Ожидаем подтверждения в Telegram";
      return "Telegram не подключён";
    },

    telegramStatusDescription() {
      if (this.isTelegramConnected) {
        return "Уведомления по выбранным корпусам и аудиториям будут приходить в ваш Telegram.";
      }

      if (this.isTelegramAwaitingConfirmation) {
        return "Откройте бота и подтвердите привязку. Статус обновится автоматически без перезагрузки страницы.";
      }

      return "Подключите Telegram, чтобы получать уведомления о неисправности и восстановлении оборудования.";
    },

    scopeOptions() {
      return [
        { value: "audience", label: "Аудитория" },
        { value: "office", label: "Корпус" }
      ];
    },

    eventOptions() {
      return [
        { value: "hardware_fault", label: "Неисправность оборудования" },
        { value: "hardware_recovered", label: "Восстановление оборудования" }
      ];
    },

    activeScopeItems() {
      return this.subscriptionForm.scope_type === "office" ? this.offices : this.audiences;
    },

    scopePlaceholder() {
      if (this.dictionariesLoading) {
        return "Загрузка списка...";
      }

      return this.subscriptionForm.scope_type === "office"
        ? "Выберите корпус"
        : "Выберите аудиторию";
    },

    canManageSelectedScopeEvents() {
      return this.isTelegramConnected &&
        this.subscriptionForm.scope_id !== null &&
        this.subscriptionForm.scope_id !== "";
    },

    securitySubscription() {
      if (!this.currentUserId) return null;

      return this.telegramSubscriptions.find((subscription) =>
        subscription.scope_type === "user" &&
        subscription.event_type === "auth_security" &&
        Number(subscription.scope_id) === this.currentUserId
      ) || null;
    },

    hasSecuritySubscription() {
      return !!this.securitySubscription;
    },

    displaySubscriptions() {
      return this.telegramSubscriptions.filter((subscription) =>
        !(
          subscription.scope_type === "user" &&
          subscription.event_type === "auth_security"
        )
      );
    },

    sortedSubscriptions() {
      return [...this.displaySubscriptions].sort((left, right) => {
        const leftTime = new Date(left.created_at || 0).getTime();
        const rightTime = new Date(right.created_at || 0).getTime();

        if (leftTime !== rightTime) {
          return rightTime - leftTime;
        }

        return (right.id || 0) - (left.id || 0);
      });
    },

    linkExpiresLabel() {
      return this.lastLinkInfo?.expires_at
        ? this.formatDateTime(this.lastLinkInfo.expires_at)
        : "";
    },

    securitySubscriptionDescription() {
      if (this.hasSecuritySubscription) {
        return "Уведомления о входах, завершении сессий и других событиях безопасности уже приходят в Telegram.";
      }

      return "Получайте уведомления о входах, завершении сессий и других событиях безопасности аккаунта.";
    },

    selectedScopeDisplayLabel() {
      if (!this.canManageSelectedScopeEvents) return "";

      const activeItem = this.activeScopeItems.find(
        (item) => Number(item.id) === Number(this.subscriptionForm.scope_id)
      );

      if (!activeItem) return "";

      return this.subscriptionForm.scope_type === "office"
        ? this.getOfficeLabel(activeItem)
        : this.getAudienceLabel(activeItem);
    }
  },

  watch: {
    "subscriptionForm.scope_type"() {
      this.subscriptionForm.scope_id = null;
    }
  },

  methods: {
    getTelegramErrorMessage(error, fallbackMessage) {
      const status = error?.response?.status;
      const detail = error?.response?.data?.detail;
      const message = typeof detail === "string" ? detail : "";

      if (error?.code === "ECONNABORTED") {
        return "Сервер Telegram не ответил вовремя. Повторите действие ещё раз.";
      }

      if (!error?.response) {
        return "Не удалось связаться с сервером. Проверьте подключение и повторите попытку.";
      }

      if (status === 401) {
        return "Необходимо повторно войти в систему.";
      }

      if (status === 403) {
        return "Недостаточно прав для работы с Telegram-настройками.";
      }

      if (status === 404) {
        return "Запрошенные Telegram-данные не найдены.";
      }

      if (status === 409) {
        if (message.toLowerCase().includes("already exists")) {
          return "Такая подписка уже существует.";
        }

        return "Это действие нельзя выполнить в текущем состоянии.";
      }

      if (status === 422) {
        return "Проверьте заполнение формы Telegram-подписки.";
      }

      if (message) {
        return message;
      }

      return fallbackMessage;
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
      if (!office) return "Корпус";

      if (office.address) {
        return `Корпус №${office.id} • ${office.address}`;
      }

      return `Корпус №${office.id}`;
    },

    getAudienceLabel(audience) {
      if (!audience) return "Аудитория";

      const parts = [`Аудитория №${audience.id}`];

      if (audience.office_id !== null && audience.office_id !== undefined) {
        parts.push(`корпус ${audience.office_id}`);
      }

      if (audience.floor !== null && audience.floor !== undefined && audience.floor !== "") {
        parts.push(`${audience.floor} этаж`);
      }

      return parts.join(" • ");
    },

    getScopeTypeLabel(scopeType) {
      return scopeType === "office" ? "Корпус" : "Аудитория";
    },

    getEventTypeLabel(eventType) {
      if (eventType === "auth_security") {
        return "Безопасность аккаунта";
      }

      if (eventType === "hardware_recovered") {
        return "Восстановление оборудования";
      }

      return "Неисправность оборудования";
    },

    getEventTypeDescription(eventType) {
      if (eventType === "hardware_recovered") {
        return "Сообщение, когда оборудование снова исправно.";
      }

      return "Сообщение, когда оборудование переходит в неисправное состояние.";
    },

    getSubscriptionKey(scopeType, scopeId, eventType) {
      return `${scopeType}:${Number(scopeId)}:${eventType}`;
    },

    findSubscription(scopeType, scopeId, eventType) {
      if (scopeId === null || scopeId === undefined || scopeId === "") {
        return null;
      }

      return this.displaySubscriptions.find((subscription) =>
        subscription.scope_type === scopeType &&
        Number(subscription.scope_id) === Number(scopeId) &&
        subscription.event_type === eventType
      ) || null;
    },

    isSelectedScopeEventEnabled(eventType) {
      return !!this.findSubscription(
        this.subscriptionForm.scope_type,
        this.subscriptionForm.scope_id,
        eventType
      );
    },

    isSelectedScopeEventBusy(eventType) {
      if (!this.canManageSelectedScopeEvents) return false;

      return this.subscriptionMutationKeys.includes(
        this.getSubscriptionKey(
          this.subscriptionForm.scope_type,
          this.subscriptionForm.scope_id,
          eventType
        )
      );
    },

    getSubscriptionScopeLabel(subscription) {
      if (subscription.scope_type === "user") {
        return "Безопасность аккаунта";
      }

      if (subscription.scope_type === "office") {
        const office = this.offices.find((item) => item.id === subscription.scope_id);
        return office ? this.getOfficeLabel(office) : `Корпус №${subscription.scope_id}`;
      }

      const audience = this.audiences.find((item) => item.id === subscription.scope_id);
      return audience ? this.getAudienceLabel(audience) : `Аудитория №${subscription.scope_id}`;
    },

    async initializeTelegram() {
      this.telegramLoading = true;
      this.telegramError = "";

      try {
        const status = await this.loadTelegramStatus({ silent: true });

        if (status?.telegram_id_confirmed) {
          await Promise.all([
            this.loadTelegramSubscriptions({ silent: true }),
            this.loadTelegramDictionaries({ silent: true })
          ]);
        } else if (status?.telegram_id && !status?.telegram_id_confirmed) {
          this.linkPending = true;
          this.startTelegramStatusPolling();
        }
      } catch (error) {
        this.telegramError = this.getTelegramErrorMessage(
          error,
          "Не удалось загрузить настройки Telegram."
        );
      } finally {
        this.telegramLoading = false;
      }
    },

    async loadTelegramStatus({ silent = false } = {}) {
      try {
        const response = await getTelegramStatus();
        const status = response.data || {};

        this.telegramStatus = {
          telegram_id: status.telegram_id || null,
          telegram_id_confirmed: !!status.telegram_id_confirmed
        };

        if (this.telegramStatus.telegram_id_confirmed) {
          this.linkPending = false;
        }

        if (!silent) {
          this.telegramError = "";
        }

        return this.telegramStatus;
      } catch (error) {
        if (!silent) {
          this.telegramError = this.getTelegramErrorMessage(
            error,
            "Не удалось загрузить статус Telegram."
          );
        }

        throw error;
      }
    },

    async loadTelegramSubscriptions({ silent = false } = {}) {
      this.subscriptionsLoading = true;

      try {
        const response = await getTelegramSubscriptions();
        this.telegramSubscriptions = Array.isArray(response.data) ? response.data : [];
      } catch (error) {
        if (!silent) {
          const message = this.getTelegramErrorMessage(
            error,
            "Не удалось загрузить Telegram-подписки."
          );
          this.telegramError = message;
          this.notify.error(message);
        }

        throw error;
      } finally {
        this.subscriptionsLoading = false;
      }
    },

    async loadTelegramDictionaries({ silent = false } = {}) {
      this.dictionariesLoading = true;

      try {
        const [officesResponse, audiencesResponse] = await Promise.all([
          getTelegramOfficesDictionary(),
          getTelegramAudiencesDictionary()
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
      } catch (error) {
        if (!silent) {
          const message = this.getTelegramErrorMessage(
            error,
            "Не удалось загрузить справочники Telegram."
          );
          this.telegramError = message;
          this.notify.error(message);
        }

        throw error;
      } finally {
        this.dictionariesLoading = false;
      }
    },

    openTelegramLink() {
      if (this.lastLinkInfo?.bot_deep_link) {
        window.open(this.lastLinkInfo.bot_deep_link, "_blank", "noopener,noreferrer");
        return;
      }

      if (this.lastLinkInfo?.bot_username) {
        window.open(
          `https://t.me/${this.lastLinkInfo.bot_username}`,
          "_blank",
          "noopener,noreferrer"
        );
      }
    },

    async startTelegramLink() {
      if (this.linkActionLoading || this.unlinkLoading) return;

      this.linkActionLoading = true;
      this.telegramError = "";

      const pendingWindow = window.open("about:blank", "_blank");

      if (pendingWindow) {
        try {
          pendingWindow.opener = null;
        } catch (error) {
          // В части браузеров это свойство защищено.
        }
      }

      try {
        const response = await createTelegramLinkToken();
        this.lastLinkInfo = response.data || null;
        this.linkPending = true;

        if (this.lastLinkInfo?.bot_deep_link) {
          if (pendingWindow) {
            pendingWindow.location.replace(this.lastLinkInfo.bot_deep_link);
          }
        } else if (this.lastLinkInfo?.bot_username) {
          const fallbackLink = `https://t.me/${this.lastLinkInfo.bot_username}`;

          if (pendingWindow) {
            pendingWindow.location.replace(fallbackLink);
          }
        } else if (pendingWindow) {
          pendingWindow.close();
        }

        this.startTelegramStatusPolling();
        this.notify.info("Подтвердите привязку в Telegram.");
      } catch (error) {
        if (pendingWindow) {
          pendingWindow.close();
        }

        this.linkPending = false;
        const message = this.getTelegramErrorMessage(
          error,
          "Не удалось начать привязку Telegram."
        );
        this.telegramError = message;
        this.notify.error(message);
      } finally {
        this.linkActionLoading = false;
      }
    },

    startTelegramStatusPolling() {
      this.stopTelegramStatusPolling();

      this.linkPollTimer = window.setInterval(async () => {
        if (!this.linkPending) return;

        if (this.lastLinkInfo?.expires_at) {
          const expiresAt = new Date(this.lastLinkInfo.expires_at).getTime();

          if (Number.isFinite(expiresAt) && expiresAt <= Date.now()) {
            this.linkPending = false;
            this.stopTelegramStatusPolling();
            this.notify.warning("Срок действия ссылки истёк. Запросите новую привязку.");
            return;
          }
        }

        try {
          const status = await this.loadTelegramStatus({ silent: true });

          if (status?.telegram_id_confirmed) {
            this.linkPending = false;
            this.stopTelegramStatusPolling();

            await Promise.all([
              this.loadTelegramSubscriptions({ silent: true }),
              this.loadTelegramDictionaries({ silent: true })
            ]);

            this.notify.success("Telegram успешно подключён.");
          }
        } catch (error) {
          // Во время polling не показываем уведомления на каждый временный сбой.
        }
      }, 2500);
    },

    stopTelegramStatusPolling() {
      if (!this.linkPollTimer) return;

      clearInterval(this.linkPollTimer);
      this.linkPollTimer = null;
    },

    async unlinkTelegram() {
      if (this.unlinkLoading || this.linkActionLoading) return;

      this.unlinkLoading = true;
      this.telegramError = "";

      try {
        await unlinkTelegramAccount();

        this.stopTelegramStatusPolling();
        this.linkPending = false;
        this.lastLinkInfo = null;
        this.telegramStatus = {
          telegram_id: null,
          telegram_id_confirmed: false
        };
        this.telegramSubscriptions = [];
        this.subscriptionForm.scope_id = null;

        this.notify.info("Telegram успешно отвязан.");
      } catch (error) {
        const message = this.getTelegramErrorMessage(
          error,
          "Не удалось отвязать Telegram."
        );
        this.telegramError = message;
        this.notify.error(message);
      } finally {
        this.unlinkLoading = false;
      }
    },

    async toggleSecuritySubscription() {
      if (!this.currentUserId || this.securitySubscriptionLoading) return;

      this.securitySubscriptionLoading = true;
      this.telegramError = "";

      try {
        if (this.securitySubscription?.id) {
          const securitySubscriptionId = this.securitySubscription.id;
          await deleteTelegramSubscriptionRequest(securitySubscriptionId);
          this.telegramSubscriptions = this.telegramSubscriptions.filter(
            (item) => item.id !== securitySubscriptionId
          );
          this.notify.info("Уведомления безопасности в Telegram отключены.");
        } else {
          await createTelegramSubscriptionRequest({
            scope_type: "user",
            scope_id: this.currentUserId,
            event_type: "auth_security",
            delivery_mode: "immediate"
          });

          await this.loadTelegramSubscriptions({ silent: true });
          this.notify.success("Уведомления безопасности в Telegram включены.");
        }
      } catch (error) {
        const message = this.getTelegramErrorMessage(
          error,
          "Не удалось изменить Telegram-подписку на события безопасности."
        );
        this.telegramError = message;
        this.notify.error(message);
      } finally {
        this.securitySubscriptionLoading = false;
      }
    },

    async toggleSelectedScopeEvent(eventType) {
      if (!this.canManageSelectedScopeEvents) return;

      const scopeType = this.subscriptionForm.scope_type;
      const scopeId = Number(this.subscriptionForm.scope_id);
      const loadingKey = this.getSubscriptionKey(scopeType, scopeId, eventType);

      if (this.subscriptionMutationKeys.includes(loadingKey)) return;

      this.subscriptionMutationKeys = [...this.subscriptionMutationKeys, loadingKey];
      this.telegramError = "";

      try {
        const existingSubscription = this.findSubscription(scopeType, scopeId, eventType);

        if (existingSubscription?.id) {
          await deleteTelegramSubscriptionRequest(existingSubscription.id);
        } else {
          await createTelegramSubscriptionRequest({
            scope_type: scopeType,
            scope_id: scopeId,
            event_type: eventType,
            delivery_mode: "immediate"
          });
        }

        await this.loadTelegramSubscriptions({ silent: true });

        const eventLabel = this.getEventTypeLabel(eventType);
        if (existingSubscription?.id) {
          this.notify.info(`Подписка «${eventLabel}» отключена.`);
        } else {
          this.notify.success(`Подписка «${eventLabel}» включена.`);
        }
      } catch (error) {
        const message = this.getTelegramErrorMessage(
          error,
          "Не удалось обновить Telegram-подписку."
        );
        this.telegramError = message;
        this.notify.error(message);
      } finally {
        this.subscriptionMutationKeys = this.subscriptionMutationKeys.filter(
          (item) => item !== loadingKey
        );
      }
    },

    async deleteTelegramSubscriptionById(id) {
      if (this.deletingSubscriptionIds.includes(id)) return;

      this.deletingSubscriptionIds = [...this.deletingSubscriptionIds, id];
      this.telegramError = "";

      try {
        await deleteTelegramSubscriptionRequest(id);
        this.telegramSubscriptions = this.telegramSubscriptions.filter((item) => item.id !== id);
        this.notify.info("Подписка Telegram удалена.");
      } catch (error) {
        const message = this.getTelegramErrorMessage(
          error,
          "Не удалось удалить Telegram-подписку."
        );
        this.telegramError = message;
        this.notify.error(message);
      } finally {
        this.deletingSubscriptionIds = this.deletingSubscriptionIds.filter((item) => item !== id);
      }
    }
  },

  async mounted() {
    await this.initializeTelegram();
  },

  beforeUnmount() {
    this.stopTelegramStatusPolling();
  }
};
</script>

<template>
  <section class="telegram-section" :class="{ 'is-embedded': !showHeader }">
    <div v-if="showHeader" class="telegram-section-header">
      <div>
        <h3 class="telegram-section-title">Telegram</h3>
        <p class="telegram-section-subtitle">
          Настройте привязку Telegram и подписки на события по оборудованию.
        </p>
      </div>
    </div>

    <div v-if="telegramError" class="telegram-alert">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <span>{{ telegramError }}</span>
    </div>

    <div v-if="telegramLoading" class="telegram-loading-state">
      <span class="telegram-spinner"></span>
      <span>Загрузка Telegram-настроек...</span>
    </div>

    <template v-else>
      <div class="telegram-status-card" :class="telegramStatusClass">
        <div class="telegram-status-main">
          <div class="telegram-status-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="m20.665 3.717l-17.73 6.837c-1.21.486-1.203 1.161-.222 1.462l4.552 1.42l10.532-6.645c.498-.303.953-.14.579.192l-8.533 7.701h-.002l.002.001l-.314 4.692c.46 0 .663-.211.921-.46l2.211-2.15l4.599 3.397c.848.467 1.457.227 1.668-.785l3.019-14.228c.309-1.239-.473-1.8-1.282-1.434"/></svg>
          </div>

          <div class="telegram-status-copy">
            <div class="telegram-status-topline">
              <span class="telegram-status-pill" :class="telegramStatusClass">
                {{ telegramStatusLabel }}
              </span>
              <span v-if="telegramStatus?.telegram_id" class="telegram-status-id">
                ID {{ telegramStatus.telegram_id }}
              </span>
            </div>

            <h4 class="telegram-status-title">{{ telegramStatusLabel }}</h4>
            <p class="telegram-status-text">{{ telegramStatusDescription }}</p>

            <div
              v-if="isTelegramAwaitingConfirmation && linkExpiresLabel"
              class="telegram-status-note"
            >
              Ссылка действует до {{ linkExpiresLabel }}
            </div>
          </div>
        </div>

        <div class="telegram-status-actions">
          <button
            v-if="!isTelegramConnected"
            type="button"
            class="telegram-primary-btn"
            :disabled="linkActionLoading || unlinkLoading"
            @click="startTelegramLink"
          >
            <span v-if="linkActionLoading" class="telegram-spinner small"></span>
            {{ linkActionLoading ? "Подготовка..." : "Подключить Telegram" }}
          </button>

          <button
            v-if="isTelegramAwaitingConfirmation && (lastLinkInfo?.bot_deep_link || lastLinkInfo?.bot_username)"
            type="button"
            class="telegram-secondary-btn"
            :disabled="linkActionLoading"
            @click="openTelegramLink"
          >
            Открыть бота
          </button>

          <button
            v-if="isTelegramConnected"
            type="button"
            class="telegram-secondary-btn is-danger"
            :disabled="unlinkLoading || linkActionLoading"
            @click="unlinkTelegram"
          >
            <span v-if="unlinkLoading" class="telegram-spinner small danger"></span>
            {{ unlinkLoading ? "Отвязка..." : "Отвязать" }}
          </button>
        </div>
      </div>

      <div v-if="isTelegramAwaitingConfirmation" class="telegram-waiting-card">
        <div class="telegram-waiting-head">
          <strong>Ожидаем подтверждения в Telegram</strong>
          <span v-if="lastLinkInfo?.bot_username">@{{ lastLinkInfo.bot_username }}</span>
        </div>
        <p>
          Как только вы подтвердите привязку в боте, статус обновится автоматически, и форма
          подписок станет доступна.
        </p>
      </div>

      <div v-if="isTelegramConnected" class="telegram-security-card">
        <div class="telegram-security-copy">
          <div class="telegram-security-label">Безопасность аккаунта</div>
          <h4 class="telegram-security-title">Уведомления о событиях безопасности</h4>
          <p class="telegram-security-text">{{ securitySubscriptionDescription }}</p>
          <p
            v-if="hasSecuritySubscription && securitySubscription?.created_at"
            class="telegram-security-meta"
          >
            Активно с {{ formatDateTime(securitySubscription.created_at) }}
          </p>
        </div>

        <button
          type="button"
          class="telegram-security-toggle"
          :class="{ active: hasSecuritySubscription }"
          :disabled="securitySubscriptionLoading || !currentUserId"
          :aria-pressed="hasSecuritySubscription"
          @click="toggleSecuritySubscription"
        >
          <span v-if="securitySubscriptionLoading" class="telegram-spinner small"></span>
          <span v-else class="telegram-security-toggle-thumb"></span>
        </button>
      </div>

      <div v-if="isTelegramConnected" class="telegram-layout">
        <div class="telegram-panel">
          <div class="telegram-panel-head">
            <div>
              <h4 class="telegram-panel-title">Подписки</h4>
              <p class="telegram-panel-subtitle">
                Активные уведомления о состоянии оборудования.
              </p>
            </div>
            <span class="telegram-counter">{{ displaySubscriptions.length }}</span>
          </div>

          <div v-if="subscriptionsLoading" class="telegram-loading-state compact">
            <span class="telegram-spinner"></span>
            <span>Загрузка подписок...</span>
          </div>

          <div v-else-if="sortedSubscriptions.length" class="telegram-subscriptions">
            <article
              v-for="subscription in sortedSubscriptions"
              :key="subscription.id"
              class="telegram-subscription-item"
            >
              <div class="telegram-subscription-content">
                <div class="telegram-subscription-tags">
                  <span class="telegram-tag">
                    {{ getScopeTypeLabel(subscription.scope_type) }}
                  </span>
                  <span class="telegram-tag accent">
                    {{ getEventTypeLabel(subscription.event_type) }}
                  </span>
                </div>
                <h5 class="telegram-subscription-title">
                  {{ getSubscriptionScopeLabel(subscription) }}
                </h5>
                <p class="telegram-subscription-meta">
                  Сразу после события • {{ formatDateTime(subscription.created_at) }}
                </p>
              </div>

              <button
                type="button"
                class="telegram-remove-btn"
                :title="deletingSubscriptionIds.includes(subscription.id) ? 'Удаление подписки' : 'Удалить подписку'"
                :aria-label="deletingSubscriptionIds.includes(subscription.id) ? 'Удаление подписки' : 'Удалить подписку'"
                :disabled="deletingSubscriptionIds.includes(subscription.id)"
                @click="deleteTelegramSubscriptionById(subscription.id)"
              >
                <span
                  v-if="deletingSubscriptionIds.includes(subscription.id)"
                  class="telegram-spinner small danger"
                ></span>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40"><path fill="currentColor" d="M21.499 19.994L32.755 8.727a1.064 1.064 0 0 0-.001-1.502c-.398-.396-1.099-.398-1.501.002L20 18.494L8.743 7.224c-.4-.395-1.101-.393-1.499.002a1.05 1.05 0 0 0-.309.751c0 .284.11.55.309.747L18.5 19.993L7.245 31.263a1.064 1.064 0 0 0 .003 1.503c.193.191.466.301.748.301h.006c.283-.001.556-.112.745-.305L20 21.495l11.257 11.27c.199.198.465.308.747.308a1.06 1.06 0 0 0 1.061-1.061c0-.283-.11-.55-.31-.747z"/></svg>
              </button>
            </article>
          </div>

          <div v-else class="telegram-empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <div>
              <strong>Подписок пока нет</strong>
              <span>Добавьте первую подписку на аудиторию или корпус.</span>
            </div>
          </div>
        </div>

        <div class="telegram-panel">
          <div class="telegram-panel-head">
            <div>
              <h4 class="telegram-panel-title">Добавить подписку</h4>
              <p class="telegram-panel-subtitle">
                Доступны уведомления по аудиториям и корпусам.
              </p>
            </div>
          </div>

          <div class="telegram-form">
            <div class="telegram-form-group">
              <label>Тип подписки</label>
              <div class="telegram-segmented">
                <button
                  v-for="option in scopeOptions"
                  :key="option.value"
                  type="button"
                  class="telegram-segmented-btn"
                  :class="{ active: subscriptionForm.scope_type === option.value }"
                  @click="subscriptionForm.scope_type = option.value"
                >
                  {{ option.label }}
                </button>
              </div>
            </div>

            <div class="telegram-form-group">
              <label>
                {{ subscriptionForm.scope_type === "office" ? "Корпус" : "Аудитория" }}
              </label>
              <select
                v-model.number="subscriptionForm.scope_id"
                class="telegram-select"
                :disabled="dictionariesLoading || !activeScopeItems.length"
              >
                <option :value="null">{{ scopePlaceholder }}</option>
                <option
                  v-for="item in activeScopeItems"
                  :key="item.id"
                  :value="item.id"
                >
                  {{
                    subscriptionForm.scope_type === "office"
                      ? getOfficeLabel(item)
                      : getAudienceLabel(item)
                  }}
                </option>
              </select>
            </div>

            <div class="telegram-form-group">
              <label>События</label>
              <div class="telegram-event-grid">
                <label
                  v-for="option in eventOptions"
                  :key="option.value"
                  class="telegram-event-card"
                  :class="{
                    active: isSelectedScopeEventEnabled(option.value),
                    disabled: !canManageSelectedScopeEvents,
                    loading: isSelectedScopeEventBusy(option.value)
                  }"
                >
                  <input
                    type="checkbox"
                    class="telegram-event-checkbox"
                    :checked="isSelectedScopeEventEnabled(option.value)"
                    :disabled="!canManageSelectedScopeEvents || isSelectedScopeEventBusy(option.value)"
                    @change="toggleSelectedScopeEvent(option.value)"
                  >
                  <span class="telegram-event-marker">
                    <span
                      v-if="isSelectedScopeEventBusy(option.value)"
                      class="telegram-spinner small"
                    ></span>
                    <svg
                      v-else-if="isSelectedScopeEventEnabled(option.value)"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2.4"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                  </span>
                  <span class="telegram-event-copy">
                    <strong>{{ option.label }}</strong>
                    <span>{{ getEventTypeDescription(option.value) }}</span>
                  </span>
                </label>
              </div>
            </div>

            <div class="telegram-inline-note" :class="{ muted: !canManageSelectedScopeEvents }">
              <template v-if="canManageSelectedScopeEvents">
                Изменения применяются сразу для: {{ selectedScopeDisplayLabel }}.
              </template>
              <template v-else>
                Сначала выберите аудиторию или корпус, затем отметьте нужные события.
              </template>
            </div>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.telegram-section {
  --telegram-divider: #e2e8f0;
  --telegram-soft-bg: #f8fafc;
  --telegram-soft-bg-strong: #ffffff;
  --telegram-soft-border: #e2e8f0;
  --telegram-text-main: #0f172a;
  --telegram-text-secondary: #64748b;
  --telegram-shadow: 0 18px 30px rgba(15, 23, 42, 0.06);
  --telegram-pill-bg: #e2e8f0;
  --telegram-pill-text: #334155;
  margin-top: 32px;
  padding-top: 28px;
  border-top: 1px solid var(--telegram-divider);
}

.telegram-section.is-embedded {
  margin-top: 0;
  padding-top: 0;
  border-top: none;
}

.telegram-section-header {
  margin-bottom: 18px;
}

.telegram-section-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--telegram-text-main);
}

.telegram-section-subtitle {
  margin: 6px 0 0;
  font-size: 14px;
  line-height: 1.55;
  color: var(--telegram-text-secondary);
}

.telegram-alert {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  margin-bottom: 16px;
  border-radius: 12px;
  border: 1px solid rgba(248, 113, 113, 0.28);
  background: rgba(254, 242, 242, 0.96);
  color: #b91c1c;
  font-size: 13px;
}

.telegram-alert svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.telegram-loading-state {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--telegram-text-secondary);
  font-size: 14px;
}

.telegram-loading-state.compact {
  min-height: 120px;
}

.telegram-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(59, 130, 246, 0.2);
  border-radius: 50%;
  border-top-color: #2563eb;
  animation: telegram-spin 0.75s linear infinite;
}

.telegram-spinner.small {
  width: 14px;
  height: 14px;
}

.telegram-spinner.danger {
  border-color: rgba(239, 68, 68, 0.16);
  border-top-color: #dc2626;
}

.telegram-status-card {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  padding: 20px;
  border-radius: 18px;
  border: 1px solid var(--telegram-soft-border);
  background: linear-gradient(180deg, var(--telegram-soft-bg), var(--telegram-soft-bg-strong));
  box-shadow: var(--telegram-shadow);
}

.telegram-status-card.is-connected {
  background:
    radial-gradient(circle at top right, rgba(34, 197, 94, 0.16), transparent 34%),
    linear-gradient(180deg, var(--telegram-soft-bg), var(--telegram-soft-bg-strong));
}

.telegram-status-card.is-pending {
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.16), transparent 34%),
    linear-gradient(180deg, var(--telegram-soft-bg), var(--telegram-soft-bg-strong));
}

.telegram-status-main {
  min-width: 0;
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.telegram-status-icon {
  width: 54px;
  height: 54px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.14), rgba(14, 165, 233, 0.12));
  color: #2563eb;
}

.telegram-status-icon svg {
  width: 26px;
  height: 26px;
}

.telegram-status-copy {
  min-width: 0;
}

.telegram-status-topline {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.telegram-status-pill,
.telegram-status-id,
.telegram-counter,
.telegram-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.telegram-status-pill,
.telegram-status-id,
.telegram-counter,
.telegram-tag {
  background: var(--telegram-pill-bg);
  color: var(--telegram-pill-text);
}

.telegram-status-pill.is-connected {
  background: rgba(34, 197, 94, 0.14);
  color: #15803d;
}

.telegram-status-pill.is-pending {
  background: rgba(59, 130, 246, 0.14);
  color: #1d4ed8;
}

.telegram-status-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--telegram-text-main);
}

.telegram-status-text,
.telegram-status-note,
.telegram-panel-subtitle,
.telegram-subscription-meta,
.telegram-inline-note,
.telegram-waiting-card p {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--telegram-text-secondary);
}

.telegram-status-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
  align-items: flex-start;
}

.telegram-primary-btn,
.telegram-secondary-btn,
.telegram-remove-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 42px;
  padding: 0 16px;
  border-radius: 12px;
  border: 1px solid transparent;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.telegram-primary-btn {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #ffffff;
  box-shadow: 0 14px 24px rgba(37, 99, 235, 0.2);
}

.telegram-primary-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 18px 28px rgba(37, 99, 235, 0.24);
}

.telegram-secondary-btn {
  background: rgba(255, 255, 255, 0.82);
  border-color: var(--telegram-soft-border);
  color: #334155;
}

.telegram-secondary-btn:hover:not(:disabled) {
  background: #ffffff;
}

.telegram-secondary-btn.is-danger,
.telegram-remove-btn {
  background: rgba(254, 242, 242, 0.96);
  border-color: rgba(248, 113, 113, 0.2);
  color: #b91c1c;
}

.telegram-secondary-btn.is-danger:hover:not(:disabled),
.telegram-remove-btn:hover:not(:disabled) {
  background: rgba(254, 226, 226, 0.98);
}

.telegram-primary-btn:disabled,
.telegram-secondary-btn:disabled,
.telegram-remove-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

.telegram-waiting-card,
.telegram-panel {
  margin-top: 16px;
  padding: 18px;
  border-radius: 16px;
  border: 1px solid var(--telegram-soft-border);
  background: var(--telegram-soft-bg);
}

.telegram-waiting-head,
.telegram-panel-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.telegram-waiting-head strong,
.telegram-panel-title,
.telegram-subscription-title,
.telegram-empty-state strong {
  color: var(--telegram-text-main);
}

.telegram-security-card {
  margin-top: 16px;
  padding: 18px;
  border-radius: 16px;
  border: 1px solid var(--telegram-soft-border);
  background:
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.08), transparent 30%),
    var(--telegram-soft-bg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.telegram-security-copy {
  min-width: 0;
}

.telegram-security-label {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  background: var(--telegram-pill-bg);
  color: var(--telegram-pill-text);
  font-size: 11px;
  font-weight: 700;
}

.telegram-security-title {
  margin: 10px 0 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--telegram-text-main);
}

.telegram-security-text,
.telegram-security-meta {
  margin: 6px 0 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--telegram-text-secondary);
}

.telegram-security-meta {
  font-size: 12px;
}

.telegram-security-toggle {
  position: relative;
  flex-shrink: 0;
  width: 58px;
  height: 34px;
  padding: 4px;
  border: 1px solid var(--telegram-soft-border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  cursor: pointer;
  transition: all 0.2s ease;
}

.telegram-security-toggle.active {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  border-color: rgba(37, 99, 235, 0.3);
  box-shadow: 0 12px 22px rgba(37, 99, 235, 0.24);
}

.telegram-security-toggle:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  box-shadow: none;
}

.telegram-security-toggle-thumb {
  display: block;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.16);
  transition: transform 0.2s ease;
}

.telegram-security-toggle.active .telegram-security-toggle-thumb {
  transform: translateX(24px);
}

.telegram-panel-title,
.telegram-subscription-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
}

.telegram-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
  gap: 16px;
  margin-top: 16px;
}

.telegram-subscriptions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: min(66vh, 560px);
  overflow-y: auto;
  padding-right: 6px;
  scrollbar-gutter: stable;
}

.telegram-subscriptions::-webkit-scrollbar {
  width: 8px;
}

.telegram-subscriptions::-webkit-scrollbar-track {
  background: transparent;
}

.telegram-subscriptions::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.45);
  border-radius: 999px;
}

.telegram-subscriptions::-webkit-scrollbar-thumb:hover {
  background: rgba(100, 116, 139, 0.7);
}

.telegram-subscription-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 32px;
  align-items: start;
  gap: 10px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid var(--telegram-soft-border);
  background: var(--telegram-soft-bg-strong);
}

.telegram-subscription-content {
  min-width: 0;
}

.telegram-subscription-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 6px;
}

.telegram-subscription-title {
  font-size: 14px;
  line-height: 1.35;
}

.telegram-subscription-meta {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.45;
}

.telegram-tag.accent {
  background: rgba(59, 130, 246, 0.12);
  color: #1d4ed8;
}

.telegram-subscription-item .telegram-tag {
  min-height: 24px;
  padding: 0 8px;
  font-size: 11px;
}

.telegram-remove-btn {
  flex-shrink: 0;
  align-self: start;
  justify-self: end;
  width: 32px;
  height: 32px;
  min-height: 32px;
  padding: 0;
  border-radius: 10px;
  line-height: 1;
  box-shadow: none;
}

.telegram-remove-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.telegram-remove-btn svg {
  width: 16px;
  height: 16px;
}

.telegram-form {
  display: grid;
  gap: 16px;
}

.telegram-form-group {
  display: grid;
  gap: 8px;
}

.telegram-form-group label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}

.telegram-segmented {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  padding: 4px;
  border-radius: 14px;
  background: var(--telegram-soft-bg-strong);
  border: 1px solid var(--telegram-soft-border);
}

.telegram-segmented-btn {
  min-height: 40px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.telegram-segmented-btn.active {
  background: rgba(59, 130, 246, 0.12);
  color: #1d4ed8;
}

.telegram-select {
  width: 100%;
  min-height: 44px;
  padding: 0 38px 0 12px;
  border-radius: 12px;
  border: 1px solid var(--telegram-soft-border);
  background-color: var(--telegram-soft-bg-strong);
  color: var(--telegram-text-main);
  font-size: 14px;
  box-sizing: border-box;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg width='12' height='8' viewBox='0 0 12 8' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1.5L6 6.5L11 1.5' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
}

.telegram-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.14);
}

.telegram-event-grid {
  display: grid;
  gap: 10px;
}

.telegram-event-card {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 13px 14px;
  border-radius: 14px;
  border: 1px solid var(--telegram-soft-border);
  background: var(--telegram-soft-bg-strong);
  cursor: pointer;
  transition: all 0.2s ease;
}

.telegram-event-card:hover:not(.disabled) {
  border-color: rgba(59, 130, 246, 0.34);
  transform: translateY(-1px);
}

.telegram-event-card.active {
  border-color: rgba(59, 130, 246, 0.34);
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.1), transparent 32%),
    var(--telegram-soft-bg-strong);
  box-shadow: 0 14px 24px rgba(37, 99, 235, 0.08);
}

.telegram-event-card.disabled {
  opacity: 0.68;
  cursor: not-allowed;
}

.telegram-event-card.loading {
  cursor: wait;
}

.telegram-event-checkbox {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.telegram-event-marker {
  width: 22px;
  height: 22px;
  margin-top: 1px;
  border-radius: 7px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #2563eb;
  transition: all 0.2s ease;
}

.telegram-event-card.active .telegram-event-marker {
  border-color: rgba(37, 99, 235, 0.4);
  background: rgba(59, 130, 246, 0.14);
}

.telegram-event-marker svg {
  width: 14px;
  height: 14px;
}

.telegram-event-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.telegram-event-copy strong {
  font-size: 13px;
  font-weight: 700;
  color: var(--telegram-text-main);
}

.telegram-event-copy span {
  font-size: 12px;
  line-height: 1.45;
  color: var(--telegram-text-secondary);
}

.telegram-inline-note {
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px dashed var(--telegram-soft-border);
  background: rgba(255, 255, 255, 0.68);
}

.telegram-inline-note.muted {
  color: var(--telegram-text-secondary);
}

.telegram-empty-state {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 16px;
  border-radius: 14px;
  border: 1px dashed var(--telegram-soft-border);
  color: var(--telegram-text-secondary);
  background: rgba(255, 255, 255, 0.55);
}

.telegram-empty-state svg {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
}

.telegram-empty-state div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

@keyframes telegram-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 860px) {
  .telegram-status-card,
  .telegram-security-card {
    flex-direction: column;
  }

  .telegram-status-actions {
    justify-content: flex-start;
  }

  .telegram-layout {
    grid-template-columns: 1fr;
  }

  .telegram-remove-btn {
    align-self: start;
    justify-self: end;
  }

  .telegram-security-toggle {
    align-self: flex-start;
  }

  .telegram-subscriptions {
    max-height: min(46vh, 360px);
  }
}

@media (max-width: 560px) {
  .telegram-section {
    margin-top: 24px;
    padding-top: 24px;
  }

  .telegram-status-card,
  .telegram-waiting-card,
  .telegram-panel {
    padding: 16px;
    border-radius: 14px;
  }

  .telegram-status-icon {
    width: 48px;
    height: 48px;
    border-radius: 14px;
  }

  .telegram-status-icon svg {
    width: 24px;
    height: 24px;
  }

  .telegram-status-title {
    font-size: 16px;
  }

  .telegram-primary-btn,
  .telegram-secondary-btn {
    width: 100%;
  }

  .telegram-remove-btn {
    width: 30px;
    height: 30px;
    min-width: 30px;
    min-height: 30px;
    border-radius: 9px;
  }

  .telegram-subscriptions {
    gap: 6px;
    max-height: min(42vh, 320px);
    padding-right: 4px;
  }

  .telegram-subscription-item {
    grid-template-columns: minmax(0, 1fr) 30px;
    gap: 8px;
    padding: 10px;
    border-radius: 10px;
  }

  .telegram-subscription-tags {
    gap: 4px;
    margin-bottom: 5px;
  }

  .telegram-subscription-item .telegram-tag {
    min-height: 21px;
    padding: 0 7px;
    font-size: 10px;
  }

  .telegram-subscription-title {
    font-size: 13px;
    line-height: 1.3;
    overflow-wrap: anywhere;
  }

  .telegram-subscription-meta {
    margin-top: 3px;
    font-size: 11px;
    line-height: 1.35;
  }

  .telegram-remove-btn svg {
    width: 14px;
    height: 14px;
  }

  .telegram-waiting-head,
  .telegram-panel-head {
    flex-direction: column;
  }
}

:global(html[data-theme='dark']) .telegram-section {
  --telegram-divider: #334155;
  --telegram-soft-bg: rgba(15, 23, 42, 0.84);
  --telegram-soft-bg-strong: rgba(15, 23, 42, 0.94);
  --telegram-soft-border: #334155;
  --telegram-text-main: #f8fafc;
  --telegram-text-secondary: #94a3b8;
  --telegram-shadow: 0 24px 42px rgba(2, 6, 23, 0.28);
  --telegram-pill-bg: rgba(30, 41, 59, 0.92);
  --telegram-pill-text: #cbd5e1;
}

:global(html[data-theme='dark']) .telegram-alert {
  background: rgba(127, 29, 29, 0.26);
  border-color: rgba(248, 113, 113, 0.2);
  color: #fecaca;
}

:global(html[data-theme='dark']) .telegram-status-icon {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.3), rgba(14, 165, 233, 0.14));
  color: #93c5fd;
}

:global(html[data-theme='dark']) .telegram-status-pill.is-connected {
  background: rgba(22, 163, 74, 0.22);
  color: #86efac;
}

:global(html[data-theme='dark']) .telegram-status-pill.is-pending,
:global(html[data-theme='dark']) .telegram-tag.accent,
:global(html[data-theme='dark']) .telegram-segmented-btn.active {
  background: rgba(37, 99, 235, 0.2);
  color: #bfdbfe;
}

:global(html[data-theme='dark']) .telegram-security-card {
  background:
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.14), transparent 30%),
    rgba(15, 23, 42, 0.9);
}

:global(html[data-theme='dark']) .telegram-security-toggle {
  background: rgba(15, 23, 42, 0.92);
  border-color: #334155;
}

:global(html[data-theme='dark']) .telegram-security-toggle-thumb {
  background: #e2e8f0;
  box-shadow: 0 6px 14px rgba(2, 6, 23, 0.34);
}

:global(html[data-theme='dark']) .telegram-secondary-btn {
  background: rgba(15, 23, 42, 0.92);
  border-color: #334155;
  color: #cbd5e1;
}

:global(html[data-theme='dark']) .telegram-secondary-btn:hover:not(:disabled) {
  background: rgba(30, 41, 59, 0.98);
  color: #f8fafc;
}

:global(html[data-theme='dark']) .telegram-secondary-btn.is-danger,
:global(html[data-theme='dark']) .telegram-remove-btn {
  background: rgba(127, 29, 29, 0.2);
  border-color: rgba(248, 113, 113, 0.16);
  color: #fda4af;
}

:global(html[data-theme='dark']) .telegram-inline-note,
:global(html[data-theme='dark']) .telegram-empty-state,
:global(html[data-theme='dark']) .telegram-subscription-item,
:global(html[data-theme='dark']) .telegram-segmented,
:global(html[data-theme='dark']) .telegram-event-card {
  background: rgba(15, 23, 42, 0.96);
}

:global(html[data-theme='dark']) .telegram-event-card.active {
  background:
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.14), transparent 32%),
    rgba(15, 23, 42, 0.96);
  border-color: rgba(96, 165, 250, 0.3);
  box-shadow: 0 16px 26px rgba(2, 6, 23, 0.22);
}

:global(html[data-theme='dark']) .telegram-event-card:hover:not(.disabled) {
  border-color: rgba(96, 165, 250, 0.3);
}

:global(html[data-theme='dark']) .telegram-event-marker {
  background: rgba(15, 23, 42, 0.92);
  border-color: #475569;
  color: #93c5fd;
}

:global(html[data-theme='dark']) .telegram-event-card.active .telegram-event-marker {
  background: rgba(37, 99, 235, 0.2);
  border-color: rgba(96, 165, 250, 0.34);
}

:global(html[data-theme='dark']) .telegram-event-copy strong {
  color: #f8fafc;
}

:global(html[data-theme='dark']) .telegram-event-copy span {
  color: #94a3b8;
}

:global(html[data-theme='dark']) .telegram-subscriptions::-webkit-scrollbar-thumb {
  background: rgba(71, 85, 105, 0.92);
}

:global(html[data-theme='dark']) .telegram-subscriptions::-webkit-scrollbar-thumb:hover {
  background: rgba(100, 116, 139, 0.96);
}

:global(html[data-theme='dark']) .telegram-form-group label {
  color: #cbd5e1;
}

:global(html[data-theme='dark']) .telegram-select {
  background-color: rgba(15, 23, 42, 0.96);
  color: #f8fafc;
  background-image: url("data:image/svg+xml,%3Csvg width='12' height='8' viewBox='0 0 12 8' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1.5L6 6.5L11 1.5' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
}
</style>
