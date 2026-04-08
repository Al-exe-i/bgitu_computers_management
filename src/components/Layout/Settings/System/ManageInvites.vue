<script>
import api from "@/services/api";
import { useNotificationsStore } from "@/stores/notifications";
import {
  INVITE_ROLE_OPTIONS,
  copyTextToClipboard,
  formatInviteDate,
  fromLocalDateTimeInputValue,
  getDefaultInviteExpiresAtValue,
  getInviteRoleLabel,
  getInviteStatus,
  getInviteStatusLabel,
  isValidEmail,
  normalizeInviteCreateResponse,
  normalizeInviteListResponse,
  normalizeInviteRoleValue,
  parseInviteEmails,
} from "@/utils/invites.js";

const ADMIN_INVITES_BASE = "/admin/invites";

function createInviteFormDefaults() {
  return {
    target_role: 2,
    note: '',
    expires_at: getDefaultInviteExpiresAtValue(),
  };
}

export default {
  name: "ManageInvites",

  data() {
    return {
      invites: [],
      loading: true,
      error: null,

      createOneLoading: false,
      createBatchLoading: false,
      processingInviteId: null,
      processingAction: '',

      createdInvites: [],

      oneForm: {
        target_email: '',
        ...createInviteFormDefaults(),
      },

      batchForm: {
        emails: '',
        ...createInviteFormDefaults(),
      },
    };
  },

  computed: {
    notify() {
      return useNotificationsStore();
    },

    roleOptions() {
      return INVITE_ROLE_OPTIONS;
    },

    hasCreatedInvites() {
      return this.createdInvites.length > 0;
    },

    activeInvitesCount() {
      return this.invites.filter(invite => this.getInviteStatus(invite) === 'active').length;
    },
  },

  methods: {
    sortInvites(items) {
      return [...items].sort((left, right) => {
        const leftTime = new Date(left.created_at ?? 0).getTime();
        const rightTime = new Date(right.created_at ?? 0).getTime();
        return rightTime - leftTime;
      });
    },

    formatDate(value) {
      return formatInviteDate(value);
    },

    getDateParts(value) {
      const formatted = this.formatDate(value);
      if (!formatted || formatted === '—') {
        return { date: '—', time: '' };
      }

      const [date = formatted, time = ''] = formatted.split(', ');
      return { date, time };
    },

    getInviteStatus(invite) {
      return getInviteStatus(invite);
    },

    getInviteStatusLabel(status) {
      return getInviteStatusLabel(status);
    },

    getInviteRoleLabel(role) {
      return getInviteRoleLabel(role);
    },

    getInviteStatusClass(invite) {
      return `status-${this.getInviteStatus(invite)}`;
    },

    getInviteMetaText(invite) {
      const status = this.getInviteStatus(invite);

      if (status === 'used') return `Использована ${this.formatDate(invite.used_at)}`;
      if (status === 'revoked') return `Отозвана ${this.formatDate(invite.revoked_at)}`;
      if (status === 'expired') return `Истекла ${this.formatDate(invite.expires_at)}`;

      return invite.expires_at ? `Действует до ${this.formatDate(invite.expires_at)}` : 'Без срока действия';
    },

    getInviteCreatedBadge(invite) {
      return invite.created_by_user_id ? `Создал ID ${invite.created_by_user_id}` : 'Создано администратором';
    },

    buildBaseInvitePayload(form) {
      const targetRole = normalizeInviteRoleValue(form.target_role);
      const payload = {
        target_role: targetRole ?? 2,
      };

      const note = String(form.note ?? '').trim();
      const expiresAt = fromLocalDateTimeInputValue(form.expires_at);

      if (note) payload.note = note;
      if (expiresAt) payload.expires_at = expiresAt;

      return payload;
    },

    buildSingleInvitePayload() {
      return {
        ...this.buildBaseInvitePayload(this.oneForm),
        target_email: this.oneForm.target_email.trim(),
      };
    },

    buildBatchInvitePayload(emails) {
      return {
        ...this.buildBaseInvitePayload(this.batchForm),
        emails: emails,
      };
    },

    resetOneForm() {
      this.oneForm = {
        target_email: '',
        ...createInviteFormDefaults(),
      };
    },

    resetBatchForm() {
      this.batchForm = {
        emails: '',
        ...createInviteFormDefaults(),
      };
    },

    async fetchInvites() {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.get(ADMIN_INVITES_BASE);
        this.invites = this.sortInvites(normalizeInviteListResponse(response.data));
      } catch (error) {
        this.error = error.response?.data?.detail || 'Не удалось загрузить invite-ссылки';
        this.notify.error(this.error);
      } finally {
        this.loading = false;
      }
    },

    async createSingleInvite() {
      const email = this.oneForm.target_email.trim();

      if (!isValidEmail(email)) {
        this.notify.warning('Введите корректный email для invite-ссылки');
        return;
      }

      this.createOneLoading = true;

      try {
        const response = await api.post(`${ADMIN_INVITES_BASE}/one`, this.buildSingleInvitePayload());
        this.createdInvites = normalizeInviteCreateResponse(response.data);
        this.notify.success('Invite-ссылка создана');
        this.resetOneForm();
        await this.fetchInvites();
      } catch (error) {
        const message = error.response?.data?.detail || 'Не удалось создать invite-ссылку';
        this.notify.error(message);
      } finally {
        this.createOneLoading = false;
      }
    },

    async createBatchInvites() {
      const emails = parseInviteEmails(this.batchForm.emails);

      if (emails.length === 0) {
        this.notify.warning('Добавьте хотя бы один email для batch invite');
        return;
      }

      const invalidEmails = emails.filter(email => !isValidEmail(email));
      if (invalidEmails.length > 0) {
        this.notify.warning(`Некорректные email: ${invalidEmails.slice(0, 3).join(', ')}`);
        return;
      }

      this.createBatchLoading = true;

      try {
        const response = await api.post(`${ADMIN_INVITES_BASE}/batch`, this.buildBatchInvitePayload(emails));
        this.createdInvites = normalizeInviteCreateResponse(response.data);
        this.notify.success(`Создано invite-ссылок: ${this.createdInvites.length}`);
        this.resetBatchForm();
        await this.fetchInvites();
      } catch (error) {
        const message = error.response?.data?.detail || 'Не удалось создать batch invite-ссылки';
        this.notify.error(message);
      } finally {
        this.createBatchLoading = false;
      }
    },

    isBusy(inviteId, action) {
      return this.processingInviteId === inviteId && this.processingAction === action;
    },

    async revokeInvite(invite) {
      if (this.getInviteStatus(invite) !== 'active') return;
      if (!confirm(`Отозвать invite для ${invite.target_email}?`)) return;

      this.processingInviteId = invite.id;
      this.processingAction = 'revoke';

      try {
        await api.post(`${ADMIN_INVITES_BASE}/${invite.id}/revoke`);
        this.invites = this.invites.map(item => (
            item.id === invite.id
                ? { ...item, revoked_at: new Date().toISOString() }
                : item
        ));
        this.notify.success('Invite-ссылка отозвана');
      } catch (error) {
        const message = error.response?.data?.detail || 'Не удалось отозвать invite-ссылку';
        this.notify.error(message);
      } finally {
        this.processingInviteId = null;
        this.processingAction = '';
      }
    },

    async deleteInvite(invite) {
      if (!confirm(`Удалить invite для ${invite.target_email}? Это действие необратимо.`)) return;

      this.processingInviteId = invite.id;
      this.processingAction = 'delete';

      try {
        await api.delete(`${ADMIN_INVITES_BASE}/${invite.id}`);
        this.invites = this.invites.filter(item => item.id !== invite.id);
        this.notify.success('Invite-ссылка удалена');
      } catch (error) {
        const message = error.response?.data?.detail || 'Не удалось удалить invite-ссылку';
        this.notify.error(message);
      } finally {
        this.processingInviteId = null;
        this.processingAction = '';
      }
    },

    async copyInviteUrl(url) {
      try {
        await copyTextToClipboard(url);
        this.notify.success('Ссылка скопирована');
      } catch (error) {
        this.notify.error('Не удалось скопировать ссылку');
      }
    },

    async copyCreatedUrls() {
      const urls = this.createdInvites
          .map(item => item.invite_url)
          .filter(Boolean)
          .join('\n');

      if (!urls) {
        this.notify.warning('Нет ссылок для копирования');
        return;
      }

      await this.copyInviteUrl(urls);
    },

    clearCreatedInvites() {
      this.createdInvites = [];
    },
  },

  mounted() {
    this.fetchInvites();
  },
};
</script>

<template>
  <div class="card invite-admin-page">
    <div class="card-header">
      <div>
        <h2 class="section-title">Пригласительные-ссылки</h2>
        <p class="section-subtitle">Создание, отзыв и контроль ссылок регистрации по приглашению</p>
      </div>

      <div class="header-actions">
        <div class="header-chip">
          <span class="header-chip-label">Активных</span>
          <strong>{{ activeInvitesCount }}</strong>
        </div>
        <button class="btn btn-secondary" @click="fetchInvites" :disabled="loading">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 2v6h-6"></path>
            <path d="M3 12a9 9 0 0 1 15.55-6.36L21 8"></path>
            <path d="M3 22v-6h6"></path>
            <path d="M21 12a9 9 0 0 1-15.55 6.36L3 16"></path>
          </svg>
          Обновить
        </button>
      </div>
    </div>

    <div class="invite-form-grid">
      <section class="invite-panel">
        <div class="panel-head">
          <div class="panel-icon single">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M14 14.252v2.09A6 6 0 0 0 6 22H4a8 8 0 0 1 10-7.749M12 13c-3.315 0-6-2.685-6-6s2.685-6 6-6s6 2.685 6 6s-2.685 6-6 6m0-2c2.21 0 4-1.79 4-4s-1.79-4-4-4s-4 1.79-4 4s1.79 4 4 4m6 6v-3h2v3h3v2h-3v3h-2v-3h-3v-2z"/></svg>
          </div>
          <div>
            <h3>Одна ссылка</h3>
            <p>Создать приглашение для одного пользователя</p>
          </div>
        </div>

        <form class="panel-form" @submit.prevent="createSingleInvite">
          <div class="form-group">
            <label for="invite-one-email">Email</label>
            <input
                id="invite-one-email"
                v-model.trim="oneForm.target_email"
                type="email"
                class="form-input"
                placeholder="teacher@example.com"
                required
            >
          </div>

          <div class="form-row two-columns">
            <div class="form-group">
              <label for="invite-one-role">Роль</label>
              <select id="invite-one-role" v-model="oneForm.target_role" class="form-select">
                <option v-for="option in roleOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
            </div>

            <div class="form-group">
              <label for="invite-one-expire">Действует до</label>
              <input
                  id="invite-one-expire"
                  v-model="oneForm.expires_at"
                  type="datetime-local"
                  class="form-input"
              >
            </div>
          </div>

          <div class="form-group">
            <label for="invite-one-note">Примечание</label>
            <textarea
                id="invite-one-note"
                v-model.trim="oneForm.note"
                class="form-textarea"
                rows="3"
                placeholder="Например: кафедра ИТ"
            ></textarea>
          </div>

          <div class="panel-actions">
            <button type="button" class="btn btn-secondary" @click="resetOneForm" :disabled="createOneLoading">Сбросить</button>
            <button type="submit" class="btn btn-primary" :disabled="createOneLoading">
              <span v-if="createOneLoading" class="spinner-small spinner-white"></span>
              {{ createOneLoading ? 'Создание...' : 'Создать ссылку' }}
            </button>
          </div>
        </form>
      </section>

      <section class="invite-panel">
        <div class="panel-head">
          <div class="panel-icon batch">
            <svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024"><path fill="currentColor" d="M892 772h-80v-80c0-4.4-3.6-8-8-8h-48c-4.4 0-8 3.6-8 8v80h-80c-4.4 0-8 3.6-8 8v48c0 4.4 3.6 8 8 8h80v80c0 4.4 3.6 8 8 8h48c4.4 0 8-3.6 8-8v-80h80c4.4 0 8-3.6 8-8v-48c0-4.4-3.6-8-8-8M373.5 498.4c-.9-8.7-1.4-17.5-1.4-26.4c0-15.9 1.5-31.4 4.3-46.5c.7-3.6-1.2-7.3-4.5-8.8c-13.6-6.1-26.1-14.5-36.9-25.1a127.54 127.54 0 0 1-38.7-95.4c.9-32.1 13.8-62.6 36.3-85.6c24.7-25.3 57.9-39.1 93.2-38.7c31.9.3 62.7 12.6 86 34.4c7.9 7.4 14.7 15.6 20.4 24.4c2 3.1 5.9 4.4 9.3 3.2c17.6-6.1 36.2-10.4 55.3-12.4c5.6-.6 8.8-6.6 6.3-11.6c-32.5-64.3-98.9-108.7-175.7-109.9c-110.8-1.7-203.2 89.2-203.2 200c0 62.8 28.9 118.8 74.2 155.5c-31.8 14.7-61.1 35-86.5 60.4c-54.8 54.7-85.8 126.9-87.8 204a8 8 0 0 0 8 8.2h56.1c4.3 0 7.9-3.4 8-7.7c1.9-58 25.4-112.3 66.7-153.5c29.4-29.4 65.4-49.8 104.7-59.7c3.8-1.1 6.4-4.8 5.9-8.8M824 472c0-109.4-87.9-198.3-196.9-200C516.3 270.3 424 361.2 424 472c0 62.8 29 118.8 74.2 155.5a301 301 0 0 0-86.4 60.4C357 742.6 326 814.8 324 891.8a8 8 0 0 0 8 8.2h56c4.3 0 7.9-3.4 8-7.7c1.9-58 25.4-112.3 66.7-153.5C505.8 695.7 563 672 624 672c110.4 0 200-89.5 200-200m-109.5 90.5C690.3 586.7 658.2 600 624 600s-66.3-13.3-90.5-37.5a127.26 127.26 0 0 1-37.5-91.8c.3-32.8 13.4-64.5 36.3-88c24-24.6 56.1-38.3 90.4-38.7c33.9-.3 66.8 12.9 91 36.6c24.8 24.3 38.4 56.8 38.4 91.4c-.1 34.2-13.4 66.3-37.6 90.5"/></svg>
          </div>
          <div>
            <h3>Несколько ссылок</h3>
            <p>Сразу несколько invite-ссылок с общими параметрами</p>
          </div>
        </div>

        <form class="panel-form" @submit.prevent="createBatchInvites">
          <div class="form-group">
            <label for="invite-batch-emails">Email-адреса</label>
            <textarea
                id="invite-batch-emails"
                v-model.trim="batchForm.emails"
                class="form-textarea form-textarea-large"
                rows="5"
                placeholder="teacher1@example.com&#10;teacher2@example.com"
                required
            ></textarea>
            <p class="field-hint">По одному email в строке, либо через запятую</p>
          </div>

          <div class="form-row two-columns">
            <div class="form-group">
              <label for="invite-batch-role">Роль</label>
              <select id="invite-batch-role" v-model="batchForm.target_role" class="form-select">
                <option v-for="option in roleOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
            </div>

            <div class="form-group">
              <label for="invite-batch-expire">Действует до</label>
              <input
                  id="invite-batch-expire"
                  v-model="batchForm.expires_at"
                  type="datetime-local"
                  class="form-input"
              >
            </div>
          </div>

          <div class="form-group">
            <label for="invite-batch-note">Примечание</label>
            <textarea
                id="invite-batch-note"
                v-model.trim="batchForm.note"
                class="form-textarea"
                rows="3"
                placeholder="Общее примечание для пакета"
            ></textarea>
          </div>

          <div class="panel-actions">
            <button type="button" class="btn btn-secondary" @click="resetBatchForm" :disabled="createBatchLoading">Сбросить</button>
            <button type="submit" class="btn btn-primary" :disabled="createBatchLoading">
              <span v-if="createBatchLoading" class="spinner-small spinner-white"></span>
              {{ createBatchLoading ? 'Создание...' : 'Создать ссылки' }}
            </button>
          </div>
        </form>
      </section>
    </div>

    <section v-if="hasCreatedInvites" class="created-results">
      <div class="created-results-header">
        <div>
          <h3>Созданные ссылки</h3>
          <p>Скопируйте и отправьте получателям готовые invite URL</p>
        </div>

        <div class="created-results-actions">
          <button class="btn btn-secondary" @click="copyCreatedUrls">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            Скопировать все
          </button>
          <button class="btn btn-ghost" @click="clearCreatedInvites">Скрыть</button>
        </div>
      </div>

      <div class="created-results-list">
        <article v-for="invite in createdInvites" :key="invite.id" class="created-result-card">
          <div class="created-result-main">
            <div class="created-result-topline">
              <strong>{{ invite.target_email }}</strong>
              <span class="mini-pill">{{ getInviteRoleLabel(invite.target_role) }}</span>
            </div>

            <div class="created-result-url">{{ invite.invite_url }}</div>

            <div class="created-result-meta">
              <span>Истекает: {{ formatDate(invite.expires_at) }}</span>
              <span v-if="invite.note">{{ invite.note }}</span>
            </div>
          </div>

          <button class="btn btn-secondary btn-copy" @click="copyInviteUrl(invite.invite_url)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            Копировать
          </button>
        </article>
      </div>
    </section>

    <section class="invite-list-section">
      <div class="section-head">
        <div>
          <h3>Список ссылок</h3>
        </div>
      </div>

      <div v-if="error" class="alert-box error">
        <span>{{ error }}</span>
        <button class="btn btn-secondary" @click="fetchInvites">Повторить</button>
      </div>

      <div class="table-wrapper invite-table-wrapper">
        <table v-if="!loading && invites.length > 0" class="data-table invite-table">
          <thead>
          <tr>
            <th>Email</th>
            <th>Роль</th>
            <th>Статус</th>
            <th>Создана</th>
            <th>Действует до</th>
            <th>Примечание</th>
            <th class="text-right">Действия</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="invite in invites" :key="invite.id" class="table-row">
            <td>
              <div class="invite-target-cell">
                <strong>{{ invite.target_email }}</strong>
                <span>{{ getInviteCreatedBadge(invite) }}</span>
              </div>
            </td>
            <td>
              <span class="mini-pill">{{ getInviteRoleLabel(invite.target_role) }}</span>
            </td>
            <td>
              <div class="status-cell">
                <span class="status-badge" :class="getInviteStatusClass(invite)">
                  <span class="status-dot"></span>
                  {{ getInviteStatusLabel(getInviteStatus(invite)) }}
                </span>
                <span class="status-meta">{{ getInviteMetaText(invite) }}</span>
              </div>
            </td>
            <td>
              <div class="datetime-cell">
                <strong>{{ getDateParts(invite.created_at).date }}</strong>
                <span v-if="getDateParts(invite.created_at).time">{{ getDateParts(invite.created_at).time }}</span>
              </div>
            </td>
            <td>
              <div class="datetime-cell">
                <strong>{{ getDateParts(invite.expires_at).date }}</strong>
                <span v-if="getDateParts(invite.expires_at).time">{{ getDateParts(invite.expires_at).time }}</span>
              </div>
            </td>
            <td>
              <span class="note-text">{{ invite.note || '—' }}</span>
            </td>
            <td class="text-right">
              <div class="row-actions">
                <button
                    class="action-btn warn"
                    :disabled="getInviteStatus(invite) !== 'active' || isBusy(invite.id, 'revoke')"
                    title="Отозвать"
                    @click="revokeInvite(invite)"
                >
                  <span v-if="isBusy(invite.id, 'revoke')" class="spinner-small"></span>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path fill="currentColor" fill-rule="evenodd" d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0m-6.305 4.17A4.5 4.5 0 0 1 3.83 6.305zm2.475-2.475L6.305 3.83a4.5 4.5 0 0 1 5.865 5.865" clip-rule="evenodd"/></svg>
                </button>

                <button
                    class="action-btn delete"
                    :disabled="isBusy(invite.id, 'delete')"
                    title="Удалить"
                    @click="deleteInvite(invite)"
                >
                  <span v-if="isBusy(invite.id, 'delete')" class="spinner-small"></span>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"></path>
                    <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  </svg>
                </button>
              </div>
            </td>
          </tr>
          </tbody>
        </table>

        <div v-else-if="loading" class="state-box">
          <div class="spinner-large"></div>
          <p>Загрузка invite-ссылок...</p>
        </div>

        <div v-else class="state-box empty">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8 12h8"></path>
            <path d="M8 16h5"></path>
            <path d="M15 3h3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8l5-5h6a2 2 0 0 1 2 2v2"></path>
          </svg>
          <p>Invite-ссылок пока нет</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.invite-admin-page {
  background: var(--surface);
  color: var(--text-primary);
  border: 1px solid var(--border);
}

.card {
  padding: 24px;
  border-radius: 18px;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
}

.card-header,
.section-head,
.created-results-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.card-header {
  margin-bottom: 24px;
}

.section-title,
.section-head h3,
.created-results-header h3 {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
}

.section-subtitle,
.section-head p,
.created-results-header p,
.field-hint {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.header-actions,
.created-results-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.header-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.16);
  color: var(--text-primary);
}

.header-chip-label {
  color: var(--text-secondary);
  font-size: 13px;
}

.invite-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 22px;
}

.invite-panel,
.created-results {
  background:
      radial-gradient(circle at top right, rgba(37, 99, 235, 0.08), transparent 34%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.95));
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 18px;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 18px;
}

.panel-head h3 {
  margin: 0 0 4px;
  font-size: 18px;
  font-weight: 700;
}

.panel-head p {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.panel-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  flex-shrink: 0;
}

.panel-icon.single {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
}

.panel-icon.batch {
  background: linear-gradient(135deg, #0f766e, #14b8a6);
}

.panel-icon svg {
  width: 22px;
  height: 22px;
}

.panel-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-row.two-columns {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  border: 1px solid var(--input-border);
  border-radius: 12px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 14px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
  box-sizing: border-box;
}

.form-input,
.form-select {
  height: 42px;
  padding: 0 14px;
}

.form-textarea {
  padding: 12px 14px;
  min-height: 96px;
  resize: vertical;
}

.form-textarea-large {
  min-height: 126px;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.14);
}

.form-select {
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg width='12' height='8' viewBox='0 0 12 8' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%2364748b' stroke-width='2' fill='none'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
  padding-right: 38px;
}

.panel-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 4px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 40px;
  padding: 0 16px;
  border-radius: 10px;
  border: 1px solid transparent;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease, border-color 0.18s ease;
}

.btn svg {
  width: 16px;
  height: 16px;
}

.btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  transform: none;
}

.btn-primary {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #ffffff;
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.18);
}

.btn-primary:hover:not(:disabled) {
  box-shadow: 0 14px 28px rgba(37, 99, 235, 0.24);
}

.btn-secondary {
  background: var(--surface-soft);
  color: var(--text-primary);
  border-color: var(--border);
}

.btn-secondary:hover:not(:disabled) {
  background: rgba(148, 163, 184, 0.12);
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid transparent;
}

.btn-ghost:hover:not(:disabled) {
  color: var(--text-primary);
  background: rgba(148, 163, 184, 0.08);
}

.created-results {
  margin-bottom: 22px;
}

.created-results-list {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}

.created-result-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid var(--border);
}

.created-result-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.created-result-topline {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.created-result-topline strong {
  color: var(--text-primary);
}

.created-result-url {
  font-family: ui-monospace, monospace;
  font-size: 13px;
  color: #2563eb;
  word-break: break-all;
}

.created-result-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--text-secondary);
}

.mini-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 9px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.14);
  border: 1px solid rgba(148, 163, 184, 0.18);
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 600;
}

.btn-copy {
  flex-shrink: 0;
}

.invite-list-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.alert-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid rgba(239, 68, 68, 0.24);
  background: rgba(254, 242, 242, 0.9);
  color: #b91c1c;
}

.invite-table-wrapper {
  overflow-x: auto;
  border-radius: 16px;
}

.invite-table {
  width: 100%;
  min-width: 980px;
  border-collapse: collapse;
}

.invite-table th,
.invite-table td {
  padding: 14px 16px;
  vertical-align: top;
}

.invite-table th {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-secondary);
  background: rgba(248, 250, 252, 0.86);
}

.invite-target-cell,
.status-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.invite-target-cell strong {
  color: var(--text-primary);
}

.invite-target-cell span,
.status-meta,
.note-text {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.45;
}

.datetime-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.datetime-cell strong {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
  white-space: nowrap;
}

.datetime-cell span {
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.2;
  white-space: nowrap;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  width: fit-content;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  border: 1px solid transparent;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: currentColor;
}

.status-active {
  background: rgba(20, 184, 166, 0.12);
  color: #0f766e;
  border-color: rgba(20, 184, 166, 0.18);
}

.status-used {
  background: rgba(37, 99, 235, 0.12);
  color: #1d4ed8;
  border-color: rgba(37, 99, 235, 0.18);
}

.status-revoked {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
  border-color: rgba(239, 68, 68, 0.18);
}

.status-expired {
  background: rgba(245, 158, 11, 0.14);
  color: #b45309;
  border-color: rgba(245, 158, 11, 0.18);
}

.text-right {
  text-align: right;
}

.row-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.action-btn {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--surface-soft);
  color: var(--text-secondary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.18s ease, background 0.18s ease, color 0.18s ease, border-color 0.18s ease;
}

.action-btn svg {
  width: 16px;
  height: 16px;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.action-btn.warn:hover:not(:disabled) {
  background: rgba(245, 158, 11, 0.14);
  color: #b45309;
  border-color: rgba(245, 158, 11, 0.24);
}

.action-btn.delete:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
  border-color: rgba(239, 68, 68, 0.24);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.state-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 42px 20px;
  color: var(--text-secondary);
}

.state-box.empty svg {
  width: 42px;
  height: 42px;
  color: var(--text-secondary);
}

.spinner-small,
.spinner-large {
  border-radius: 999px;
  border-style: solid;
  border-color: rgba(148, 163, 184, 0.24);
  border-top-color: currentColor;
  animation: spin 0.8s linear infinite;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border-width: 2px;
}

.spinner-large {
  width: 30px;
  height: 30px;
  border-width: 3px;
  color: #2563eb;
}

.spinner-white {
  border-color: rgba(255, 255, 255, 0.3);
  border-top-color: #ffffff;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

:global(html[data-theme='dark']) .invite-admin-page .invite-panel,
:global(html[data-theme='dark']) .invite-admin-page .created-results {
  background:
      radial-gradient(circle at top right, rgba(37, 99, 235, 0.16), transparent 34%),
      linear-gradient(180deg, rgba(15, 23, 42, 0.94), rgba(17, 24, 39, 0.96));
  border-color: #334155;
  box-shadow: 0 18px 36px rgba(2, 6, 23, 0.2);
}

:global(html[data-theme='dark']) .invite-admin-page .created-result-card {
  background: rgba(15, 23, 42, 0.72);
  border-color: #334155;
}

:global(html[data-theme='dark']) .invite-admin-page .header-chip {
  background: rgba(30, 64, 175, 0.22);
  border-color: rgba(96, 165, 250, 0.32);
}

:global(html[data-theme='dark']) .invite-admin-page .panel-head p,
:global(html[data-theme='dark']) .invite-admin-page .field-hint,
:global(html[data-theme='dark']) .invite-admin-page .created-result-meta,
:global(html[data-theme='dark']) .invite-admin-page .invite-target-cell span,
:global(html[data-theme='dark']) .invite-admin-page .status-meta,
:global(html[data-theme='dark']) .invite-admin-page .note-text,
:global(html[data-theme='dark']) .invite-admin-page .datetime-cell span {
  color: #94a3b8;
}

:global(html[data-theme='dark']) .invite-admin-page .panel-head h3,
:global(html[data-theme='dark']) .invite-admin-page .created-result-topline strong,
:global(html[data-theme='dark']) .invite-admin-page .datetime-cell strong {
  color: #e2e8f0;
}

:global(html[data-theme='dark']) .invite-admin-page .mini-pill {
  background: rgba(30, 41, 59, 0.82);
  border-color: #475569;
  color: #e2e8f0;
}

:global(html[data-theme='dark']) .invite-admin-page .form-input,
:global(html[data-theme='dark']) .invite-admin-page .form-select,
:global(html[data-theme='dark']) .invite-admin-page .form-textarea {
  background: #0b1220;
  border-color: #334155;
  color: #e2e8f0;
}

:global(html[data-theme='dark']) .invite-admin-page .form-input::placeholder,
:global(html[data-theme='dark']) .invite-admin-page .form-textarea::placeholder {
  color: #64748b;
}

:global(html[data-theme='dark']) .invite-admin-page .form-input:focus,
:global(html[data-theme='dark']) .invite-admin-page .form-select:focus,
:global(html[data-theme='dark']) .invite-admin-page .form-textarea:focus {
  border-color: #60a5fa;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.18);
}

:global(html[data-theme='dark']) .invite-admin-page .created-result-url {
  color: #93c5fd;
}

:global(html[data-theme='dark']) .invite-admin-page .invite-table th {
  background: rgba(15, 23, 42, 0.92) !important;
}

:global(html[data-theme='dark']) .invite-admin-page .form-select {
  background-image: url("data:image/svg+xml,%3Csvg width='12' height='8' viewBox='0 0 12 8' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1l5 5l5-5' stroke='%23cbd5e1' stroke-width='2' fill='none'/%3E%3C/svg%3E");
}

:global(html[data-theme='dark']) .invite-admin-page .alert-box {
  background: rgba(127, 29, 29, 0.22);
  border-color: rgba(248, 113, 113, 0.28);
  color: #fecaca;
}

@media (max-width: 960px) {
  .invite-form-grid {
    grid-template-columns: 1fr;
  }

  .created-result-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .btn-copy {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .card {
    padding: 18px;
  }

  .section-title,
  .section-head h3,
  .created-results-header h3 {
    font-size: 19px;
  }

  .form-row.two-columns {
    grid-template-columns: 1fr;
  }

  .header-actions,
  .created-results-actions,
  .panel-actions {
    width: 100%;
  }

  .panel-actions .btn,
  .header-actions .btn,
  .created-results-actions .btn {
    flex: 1;
  }

  .header-chip {
    width: 100%;
    justify-content: center;
  }

  .alert-box {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
