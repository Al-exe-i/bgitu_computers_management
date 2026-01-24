<script>
import api from "@/services/api.js";
import router from "@/router/index.js";
import {useNotificationsStore} from "@/stores/notifications.js";
import LoaderContainer from "@/components/Common/LoaderContainer.vue";
import {useAuthStore} from "@/stores/auth.js";
import {getApiUrl, getWsUrl, SERVER_URL} from "@/config/api.js";
import {useAudienceContext} from "@/stores/officeCtx.js";

export default {
  name: 'AudienceView',
  components: { LoaderContainer},
  props: ['audienceId'],
  data() {
    return {
      classroom: null,
      loading: true,
      dropClassroomModalShow: false,
      selectedCell: null,
      equipmentTypes: {
        computer: {
          name: 'Компьютер',
          color: 'linear-gradient(135deg, #3b82f6, #2563eb)',
          icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"></rect><path d="M8 21h8M12 17v4"></path></svg>'
        },
        tv: {
          name: 'Телевизор',
          color: 'linear-gradient(135deg, #f97316, #ea580c)',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 1920 1536"><path fill="currentColor" d="M1792 1120V160q0-13-9.5-22.5T1760 128H160q-13 0-22.5 9.5T128 160v960q0 13 9.5 22.5t22.5 9.5h1600q13 0 22.5-9.5t9.5-22.5m128-960v960q0 66-47 113t-113 47h-736v128h352q14 0 23 9t9 23v64q0 14-9 23t-23 9H544q-14 0-23-9t-9-23v-64q0-14 9-23t23-9h352v-128H160q-66 0-113-47T0 1120V160Q0 94 47 47T160 0h1600q66 0 113 47t47 113"/></svg>'
        },
        projector: {
          name: 'Проектор',
          color: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 16 16"><g fill="currentColor"><path d="M14 7.5a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0M2.5 6a.5.5 0 0 0 0 1h4a.5.5 0 0 0 0-1zm0 2a.5.5 0 0 0 0 1h4a.5.5 0 0 0 0-1z"/><path d="M0 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2a1 1 0 0 1-1 1h-1a1 1 0 0 1-1-1H5a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1a2 2 0 0 1-2-2zm2-1a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V6a1 1 0 0 0-1-1z"/></g></svg>'
        },
        printer: {
          name: 'Принтер',
          color: 'linear-gradient(135deg, #10b981, #059669)',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 16 16"><g fill="currentColor"><path d="M5 1a2 2 0 0 0-2 2v1h10V3a2 2 0 0 0-2-2zm6 8H5a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-3a1 1 0 0 0-1-1"/><path d="M0 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2h-1v-2a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v2H2a2 2 0 0 1-2-2zm2.5 1a.5.5 0 1 0 0-1a.5.5 0 0 0 0 1"/></g></svg>'
        },
        switch: {
          name: 'Коммутатор',
          color: 'linear-gradient(135deg, #f59e0b, #d97706)',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 36 36"><path fill="currentColor" d="M32.26 13.15A7.49 7.49 0 0 1 22.57 7H7.13a2 2 0 0 0-1.91 1.41L2.09 18.48a2 2 0 0 0-.09.59V27a2 2 0 0 0 2 2h28a2 2 0 0 0 2-2v-7.94a2 2 0 0 0-.09-.59ZM8.92 25h-1.8v-3h1.8Zm5 0h-1.8v-3h1.8Zm5 0h-1.8v-3h1.8Zm5 0H22.1v-3h1.8Zm5 0H27.1v-3h1.8ZM31 19.4H5V18h26Z" class="clr-i-solid--badged clr-i-solid-path-1--badged"/><circle cx="30" cy="6" r="5" fill="currentColor" class="clr-i-solid--badged clr-i-solid-path-2--badged clr-i-badge"/><path fill="none" d="M0 0h36v36H0z"/></svg>'
        },
        router: {
          name: 'Роутер',
          color: 'linear-gradient(135deg, #06b6d4, #0891b2)',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 16 16"><g fill="currentColor"><path d="M5.525 3.025a3.5 3.5 0 0 1 4.95 0a.5.5 0 1 0 .707-.707a4.5 4.5 0 0 0-6.364 0a.5.5 0 0 0 .707.707"/><path d="M6.94 4.44a1.5 1.5 0 0 1 2.12 0a.5.5 0 0 0 .708-.708a2.5 2.5 0 0 0-3.536 0a.5.5 0 0 0 .707.707Z"/><path d="M2.974 2.342a.5.5 0 1 0-.948.316L3.806 8H1.5A1.5 1.5 0 0 0 0 9.5v2A1.5 1.5 0 0 0 1.5 13H2a.5.5 0 0 0 .5.5h2A.5.5 0 0 0 5 13h6a.5.5 0 0 0 .5.5h2a.5.5 0 0 0 .5-.5h.5a1.5 1.5 0 0 0 1.5-1.5v-2A1.5 1.5 0 0 0 14.5 8h-2.306l1.78-5.342a.5.5 0 1 0-.948-.316L11.14 8H4.86zM2.5 11a.5.5 0 1 1 0-1a.5.5 0 0 1 0 1m4.5-.5a.5.5 0 1 1 1 0a.5.5 0 0 1-1 0m2.5.5a.5.5 0 1 1 0-1a.5.5 0 0 1 0 1m1.5-.5a.5.5 0 1 1 1 0a.5.5 0 0 1-1 0m2 0a.5.5 0 1 1 1 0a.5.5 0 0 1-1 0"/><path d="M8.5 5.5a.5.5 0 1 1-1 0a.5.5 0 0 1 1 0"/></g></svg>'
        },
        other: {
          name: 'Другое',
          color: 'linear-gradient(135deg, #64748b, #475569)',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M10.358 9.938c1.082-.12 2.202-.12 3.284 0a.464.464 0 0 1 .409.4c.129 1.104.129 2.22 0 3.324a.464.464 0 0 1-.41.4a14.92 14.92 0 0 1-3.283 0a.464.464 0 0 1-.409-.4a14.324 14.324 0 0 1 0-3.324a.464.464 0 0 1 .41-.4"/><path fill="currentColor" fill-rule="evenodd" d="M15 2.25a.75.75 0 0 1 .75.75v2.927a2.929 2.929 0 0 1 2.308 2.323H21a.75.75 0 0 1 0 1.5h-2.788c.037.5.061 1 .073 1.5H20a.75.75 0 0 1 0 1.5h-1.715c-.012.5-.036 1-.073 1.5H21a.75.75 0 0 1 0 1.5h-2.942a2.929 2.929 0 0 1-2.308 2.323V21a.75.75 0 0 1-1.5 0v-2.774c-.498.035-.999.059-1.5.07V20a.75.75 0 0 1-1.5 0v-1.704a31.963 31.963 0 0 1-1.5-.07V21a.75.75 0 0 1-1.5 0v-2.927a2.929 2.929 0 0 1-2.308-2.323H3a.75.75 0 0 1 0-1.5h2.788c-.037-.5-.061-1-.074-1.5H4a.75.75 0 0 1 0-1.5h1.714c.013-.5.037-1 .074-1.5H3a.75.75 0 0 1 0-1.5h2.942A2.929 2.929 0 0 1 8.25 5.927V3a.75.75 0 0 1 1.5 0v2.774c.498-.035.999-.059 1.5-.07V4a.75.75 0 0 1 1.5 0v1.704c.501.011 1.002.035 1.5.07V3a.75.75 0 0 1 .75-.75m-1.192 6.197a16.407 16.407 0 0 0-3.616 0c-.898.1-1.626.808-1.732 1.717a15.808 15.808 0 0 0 0 3.672c.106.91.834 1.616 1.732 1.717c1.192.133 2.424.133 3.616 0a1.963 1.963 0 0 0 1.732-1.717c.143-1.22.143-2.452 0-3.672a1.963 1.963 0 0 0-1.732-1.717" clip-rule="evenodd"/></svg>'
        }
      },
      /*Редактирование инв номера и названия оборудования в модалке */
      invNumEdit: false,
      hwTitleEdit: false,
      newInv_no: ``,
      newHwTitle: ``,

      /* Раздел файлов оборудования в модалке */
      isDragOver: false,
      showConfirmModal: false,
      fileToDeleteId: null,
      dontAskAgain: false,

      /*WebSocket*/
      ws: null,
      wsConnected: false,
      wsError: false,
      wsReconnectAttempts: 0,
      maxReconnectAttempts: 3,
      reconnectDelay: 3000,

      /* Preview */
      previewIndex: null
    };
  },
  computed: {
    stats() {
      const result = {
        total: 0,
        working: 0,
        broken: 0,
        computers: 0
      };

      Object.values(this.classroom.equipment).forEach(eq => {
        result.total++;
        if (eq.working) result.working++;
        else result.broken++;

        if (eq.id === 'computer') {
          result.computers++;
        }
      });

      return result;
    },

    notify() {
      return useNotificationsStore()
    },

    authStore() {
      return useAuthStore()
    },

    audienceContext() {
      return useAudienceContext()
    },

    currentPreviewFile() {
      if (this.previewIndex === null || !this.selectedCell?.data?.files) return null;
      return this.selectedCell.data.files[this.previewIndex];
    },

    isPreviewImage() {
      return this.currentPreviewFile?.file_type?.startsWith('image/');
    },

    isPreviewVideo() {
      return this.currentPreviewFile?.file_type?.startsWith('video/');
    },

    // Админ или специалист ОИ + авторизован
    havePermission()
    {
      const user = this.authStore.user;
      return this.authStore.isAuthenticated && user && user.role < 2;
    },

    // Плотность сетки
    gridDensityClass()
    {
      if (!this.classroom) return '';

      const cols = this.classroom.gridSize.width;

      if (cols > 15) return 'density-tiny';    // >15 колонок: Очень мелко (как на телефоне)
      if (cols > 10) return 'density-compact'; // 11-15 колонок: Средне (как на планшете)
      return 'density-normal';                 // <=10 колонок: Стандарт
    },
  },

  methods: {
    getApiUrl,
    async getAudience() {
      await api.get(`/audiences/${this.audienceId}`).then(res => {
        this.classroom = this.mapBackendToFrontend(res.data);
        this.loading = false;
        this.audienceContext.setOffice(this.classroom.office_id)
        //Обновляем, если открыта модалка,
        if(this.selectedCell)
        {
          const row = this.selectedCell.row
          const col = this.selectedCell.col
          this.closeModal()
          this.openModal(row, col);
        }
        this.connectWebSocket();
      }).catch(err => {
        this.loading = false;
        router.push(`/`)
      })
    },

    mapBackendToFrontend(data) {
      const equipmentMap = {};

      data.hardware.forEach(item => {
        const gridKey = `${item.y}-${item.x}`;

        equipmentMap[gridKey] = {
          // UI поля (для отображения иконок и цветов)
          id: item.type,          // На фронте id - это тип иконки (computer)
          working: item.state,    // true/false
          comment: item.description || '',

          // Технические поля (сохраняем реальные данные)
          dbId: item.id,          // ВАЖНО: сохраняем ID из базы (19, 20...)
          invNumber: item.inv_number,
          title: item.title,
          files: item.files,
        };
      });

      return {
        number: data.id,
        floor: data.floor,
        gridSize: {
          width: data.width,
          height: data.height
        },
        equipment: equipmentMap,
        office_id: data.office_id,
        description: data.description,
      };
    },

    getEquipment(row, col) {
      return this.classroom.equipment[`${row}-${col}`];
    },

    getEquipmentType(id) {
      return this.equipmentTypes[id];
    },

    getCellClasses(row, col) {
      const eq = this.getEquipment(row, col);
      if (!eq) return ['empty'];

      return [
        'occupied',
        eq.working ? 'working' : 'broken'
      ];
    },

    openModal(row, col) {
      if(!this.authStore.isAuthenticated) return;
      const eq = this.getEquipment(row, col);
      if (!eq) return;

      this.selectedCell = {
        row,
        col,
        key: `${row}-${col}`,
        data: eq
      };
      this.newInv_no = this.selectedCell.data.invNumber;
      this.newHwTitle = this.selectedCell.data.title;
    },

    closeModal() {
      this.selectedCell = null;
      this.invNumEdit = false;
      this.hwTitleEdit = false;
      this.newHwTitle = this.newInv_no = ``;
    },

    async setWorkingStatus(status) {
      if (this.selectedCell)
      {
        let description = status === true ? `` : this.selectedCell.data.comment
        this.closeWebSocket();
        await api.patch(`/hardware/${this.selectedCell.data.dbId}`, {state: status, description: description}
        ).then(res => {
          this.selectedCell.data.working = status;
        }).catch(err => {
          this.notify.error(`Не удалось изменить состояние текущего оборудования!`)
        }).finally(() => {
          this.connectWebSocket()
        })
        if(status)
          this.selectedCell.data.comment = ``
      }
    },

    goBack() {
      router.go(-1)
    },

    editClassroom() {
      router.push({
        name: 'ChangeAudience',
        params: { id: this.classroom.number }
      });
    },

    async updateHardwareField(localKey, apiKey, newValue, editFlagKey, errorMsg)
    {
      const oldValue = this.selectedCell.data[localKey];

      const isUnchanged = oldValue === newValue || (oldValue === null && newValue === '');

      if (isUnchanged) {
        this[editFlagKey] = false;
        return;
      }

      try
      {
        await api.patch(`/hardware/${this.selectedCell.data.dbId}`, {
          [apiKey]: newValue
        });

        this.selectedCell.data[localKey] = newValue;
        this[editFlagKey] = false;

      }
      catch (err)
      {
        this.notify.error(errorMsg);
      }
    },

    async deleteClassroom()
    {
      await api.delete(`/audiences/${this.classroom.number}`).then((response) => {
        this.notify.info(`Аудитория №${this.classroom.number} удалена`)
        const officeIdToRedirect = this.classroom.office_id
        router.push({
          name: `Office`,
          params: {
            officeNumber: officeIdToRedirect}
        }).catch((error) => {
          this.notify.error(`Не удалось удалить аудиторию!`)
        })
      })
    },

    async saveInv_no() {
      await this.updateHardwareField(
          'invNumber',
          'inv_number',
          this.newInv_no,
          'invNumEdit',
          'Не удалось изменить инв. номер текущего оборудования!'
      );
    },

    async saveHwTitle()
    {
      await this.updateHardwareField(
          'title',
          'title',
          this.newHwTitle,
          'hwTitleEdit',
          'Не удалось изменить заголовок текущего оборудования!'
      );
    },
    /* WebSocket */
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
        if (msg?.audience_updated === this.classroom.number)
        {
          this.getAudience()
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
          router.push(`/`)
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
    },
    /* Файлы оборудования */
    async uploadFiles(files) {
      const formData = new FormData();
      files.forEach(file => formData.append('files', file));

      try {
        const hwId = this.selectedCell.data.dbId;
        await api.post(`/hardware/${hwId}/files`, formData).then(response => {
          if (!this.selectedCell.data.files)
            this.selectedCell.data.files = []
          this.selectedCell.data.files.push(...response.data.files)
        })
        this.notify.success("Файлы загружены");
      } catch (e) {
        this.notify.error("Ошибка при загрузке");
      }
    },

    handleFileSelect(event) {
      const files = Array.from(event.target.files);
      this.uploadFiles(files);
    },

    handleDrop(event) {
      this.isDragOver = false;
      const files = Array.from(event.dataTransfer.files);
      if (files.length > 0)
      {
        this.uploadFiles(files);
      }
    },

    async deleteFile(fileId)
    {
      try
      {
        await api.delete(`/hardware/files/${fileId}`);

        // Удаляем файл из локального состояния, чтобы не перекачивать всё заново
        this.selectedCell.data.files = this.selectedCell.data.files.filter(f => f.id !== fileId);

        this.notify.info("Файл удален");
      }
      catch (e)
      {
        this.notify.error("Не удалось удалить файл");
      }
    },

    requestDeleteFile(fileId)
    {
      const isSuppressed = localStorage.getItem('hw_suppress_delete_confirm');

      if (isSuppressed === 'true')
      {
        // Если просили не спрашивать - удаляем сразу
        this.deleteFile(fileId);
      }
      else
      {
        // Иначе показываем окно
        this.fileToDeleteId = fileId;
        this.dontAskAgain = false; // Сбрасываем чекбокс
        this.showConfirmModal = true;
      }
    },

    confirmDelete()
    {
      if (this.dontAskAgain)
      {
        localStorage.setItem('hw_suppress_delete_confirm', 'true');
      }

      this.deleteFile(this.fileToDeleteId);
      this.closeConfirmModal();
    },

    closeConfirmModal()
    {
      this.showConfirmModal = false;
      this.fileToDeleteId = null;
    },

    getVideoStreamUrl(fileId)
    {
      return `${getApiUrl()}/hardware/stream/${fileId}`;
    },

    resolveFileUrl(fileUrl)
    {
      return `${getApiUrl()}${fileUrl}`;
    },

    /* Просмотр файлов */
    openPreview(index) {
      this.previewIndex = index;
      // Блокируем скролл основной страницы, чтобы не ездила
      document.body.style.overflow = 'hidden';

      // Добавляем слушатель клавиш (Esc, Стрелки)
      window.addEventListener('keydown', this.handlePreviewKeys);
    },

    // Закрыть
    closePreview() {
      this.previewIndex = null;
      document.body.style.overflow = ''; // Возвращаем скролл
      window.removeEventListener('keydown', this.handlePreviewKeys);
    },

    nextPreview() {
      if (!this.selectedCell.data.files) return;
      // Циклическая навигация: если последний -> переходим к первому
      if (this.previewIndex < this.selectedCell.data.files.length - 1) {
        this.previewIndex++;
      } else {
        this.previewIndex = 0;
      }
    },

    prevPreview() {
      if (!this.selectedCell.data.files) return;
      // Если первый - переходим к последнему
      if (this.previewIndex > 0) {
        this.previewIndex--;
      } else {
        this.previewIndex = this.selectedCell.data.files.length - 1;
      }
    },

    handlePreviewKeys(e)
    {
      if (e.key === 'Escape') this.closePreview();
      if (e.key === 'ArrowRight') this.nextPreview();
      if (e.key === 'ArrowLeft') this.prevPreview();
    }
  },

  mounted() {
    this.getAudience();
  },

  beforeUnmount() {
    this.closeWebSocket()
    this.audienceContext.clear()
  }
};
</script>

<template>
  <LoaderContainer v-if="loading" />

  <div v-if="!loading" class="page-viewer">
    <header class="top-header">
      <div class="classroom-info">
        <h1 class="classroom-number">Аудитория {{ classroom.number }}</h1>
        <p class="classroom-subtitle">
          {{ classroom.floor }} этаж • Сетка {{ classroom.gridSize.width }}×{{ classroom.gridSize.height }}
        </p>
      </div>
      <div class="header-container">
        <div class="logo-section">
          <button class="back-btn" @click="goBack">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            Назад
          </button>
        </div>


        <div v-if="havePermission" class="header-actions">
          <button class="header-btn edit-btn" @click="editClassroom">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Редактировать
          </button>
          <button class="header-btn delete-btn" @click="dropClassroomModalShow = true">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Удалить
          </button>
        </div>
      </div>
    </header>

    <div class="container">
      <div v-if="authStore.isAuthenticated" class="stats-section">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">Всего оборудования</div>
            <div class="stat-value">{{ stats.total }}</div>
          </div>
          <div class="stat-card working">
            <div class="stat-label">Исправного</div>
            <div class="stat-value">{{ stats.working }}</div>
          </div>
          <div class="stat-card broken">
            <div class="stat-label">Неисправного</div>
            <div class="stat-value">{{ stats.broken }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Компьютеров</div>
            <div class="stat-value">{{ stats.computers }}</div>
          </div>
        </div>
      </div>

      <div v-if="classroom" class="grid-section">
        <div class="grid-header">
          <h2 class="grid-title">Состояние оборудования</h2>
          <p v-if="authStore.isAuthenticated" class="grid-info">Кликните по ячейке для деталей</p>
        </div>

        <div class="grid-wrapper">
          <div
              class="equipment-grid"
              :class="gridDensityClass"
              :style="{ '--grid-cols': classroom.gridSize.width }">
            <template v-for="row in classroom.gridSize.height" :key="row">
              <div
                  v-for="col in classroom.gridSize.width"
                  :key="`${row}-${col}`"
                  class="grid-cell"
                  :class="getCellClasses(row - 1, col - 1)"
                  @click="openModal(row - 1, col - 1)"
              >
                <template v-if="getEquipment(row - 1, col - 1)">
                  <div
                      class="equipment-icon"
                      :style="{ background: getEquipmentType(getEquipment(row - 1, col - 1).id).color }"
                      v-html="getEquipmentType(getEquipment(row - 1, col - 1).id).icon"
                  ></div>
                  <div class="equipment-label">
                    {{ getEquipmentType(getEquipment(row - 1, col - 1).id).name }}
                  </div>
                </template>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <Transition>
      <div v-if="selectedCell" class="modal active" @click.self="closeModal">
        <div class="modal-content">
          <div class="modal-close-upper">
            <button @click="closeModal" class="close">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>

          <h2 class="modal-title">
            {{ getEquipmentType(selectedCell.data.id).name }}
            <span class="modal-subtitle">Ряд {{ selectedCell.row + 1 }}, Место {{ selectedCell.col + 1 }}</span>
          </h2>

          <div class="modal-equipment-info">
            <div
                class="modal-equipment-icon"
                :style="{ background: getEquipmentType(selectedCell.data.id).color }"
                v-html="getEquipmentType(selectedCell.data.id).icon"
            ></div>
            <div class="modal-equipment-details">
              <div v-if="!hwTitleEdit">
                <h3>{{ selectedCell.data.title || getEquipmentType(selectedCell.data.id).name }}</h3>
                <svg @click="hwTitleEdit = true" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="m16.475 5.408l2.117 2.117m-.756-3.982L12.109 9.27a2.118 2.118 0 0 0-.58 1.082L11 13l2.648-.53c.41-.082.786-.283 1.082-.579l5.727-5.727a1.853 1.853 0 1 0-2.621-2.621"/><path d="M19 15v3a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h3"/></g></svg>
              </div>

              <div v-if="hwTitleEdit">
                <input v-model="newHwTitle">
                <svg @click="saveHwTitle" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20"><path fill="currentColor" d="m15.3 5.3l-6.8 6.8l-2.8-2.8l-1.4 1.4l4.2 4.2l8.2-8.2z"/></svg>
              </div>

              <div v-if="invNumEdit">
                <input v-model="newInv_no">
                <svg @click="saveInv_no" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20"><path fill="currentColor" d="m15.3 5.3l-6.8 6.8l-2.8-2.8l-1.4 1.4l4.2 4.2l8.2-8.2z"/></svg>
              </div>

              <div v-if="!invNumEdit">
                <p>Инвентарный №: {{ selectedCell.data.invNumber || `н\\д` }}</p>
                <svg @click="invNumEdit = true" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24">
                  <path fill="currentColor"
                        d="M3.995 17.207V19.5a.5.5 0 0 0 .5.5h2.298a.5.5 0 0 0 .353-.146l9.448-9.448l-3-3l-9.452 9.448a.5.5 0 0 0-.147.353m10.837-11.04l3 3l1.46-1.46a1 1 0 0 0 0-1.414l-1.585-1.586a1 1 0 0 0-1.414 0z"/>
                </svg>
              </div>

            </div>
          </div>

          <div class="status-badge" :class="selectedCell.data.working ? 'working' : 'broken'">
            Текущий статус: {{ selectedCell.data.working ? 'исправно' : 'неисправно' }}
          </div>

          <div class="form-group">
            <label class="form-label">Комментарий / Проблема</label>
            <textarea
                v-model="selectedCell.data.comment"
                class="form-textarea"
                placeholder="Опишите проблему или состояние оборудования..."
            ></textarea>
          </div>

          <div class="action-btns">
            <button
                v-if="havePermission"
                class="action-btn fix-btn"
                :disabled="selectedCell.data.working"
                @click="setWorkingStatus(true)"
            >
              Исправно
            </button>
            <button
                class="action-btn break-btn"
                :disabled="!selectedCell.data.working"
                @click="setWorkingStatus(false)"
            >
              Неисправно
            </button>
          </div>

          <!-- Список файлов (фото и видео) -->
          <div
              class="hw-files-section"
              @dragenter.prevent="isDragOver = true"
              @dragover.prevent
          >
            <!-- Заголовок и кнопка ручного добавления -->
            <div class="hw-section-header">
              <span class="hw-section-title">Вложения ({{ selectedCell.data.files ? selectedCell.data.files.length : 0 }})</span>
              <!-- Компактная кнопка для ручного выбора -->
              <button class="hw-add-btn-small" @click="$refs.fileInput.click()" title="Прикрепить файл">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
                </svg>
                Добавить
              </button>
            </div>

            <!-- Сетка файлов -->
            <div v-if="selectedCell.data.files && selectedCell.data.files.length > 0" class="hw-files-grid">
              <div @click="openPreview(index)" v-for="(file, index) in selectedCell.data.files" :key="file.id" class="hw-file-card">

                <img v-if="file.file_type.startsWith('image/')" :src="resolveFileUrl(file.url)" class="hw-file-preview" />

                <video v-else class="hw-file-preview">
                  <source :src="getVideoStreamUrl(file.id)" :type="file.file_type">
                </video>

                <button @click.stop="requestDeleteFile(file.id)" class="hw-delete-btn" title="Удалить">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 32 32"><path fill="currentColor" d="M17.414 16L24 9.414L22.586 8L16 14.586L9.414 8L8 9.414L14.586 16L8 22.586L9.414 24L16 17.414L22.586 24L24 22.586z"/></svg>
                </button>
              </div>
            </div>

            <div v-else class="hw-no-files">
              Нет прикрепленных файлов
            </div>

            <!-- Скрытый инпут -->
            <input type="file" ref="fileInput" multiple accept="image/*,video/*" @change="handleFileSelect" hidden />

            <!-- ЗОНА DRAG & DROP (OVERLAY). Появляется только если isDragOver === true -->
            <Transition name="fade">
              <div
                  v-if="isDragOver"
                  class="hw-drop-overlay"
                  @dragleave.prevent="isDragOver = false"
                  @drop.prevent="handleDrop"
              >
                <div class="hw-drop-content">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="48" height="48">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                  </svg>
                  <p>Отпустите файлы для загрузки</p>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </Transition>

    <Transition>
      <div v-if="dropClassroomModalShow" class="modal">
        <div class="modal-content">
          <h2 class="modal-title">Удаление аудитории</h2>
          <p style="font-size: 16px; color: #64748b; margin-bottom: 24px;">
            Вы уверены, что хотите удалить <strong>аудиторию №{{ audienceId }}</strong>?
            Сетка оборудования будет удалена безвозвратно.
          </p>
          <div class="action-btns">
            <button @click="deleteClassroom" class="action-btn delete-btn">Удалить</button>
            <button @click="dropClassroomModalShow = false" class="action-btn cancel-btn">Отмена</button>
          </div>
        </div>
      </div>
    </Transition>

    <div v-if="showConfirmModal" class="hw-confirm-overlay" @click.self="closeConfirmModal">
      <div class="hw-confirm-box">
        <h3 class="hw-confirm-title">Удалить файл?</h3>
        <p class="hw-confirm-text">Вы уверены, что хотите удалить этот файл? Это действие нельзя будет отменить.</p>

        <label class="hw-confirm-checkbox">
          <input type="checkbox" v-model="dontAskAgain">
          <span class="checkmark"></span>
          Больше не спрашивать
        </label>

        <div class="hw-confirm-actions">
          <button @click="closeConfirmModal" class="hw-btn-cancel">Отмена</button>
          <button @click="confirmDelete" class="hw-btn-delete">Удалить</button>
        </div>
      </div>
    </div>

    <div v-if="previewIndex !== null && selectedCell" class="hw-lightbox" @click.self="closePreview">

      <button class="hw-lb-close" @click="closePreview">&times;</button>

      <button
          v-if="selectedCell?.data?.files.length > 1"
          class="hw-lb-nav hw-lb-prev"
          @click.stop="prevPreview"
      >
        &#10094; </button>

      <div class="hw-lb-content" @click.stop>

        <img
            v-if="isPreviewImage"
            :src="resolveFileUrl(currentPreviewFile.url)"
            class="hw-lb-image"
        />

        <video
            v-if="isPreviewVideo"
            :src="getVideoStreamUrl(currentPreviewFile.id)"
            controls
            autoplay
            class="hw-lb-video"
        ></video>

        <div class="hw-lb-caption">
          Файл {{ previewIndex + 1 }} из {{ selectedCell?.data.files.length }}
        </div>
      </div>

      <button
          v-if="selectedCell.data.files.length > 1"
          class="hw-lb-nav hw-lb-next"
          @click.stop="nextPreview"
      >
        &#10095; </button>
    </div>

  </div>

</template>

<style scoped>
.page-viewer {
  background-size: 400% 400%;
  animation: gradientShift 20s ease infinite;
  min-height: 100vh;
  padding-bottom: 40px;
}

@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.container {
  max-width: 1600px;
  margin: 0 auto;
  padding: 20px;
}

/* Header */
.header-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 32px;
  gap: 24px;
  max-width: 1600px;
  margin: 0 auto;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: white;
  border: 2px solid #3b82f6;
  border-radius: 10px;
  color: #3b82f6;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: #3b82f6;
  color: white;
  transform: translateX(-3px);
}

.back-btn svg {
  width: 18px;
  height: 18px;
}

.classroom-info {
  text-align: center;
  margin-top: 1rem;
}

.classroom-number {
  font-size: 28px;
  font-weight: 800;
  color: #1e293b;
}

.classroom-subtitle {
  font-size: 14px;
  color: #64748b;
  margin-top: 4px;
}

.header-actions {
  display: flex;
  gap: 12px;
  flex: 1;
  justify-content: end;
}

.header-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.header-btn svg {
  width: 18px;
  height: 18px;
}

.edit-btn {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: white;
}

.edit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4);
}

.delete-btn {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
}

.delete-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
}

/* Statistics */
.stats-section {
  margin-bottom: 30px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 800;
  color: #1e293b;
}

.stat-card.working .stat-value {
  color: #10b981;
}

.stat-card.broken .stat-value {
  color: #ef4444;
}

/* Grid Section */
.grid-section {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 32px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(226, 232, 240, 0.8);
  margin-bottom: 24px;
}

.grid-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.grid-title {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
}

.grid-info {
  font-size: 14px;
  color: #64748b;
}

.grid-wrapper {
  display: flex;
  justify-content: center;
  overflow-x: auto;
  padding: 20px 0;
  -webkit-overflow-scrolling: touch;
}

.equipment-grid {
  --cell-size: 90px;
  --icon-div-size: 48px;
  --icon-size: 26px;
  --font-size: 12px;
  --equipment-label-fw: 600;
  --icon-div-mb: 6px;

  grid-template-columns: repeat(var(--grid-cols), var(--cell-size));
  display: inline-grid;
  gap: 12px;
  padding: 24px;
  background: #f8fafc;
  border-radius: 16px;
  border: 2px dashed #cbd5e1;
}

.equipment-grid.density-compact {
  --cell-size: 70px;
  --icon-div-size: 42px;
  --icon-size: 24px;
  --font-size: 11px;
  --equipment-label-fw: 500;
  --icon-div-mb: 3px;

  gap: 8px;
}

.equipment-grid.density-tiny {
  --cell-size: 55px;
  --icon-div-size: 38px;
  --icon-size: 24px;
  --font-size: 0px; /* Скрываем текст, так как он не влезет */
  gap: 4px;
}

.grid-cell {
  width: var(--cell-size);
  height: var(--cell-size);
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  /* Анимация появления */
  animation: fadeInCell 0.4s ease forwards;
}

@keyframes fadeInCell {
  from { opacity: 0; transform: scale(0.8); }
  to { opacity: 1; transform: scale(1); }
}

.grid-cell.empty {
  background: #f8fafc;
  border-style: dashed;
  cursor: default;
}

.grid-cell.occupied:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
  border-color: #3b82f6;
}

.grid-cell.occupied.working {
  background: linear-gradient(135deg, rgba(220, 252, 231, 0.4), rgba(187, 247, 208, 0.4));
  border-color: rgba(134, 239, 172, 0.5);
}

.grid-cell.occupied.broken {
  background: linear-gradient(135deg, rgba(254, 226, 226, 0.4), rgba(254, 202, 202, 0.4));
  border-color: rgba(252, 165, 165, 0.5);
}

.equipment-icon {
  width: var(--icon-div-size);
  height: var(--icon-div-size);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--icon-div-mb);
  color: white;
  transition: transform 0.3s ease;
  will-change: transform;
}

.grid-cell.occupied:hover .equipment-icon {
  transform: scale(1.08);
}

.equipment-icon :deep(svg) {
  width: var(--icon-size);
  height: var(--icon-size);
}

.equipment-label {
  font-size: var(--font-size);
  font-weight: var(--equipment-label-fw);
  color: #334155;
  text-align: center;
  user-select: none;
}

/* Modal */
.modal {
  position: fixed;
  z-index: 1000;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  backdrop-filter: blur(4px);
}

.modal-close-upper
{
  display: flex;
  justify-content: end;
  padding-top: 1rem;

  button
  {
    width: 40px;
    height: 40px;
    border-radius: 12px;
    border: none;
    background: #f3f4f6;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    flex-shrink: 0;
    margin: 0 -20px;
    will-change: transform;
  }

  button svg
  {
    width: 20px;
    height: 20px;
    stroke: #e82935;
  }

  button:hover
  {
    background: #e5e7eb;
    transform: scale(1.05);
  }
}

.modal-content {
  background: white;
  border-radius: 20px;
  padding: 0 32px 32px;
  width: 100%;
  max-width: 540px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  animation: modalAppear 0.3s ease;
}

.modal-title {
  font-size: 24px;
  color: #1e293b;
  margin-bottom: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.modal-subtitle {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.modal-equipment-info {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
  margin-bottom: 20px;
}

.modal-equipment-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.modal-equipment-icon :deep(svg) {
  width: 32px;
  height: 32px;
}


.modal-equipment-details h3 {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 6px;
}

.modal-equipment-details div input {
  border: 2px solid #e2e8f0;
  border-radius: 4px;
  font-size: 12px;
  color: #334155
}

.modal-equipment-details p {
  font-size: 14px;
  color: #64748b;
}

.modal-equipment-details div {
  display: flex;
  align-items: center;
}

.modal-equipment-details :deep(svg) {
  margin-left: 5px;
  cursor: pointer;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.modal-equipment-details :deep(svg):hover {
  cursor: pointer;
  transform: scale(1.02);
  opacity: 0.9;
}

.status-badge {
  display: inline-block;
  padding: 10px 20px;
  border-radius: 100px;
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 20px;
  user-select: none;
}

.status-badge.working {
  background: #dcfce7;
  color: #16a34a;
}

.status-badge.broken {
  background: #fee2e2;
  color: #dc2626;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 700;
  color: #334155;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-textarea {
  width: 100%;
  padding: 14px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 15px;
  transition: all 0.3s ease;
  font-family: inherit;
  min-height: 100px;
  resize: vertical;
}

.form-textarea::placeholder {
  color: #9ca3af;
}

.form-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
}

.action-btns {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.action-btn {
  flex: 1;
  padding: 14px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 15px;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.fix-btn {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
}

.fix-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(34, 197, 94, 0.4);
}

.break-btn {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
}

.break-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
}

.action-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
  opacity: 0.5;
}

.close-btn {
  width: 100%;
  background: #f1f5f9;
  color: #475569;
  padding: 14px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 15px;
  border: none;
  cursor: pointer;
  margin-top: 12px;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: #e2e8f0;
}

.cancel-btn {
  background: #f1f5f9;
  color: #475569;
}

.cancel-btn:hover {
  background: #e2e8f0;
}

/* Modal Transition */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-active .modal-content {
  animation: modalAppear 0.3s ease;
}

.modal-fade-leave-active .modal-content {
  animation: modalAppear 0.3s ease reverse;
}

@keyframes modalAppear {
  from { opacity: 0; transform: scale(0.9) translateY(-20px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

/* --- Контейнер секции файлов --- */
.hw-files-section {
  position: relative;
  margin-top: 15px;
  border-top: 1px solid #eee;
  padding-top: 10px;
  min-height: 100px;
}

.hw-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.hw-section-title {
  font-weight: 600;
  font-size: 14px;
  color: #333;
}

.hw-add-btn-small {
  display: flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: 1px dashed #1890ff;
  color: #1890ff;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}
.hw-add-btn-small:hover {
  background: #e6f7ff;
}
.hw-add-btn-small svg {
  width: 16px;
  height: 16px;
}

/* --- Сетка (Grid) --- */
.hw-files-grid {
  display: flex;
  flex-wrap: nowrap;
  overflow-x: auto;
  gap: 12px;
  margin-bottom: 15px;
  -webkit-overflow-scrolling: touch;
  scroll-behavior: smooth;
  scrollbar-width: thin;
  scrollbar-color: #c1c1c1 #f1f1f1;
  max-height: 180px;
  overflow-y: auto;
  /* Место для скролла */
  padding: 0 5px 0 4px;
}

.hw-no-files {
  color: #999;
  font-size: 13px;
  text-align: center;
  padding: 20px 0;
  border: 1px dashed #eee;
  border-radius: 6px;
}

.hw-drop-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(230, 247, 255, 0.95);
  border: 2px dashed #1890ff;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

.hw-drop-content {
  text-align: center;
  color: #1890ff;
  pointer-events: none;
}
.hw-drop-content p {
  margin-top: 10px;
  font-weight: 500;
}

/* --- Карточка файла --- */
.hw-file-card
{
  flex: 0 0 auto;
  width: 100px;
  height: 100px;
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  transition: transform 0.2s;
}

.hw-file-card:hover
{
  transform: translateY(-2px);
  border-color: #d1d5db;
  cursor: pointer;
}

/* Ползунок карусели файлов */
.hw-files-grid::-webkit-scrollbar {
  height: 6px;
}

.hw-files-grid::-webkit-scrollbar-track
{
  background: #f1f1f1;      /* Цвет дорожки */
  border-radius: 3px;
}

.hw-files-grid::-webkit-scrollbar-thumb
{
  background: #c1c1c1;      /* Цвет ползунка */
  border-radius: 3px;
}

.hw-files-grid::-webkit-scrollbar-thumb:hover
{
  background: #a8a8a8;      /* Цвет ползунка при наведении */
}

/* --- Превью (Картинка) --- */
.hw-file-preview {
  width: 100%;
  height: 100%;
  object-fit: cover; /* Заполняет квадрат, обрезая лишнее */
  display: block;
}

/* --- Заглушка для видео --- */
.hw-video-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #e9ecef;
  color: #6c757d;
  font-size: 0.7rem;
  font-weight: bold;
  letter-spacing: 1px;
}

/* --- Кнопка удаления --- */
.hw-delete-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 20px;
  height: 20px;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  border: none;
  border-radius: 50%;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: background 0.2s;
  z-index: 2;
  will-change: auto;
}

.hw-delete-btn:hover {
  background: rgba(220, 53, 69, 0.9); /* Красный при наведении */
}

/* Модалка подтверждения удаления файла*/
.hw-confirm-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(2px);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.2s ease;
}

/* Само окно */
.hw-confirm-box {
  background: white;
  padding: 24px;
  border-radius: 12px;
  width: 320px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.2);
  text-align: center;
  animation: scaleIn 0.2s ease;
}

.hw-confirm-title {
  margin: 0 0 10px 0;
  font-size: 1.25rem;
  color: #1f2937;
}

.hw-confirm-text {
  margin-bottom: 20px;
  color: #6b7280;
  font-size: 0.95rem;
  line-height: 1.4;
}

/* Чекбокс */
.hw-confirm-checkbox {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  font-size: 0.9rem;
  color: #4b5563;
  cursor: pointer;
  user-select: none;
}

.hw-confirm-checkbox input {
  margin-right: 8px;
  width: 16px;
  height: 16px;
  accent-color: #3b82f6;
}

/* Кнопки */
.hw-confirm-actions {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.hw-btn-cancel, .hw-btn-delete {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  font-size: 0.95rem;
  transition: opacity 0.2s;
}

.hw-btn-cancel {
  background: #f3f4f6;
  color: #374151;
}

.hw-btn-cancel:hover {
  background: #e5e7eb;
}

.hw-btn-delete {
  background: #ef4444;
  color: white;
}

.hw-btn-delete:hover {
  background: #dc2626;
}

/* Анимации */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scaleIn {
  from { transform: scale(0.9); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

/* Конец стилей модалки подтверждения удаления файла */

/* Просмотр фото и видео */
/* --- LIGHTBOX (Оверлей) --- */
.hw-lightbox {
  position: fixed;
  inset: 0; /* top:0, left:0, right:0, bottom:0 */
  background: rgba(0, 0, 0, 0.9); /* Очень темный фон */
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(5px);
  animation: fadeIn 0.2s ease;
}

/* --- Контент (обертка) --- */
.hw-lb-content {
  position: relative;
  max-width: 90vw;  /* Не шире 90% экрана */
  max-height: 90vh; /* Не выше 90% экрана */
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* --- Картинка и Видео --- */
.hw-lb-image, .hw-lb-video {
  max-width: 100%;
  max-height: 85vh; /* Оставляем место под подпись */
  object-fit: contain; /* Сохраняем пропорции */
  border-radius: 4px;
  box-shadow: 0 0 20px rgba(0,0,0,0.5);
}

/* --- Кнопки навигации (< >) --- */
.hw-lb-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  color: white;
  font-size: 3rem;
  cursor: pointer;
  padding: 20px;
  opacity: 0.6;
  transition: opacity 0.2s;
  z-index: 10001;
}

.hw-lb-nav:hover {
  opacity: 1;
}

.hw-lb-prev { left: 20px; }
.hw-lb-next { right: 20px; }

/* --- Кнопка закрытия (X) --- */
.hw-lb-close {
  position: absolute;
  top: 20px;
  right: 30px;
  background: transparent;
  border: none;
  color: white;
  font-size: 2.5rem;
  cursor: pointer;
  z-index: 10002;
  opacity: 0.7;
}

.hw-lb-close:hover { opacity: 1; }

/* --- Подпись --- */
.hw-lb-caption {
  margin-top: 10px;
  color: #ccc;
  font-family: sans-serif;
  font-size: 0.9rem;
}
/**/

/* Responsive */
@media (max-width: 1024px) {
  .equipment-grid
  {
    --cell-size: 70px;
    gap: 8px;
  }

  .grid-wrapper
  {
    justify-content: start;
  }

  .equipment-icon svg
  {
    width: 32px;
    height: 32px;
  }

  .equipment-label
  {
    font-size: 12px;
  }

  .header-container {
    flex-wrap: wrap;
  }

  .classroom-info {
    width: 100%;
    margin-bottom: 16px;
  }

  .grid-cell {
    width: 75px;
    height: 75px;
  }
  .equipment-icon {
    width: 40px;
    height: 40px;
  }
}

@media (max-width: 768px)
{
  .container {
    padding: 12px;
  }

  .header-container {
    padding: 16px;
  }

  .classroom-number {
    font-size: 22px;
  }

  .header-actions {
    width: 100%;
    order: 3;
  }

  .header-btn {
    flex: 1;
    justify-content: center;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .grid-wrapper {
    justify-content: flex-start;
  }

  .equipment-grid {
    --cell-size: 60px;
    gap: 8px;
    justify-content: start;
  }

  .grid-section {
    padding: 20px;
  }

  .grid-cell {
    width: 65px;
    height: 65px;
  }

  .equipment-icon {
    width: 36px;
    height: 36px;
  }

  .equipment-icon :deep(svg) {
    width: 20px;
    height: 20px;
  }

  .modal-content {
    padding: 14px;
  }

  .equipment-label{
    font-size: 9px;
  }

  .modal-close-upper
  {
    padding-top: 0;

    button
    {
      margin: 0;
    }
  }

}

@media (max-width: 480px) {
  .grid-cell { width: 55px; height: 55px; }
  .equipment-icon { width: 30px; height: 30px; }
  .equipment-icon :deep(svg) { width: 18px; height: 18px; }
}
</style>