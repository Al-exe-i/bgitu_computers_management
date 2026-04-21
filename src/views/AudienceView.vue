<script>
import api from "@/services/api.js";
import router from "@/router/index.js";
import {useNotificationsStore} from "@/stores/notifications.js";
import LoaderContainer from "@/components/Common/LoaderContainer.vue";
import {useAuthStore} from "@/stores/auth.js";
import {getApiUrl, getWsUrl} from "@/config/api.js";
import {useAudienceContext} from "@/stores/officeCtx.js";
import {markRaw} from "vue";

export default {
  name: 'AudienceView',
  components: { LoaderContainer},
  props: ['audienceId'],
  data() {
    return {
      classroom: null,
      loading: true,

      // workspace
      isWorkspace: false,
      workspaceWantsFullscreen: false, // Поставить false, если нужен только CSS-оверлей

      // Масштаб сетки
      scaleMode: 'auto',     // 'auto' | 'manual'
      uiScale: 1.0,          // 0.7 ... 1.4
      uiScaleMin: 0.6,
      uiScaleMax: 1.5,

      dropClassroomModalShow: false,

      selectedCell: null,

      equipmentTypes: markRaw({
        computer:{
          name: 'Компьютер',
          color: 'linear-gradient(145deg, #60a5fa 0%, #3b82f6 48%, #1d4ed8 100%)',
          icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"></rect><path d="M8 21h8M12 17v4"></path></svg>'
        },
        server: {
          name: 'Сервер',
          color: 'linear-gradient(135deg, #0f766e, #14b8a6)',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M20 3H4a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2M4 9V5h16v4zm16 4H4a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-4a2 2 0 0 0-2-2M4 19v-4h16v4z"/><path fill="currentColor" d="M17 6h2v2h-2zm-3 0h2v2h-2zm3 10h2v2h-2zm-3 0h2v2h-2z"/></svg>'
        },
        tv: {
          name: 'Телевизор',
          color: 'linear-gradient(145deg, #fb923c 0%, #f97316 50%, #c2410c 100%)',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 1920 1536"><path fill="currentColor" d="M1792 1120V160q0-13-9.5-22.5T1760 128H160q-13 0-22.5 9.5T128 160v960q0 13 9.5 22.5t22.5 9.5h1600q13 0 22.5-9.5t9.5-22.5m128-960v960q0 66-47 113t-113 47h-736v128h352q14 0 23 9t9 23v64q0 14-9 23t-23 9H544q-14 0-23-9t-9-23v-64q0-14 9-23t23-9h352v-128H160q-66 0-113-47T0 1120V160Q0 94 47 47T160 0h1600q66 0 113 47t47 113"/></svg>'
        },
        projector: {
          name: 'Проектор',
          color: 'linear-gradient(145deg, #a78bfa 0%, #8b5cf6 48%, #6d28d9 100%)',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 16 16"><g fill="currentColor"><path d="M14 7.5a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0M2.5 6a.5.5 0 0 0 0 1h4a.5.5 0 0 0 0-1zm0 2a.5.5 0 0 0 0 1h4a.5.5 0 0 0 0-1z"/><path d="M0 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2a1 1 0 0 1-1 1h-1a1 1 0 0 1-1-1H5a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1a2 2 0 0 1-2-2zm2-1a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V6a1 1 0 0 0-1-1z"/></g></svg>'
        },
        printer: {
          name: 'Принтер',
          color: 'linear-gradient(145deg, #34d399 0%, #10b981 48%, #047857 100%)',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 16 16"><g fill="currentColor"><path d="M5 1a2 2 0 0 0-2 2v1h10V3a2 2 0 0 0-2-2zm6 8H5a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-3a1 1 0 0 0-1-1"/><path d="M0 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2h-1v-2a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v2H2a2 2 0 0 1-2-2zm2.5 1a.5.5 0 1 0 0-1a.5.5 0 0 0 0 1"/></g></svg>'
        },
        switch: {
          name: 'Коммутатор',
          color: 'linear-gradient(145deg, #fbbf24 0%, #f59e0b 50%, #b45309 100%)',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 36 36"><path fill="currentColor" d="M32.26 13.15A7.49 7.49 0 0 1 22.57 7H7.13a2 2 0 0 0-1.91 1.41L2.09 18.48a2 2 0 0 0-.09.59V27a2 2 0 0 0 2 2h28a2 2 0 0 0 2-2v-7.94a2 2 0 0 0-.09-.59ZM8.92 25h-1.8v-3h1.8Zm5 0h-1.8v-3h1.8Zm5 0h-1.8v-3h1.8Zm5 0H22.1v-3h1.8Zm5 0H27.1v-3h1.8ZM31 19.4H5V18h26Z" class="clr-i-solid--badged clr-i-solid-path-1--badged"/><circle cx="30" cy="6" r="5" fill="currentColor" class="clr-i-solid--badged clr-i-solid-path-2--badged clr-i-badge"/><path fill="none" d="M0 0h36v36H0z"/></svg>'
        },
        router: {
          name: 'Роутер',
          color: 'linear-gradient(145deg, #22d3ee 0%, #06b6d4 48%, #0e7490 100%)',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 16 16"><g fill="currentColor"><path d="M5.525 3.025a3.5 3.5 0 0 1 4.95 0a.5.5 0 1 0 .707-.707a4.5 4.5 0 0 0-6.364 0a.5.5 0 0 0 .707.707"/><path d="M6.94 4.44a1.5 1.5 0 0 1 2.12 0a.5.5 0 0 0 .708-.708a2.5 2.5 0 0 0-3.536 0a.5.5 0 0 0 .707.707Z"/><path d="M2.974 2.342a.5.5 0 1 0-.948.316L3.806 8H1.5A1.5 1.5 0 0 0 0 9.5v2A1.5 1.5 0 0 0 1.5 13H2a.5.5 0 0 0 .5.5h2A.5.5 0 0 0 5 13h6a.5.5 0 0 0 .5.5h2a.5.5 0 0 0 .5-.5h.5a1.5 1.5 0 0 0 1.5-1.5v-2A1.5 1.5 0 0 0 14.5 8h-2.306l1.78-5.342a.5.5 0 1 0-.948-.316L11.14 8H4.86zM2.5 11a.5.5 0 1 1 0-1a.5.5 0 0 1 0 1m4.5-.5a.5.5 0 1 1 1 0a.5.5 0 0 1-1 0m2.5.5a.5.5 0 1 1 0-1a.5.5 0 0 1 0 1m1.5-.5a.5.5 0 1 1 1 0a.5.5 0 0 1-1 0m2 0a.5.5 0 1 1 1 0a.5.5 0 0 1-1 0"/><path d="M8.5 5.5a.5.5 0 1 1-1 0a.5.5 0 0 1 1 0"/></g></svg>'
        },
        other: {
          name: 'Другое',
          color: 'linear-gradient(145deg, #94a3b8 0%, #64748b 48%, #334155 100%)',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M10.358 9.938c1.082-.12 2.202-.12 3.284 0a.464.464 0 0 1 .409.4c.129 1.104.129 2.22 0 3.324a.464.464 0 0 1-.41.4a14.92 14.92 0 0 1-3.283 0a.464.464 0 0 1-.409-.4a14.324 14.324 0 0 1 0-3.324a.464.464 0 0 1 .41-.4"/><path fill="currentColor" fill-rule="evenodd" d="M15 2.25a.75.75 0 0 1 .75.75v2.927a2.929 2.929 0 0 1 2.308 2.323H21a.75.75 0 0 1 0 1.5h-2.788c.037.5.061 1 .073 1.5H20a.75.75 0 0 1 0 1.5h-1.715c-.012.5-.036 1-.073 1.5H21a.75.75 0 0 1 0 1.5h-2.942a2.929 2.929 0 0 1-2.308 2.323V21a.75.75 0 0 1-1.5 0v-2.774c-.498.035-.999.059-1.5.07V20a.75.75 0 0 1-1.5 0v-1.704a31.963 31.963 0 0 1-1.5-.07V21a.75.75 0 0 1-1.5 0v-2.927a2.929 2.929 0 0 1-2.308-2.323H3a.75.75 0 0 1 0-1.5h2.788c-.037-.5-.061-1-.074-1.5H4a.75.75 0 0 1 0-1.5h1.714c.013-.5.037-1 .074-1.5H3a.75.75 0 0 1 0-1.5h2.942A2.929 2.929 0 0 1 8.25 5.927V3a.75.75 0 0 1 1.5 0v2.774c.498-.035.999-.059 1.5-.07V4a.75.75 0 0 1 1.5 0v1.704c.501.011 1.002.035 1.5.07V3a.75.75 0 0 1 .75-.75m-1.192 6.197a16.407 16.407 0 0 0-3.616 0c-.898.1-1.626.808-1.732 1.717a15.808 15.808 0 0 0 0 3.672c.106.91.834 1.616 1.732 1.717c1.192.133 2.424.133 3.616 0a1.963 1.963 0 0 0 1.732-1.717c.143-1.22.143-2.452 0-3.672a1.963 1.963 0 0 0-1.732-1.717" clip-rule="evenodd"/></svg>'
        }
      }),

      specFieldMap: markRaw({
        computer: [
          { key: 'cpu_model', label: 'Процессор', type: 'text', placeholder: 'Например, Intel Core i5-10400' },
          { key: 'cpu_frequency_ghz', label: 'Частота', type: 'float', min: 0, step: 0.1, suffix: 'ГГц' },
          { key: 'cpu_cores', label: 'Ядра', type: 'int', min: 1, step: 1 },

          { key: 'ram_amount', label: 'ОЗУ', type: 'int', min: 1, step: 1 },
          { key: 'ram_unit', label: 'Ед. ОЗУ', type: 'select', options: ['mb', 'gb', 'tb'] },

          { key: 'storage_amount', label: 'ПЗУ', type: 'int', min: 1, step: 1 },
          { key: 'storage_unit', label: 'Ед. ПЗУ', type: 'select', options: ['mb', 'gb', 'tb'] },

          { key: 'purchase_year', label: 'Год закупки', type: 'int', min: 2000, max: 2100, step: 1 },
        ],

        server: [
          { key: 'cpu_model', label: 'Процессор', type: 'text', placeholder: 'Например, Intel Xeon Silver 4310' },
          { key: 'cpu_frequency_ghz', label: 'Частота', type: 'float', min: 0, step: 0.1, suffix: 'ГГц' },
          { key: 'cpu_cores', label: 'Ядра', type: 'int', min: 1, step: 1 },

          { key: 'ram_amount', label: 'ОЗУ', type: 'int', min: 1, step: 1 },
          { key: 'ram_unit', label: 'Ед. ОЗУ', type: 'select', options: ['mb', 'gb', 'tb'] },

          { key: 'storage_amount', label: 'ПЗУ', type: 'int', min: 1, step: 1 },
          { key: 'storage_unit', label: 'Ед. ПЗУ', type: 'select', options: ['mb', 'gb', 'tb'] },

          { key: 'purchase_year', label: 'Год закупки', type: 'int', min: 2000, max: 2100, step: 1 },
        ],

        switch: [
          { key: 'ports_count', label: 'Кол-во портов', type: 'int', min: 1, step: 1 },
          { key: 'managed', label: 'Тип', type: 'boolean-labels', trueLabel: 'Управляемый', falseLabel: 'Неуправляемый' },
        ],
      }),
      /*Редактирование инв номера и названия оборудования в модалке */
      invNumEdit: false,
      hwTitleEdit: false,
      newInv_no: ``,
      newHwTitle: ``,

      /* Состояние редактирования спецификаций */
      specsEdit: false,
      specsDraft: {},
      specsSaving: false,
      showSpecsModal: false,
      showStatusConfirmModal: false,
      pendingWorkingStatus: null,
      statusConfirmLoading: false,
      skipStatusConfirmSession: false,

      /* Раздел файлов оборудования в модалке */
      isDragOver: false,
      showConfirmModal: false,
      fileToDeleteId: null,
      dontAskAgain: false,

      /*WebSocket*/
      refreshTimer: null,
      refreshDebounceMs: 400,
      wsSuspendedUntil: 0,

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
    // Стата для админов
    stats() {
      const items = this.classroom?.equipment ?? [];

      const result = {
        total: 0,
        working: 0,
        broken: 0,
        computers: 0,
        servers: 0
      };

      for (const eq of items) {
        result.total++;
        if (eq.working) result.working++;
        else result.broken++;

        if (eq.type === 'computer') {
          result.computers++;
        }

        if (eq.type === 'server') {
          result.servers++;
        }
      }

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
    gridDensityClass() {
      if (!this.classroom) return '';

      const cols = this.classroom.gridSize.width;

      if (cols > 15) return 'density-tiny';    // >15 колонок: Очень мелко (как на телефоне)
      if (cols > 10) return 'density-compact'; // 11-15 колонок: Средне (как на планшете)
      return 'density-normal';                 // <=10 колонок: Стандарт
    },

    gridStyle() {
      const s = this.scaleMode === 'manual' ? this.uiScale : 1;
      return {
        '--grid-cols': this.classroom?.gridSize?.width ?? 1,
        '--grid-rows': this.classroom?.gridSize?.height ?? 1,
        '--ui-scale': s
      };
    },

    landmarkValues() {
      const source = this.classroom?.landmarks ?? {};
      const northValue =
          typeof source.north === 'string'
              ? source.north.trim()
              : typeof source.nord === 'string'
                  ? source.nord.trim()
                  : '';

      return {
        north: northValue,
        south: typeof source.south === 'string' ? source.south.trim() : '',
        west: typeof source.west === 'string' ? source.west.trim() : '',
        east: typeof source.east === 'string' ? source.east.trim() : ''
      };
    },

    occupiedMap() {
      const map = {};
      const items = this.classroom?.equipment ?? [];

      for (const item of items) {
        for (let dy = 0; dy < item.height; dy++) {
          for (let dx = 0; dx < item.width; dx++) {
            const row = item.y + dy;
            const col = item.x + dx;

            map[`${row}-${col}`] = {
              item,
              isAnchor: dx === 0 && dy === 0
            };
          }
        }
      }

      return map;
    },

    currentSpecFields() {
      const type = this.selectedCell?.data?.type;
      return this.specFieldMap[type] ?? [];
    },

    hasSpecsEditor() {
      return this.currentSpecFields.length > 0;
    },

    currentSpecGroups() {
      const type = this.selectedCell?.data?.type;

      if (type === 'computer' || type === 'server') {
        return [
          ['cpu_model'],
          ['cpu_frequency_ghz', 'cpu_cores'],
          ['ram_amount', 'ram_unit'],
          ['storage_amount', 'storage_unit'],
          ['purchase_year'],
        ];
      }

      if (type === 'switch') {
        return [
          ['ports_count', 'managed'],
        ];
      }

      return [];
    },

    currentSpecFieldMap() {
      return Object.fromEntries(
          this.currentSpecFields.map(field => [field.key, field])
      );
    },

    currentSpecsRows() {
      return this.selectedCell ? this.getSpecsRows(this.selectedCell.data) : [];
    },

    currentSpecsDisplayItems() {
      if (!this.selectedCell?.data) return [];

      const specs = this.selectedCell.data.specs ?? {};
      const items = [];
      const seen = new Set();

      for (const group of this.currentSpecGroups) {
        const isMemoryPair =
            group.length === 2 &&
            group[0].endsWith('_amount') &&
            group[1].endsWith('_unit');

        if (isMemoryPair) {
          const [leftKey, rightKey] = group;
          const leftField = this.currentSpecFieldMap[leftKey];
          const rightField = this.currentSpecFieldMap[rightKey];
          const leftRaw = specs[leftKey];
          const rightRaw = specs[rightKey];
          const leftValue =
              leftRaw !== null && leftRaw !== undefined && leftRaw !== '' ? `${leftRaw}` : null;
          const rightValue =
              rightRaw !== null && rightRaw !== undefined && rightRaw !== '' ? String(rightRaw).toUpperCase() : null;

          seen.add(leftKey);
          seen.add(rightKey);

          if (leftValue === null && rightValue === null) continue;

          items.push({
            key: `${leftKey}-${rightKey}`,
            type: 'pair',
            iconKey: leftKey,
            leftLabel: leftField?.label ?? leftKey,
            leftValue: leftValue ?? 'Не указано',
            rightLabel: rightField?.label ?? rightKey,
            rightValue: rightValue ?? 'Не указано'
          });

          continue;
        }

        for (const fieldKey of group) {
          seen.add(fieldKey);

          const field = this.currentSpecFieldMap[fieldKey];
          if (!field) continue;

          const value = this.formatSpecFieldValue(field, specs[fieldKey]);
          if (value === null) continue;

          items.push({
            key: fieldKey,
            type: 'single',
            iconKey: fieldKey,
            label: field.label,
            value
          });
        }
      }

      for (const field of this.currentSpecFields) {
        if (seen.has(field.key)) continue;

        const value = this.formatSpecFieldValue(field, specs[field.key]);
        if (value === null) continue;

        items.push({
          key: field.key,
          type: 'single',
          iconKey: field.key,
          label: field.label,
          value
        });
      }

      return items;
    },

    selectedEquipmentDisplayName() {
      const type = this.selectedCell?.data?.type;
      return this.selectedCell?.data?.title || this.getEquipmentType(type)?.name || 'Оборудование';
    },

    specsFilledCount() {
      return this.currentSpecsRows.length;
    },

    specsTotalCount() {
      return this.currentSpecFields.length;
    },

    specsCompletionPercent() {
      if (!this.specsTotalCount) return 0;
      return Math.round((this.specsFilledCount / this.specsTotalCount) * 100);
    },

    specsEntryStateClass() {
      if (!this.specsTotalCount || !this.specsFilledCount) return 'is-empty';
      if (this.specsFilledCount === this.specsTotalCount) return 'is-complete';
      return 'is-partial';
    },

    specsStatusLabel() {
      if (!this.specsTotalCount) return 'Дополнительные поля недоступны';
      if (!this.specsFilledCount) return 'Характеристики ещё не заполнены';
      if (this.specsFilledCount === this.specsTotalCount) return 'Характеристики заполнены';
      return `Заполнено ${this.specsFilledCount} из ${this.specsTotalCount} полей`;
    },

    specsTypeDescription() {
      const type = this.selectedCell?.data?.type;

      if (type === 'computer' || type === 'server') {
        return 'Процессор, оперативная память, накопитель и год закупки';
      }

      if (type === 'switch') {
        return 'Порты, тип управления и базовые сетевые параметры устройства';
      }

      return 'Технические характеристики оборудования.';
    },

    statusConfirmTargetIsWorking() {
      return this.pendingWorkingStatus === true;
    },

    statusConfirmTargetLabel() {
      if (this.pendingWorkingStatus === true) return 'Исправно';
      if (this.pendingWorkingStatus === false) return 'Неисправно';
      return '';
    },

    statusConfirmCurrentLabel() {
      return this.selectedCell?.data?.working ? 'Исправно' : 'Неисправно';
    },

    statusConfirmTitle() {
      if (this.pendingWorkingStatus === true) {
        return 'Подтвердить исправление?';
      }

      if (this.pendingWorkingStatus === false) {
        return 'Подтвердить отметку о неисправности?';
      }

      return 'Подтвердить изменение статуса';
    },

    statusConfirmDescription() {
      if (!this.selectedCell?.data) return '';

      if (this.pendingWorkingStatus === true) {
        return `Оборудование «${this.selectedEquipmentDisplayName}» будет помечено как исправное и вернётся в рабочий статус`;
      }

      if (this.pendingWorkingStatus === false) {
        return `Оборудование «${this.selectedEquipmentDisplayName}» будет отмечено как неисправное, это отразится в аудитории и статистике`;
      }

      return '';
    },

    statusConfirmHint() {
      const comment = this.selectedCell?.data?.comment?.trim?.() ?? '';

      if (this.pendingWorkingStatus === true) {
        return comment
            ? 'Текущий комментарий о проблеме будет очищен после подтверждения.'
            : 'Статус сменится без дополнительных изменений.';
      }

      if (this.pendingWorkingStatus === false) {
        return comment
            ? 'Текущий комментарий будет сохранён вместе с новым статусом.'
            : 'Комментарий не указан. При необходимости его можно добавить перед подтверждением.';
      }

      return '';
    },

    statusConfirmActionLabel() {
      if (this.pendingWorkingStatus === true) return 'Подтвердить исправность';
      if (this.pendingWorkingStatus === false) return 'Подтвердить неисправность';
      return 'Подтвердить';
    },

    statusConfirmActionClass() {
      return this.pendingWorkingStatus === true ? 'is-working' : 'is-broken';
    },

  },

  methods: {
    getApiUrl,
    async getAudience({ keepModal = true } = {}) {
      const modalState = keepModal && this.selectedCell
          ? {
            row: this.selectedCell.row,
            col: this.selectedCell.col,
            showSpecsModal: this.showSpecsModal
          }
          : null;

      try {
        const res = await api.get(`/audiences/${this.audienceId}`);

        this.classroom = this.mapBackendToFrontend(res.data);
        this.loading = false;

        this.audienceContext.setOffice(this.classroom.office_id);

        // если модалка открыта — можно просто переоткрыть на те же координаты
        if (modalState) {
          const { row, col, showSpecsModal } = modalState;
          this.closeModal();
          this.openModal(row, col);

          if (showSpecsModal && this.hasSpecsEditor) {
            this.showSpecsModal = true;
            this.specsDraft = JSON.parse(JSON.stringify(this.selectedCell?.data?.specs ?? {}));
          }
        }
      } catch (e) {
        this.loading = false;
        if(e?.status === 404)
          this.notify.warning("Нет такой аудитории")
        await router.push(`/`);
      }
    },

    scheduleRefresh() {
      if (Date.now() < this.wsSuspendedUntil) return;
      if (this.specsEdit || this.invNumEdit || this.hwTitleEdit) return;

      if (this.refreshTimer) clearTimeout(this.refreshTimer);
      this.refreshTimer = setTimeout(() => {
        this.getAudience({ keepModal: true });
      }, this.refreshDebounceMs);
    },

    mapBackendToFrontend(data) {
      return {
        number: data.id,
        floor: data.floor,

        landmarks: data.landmarks,

        gridSize: {
          width: data.width,
          height: data.height
        },

        equipment: (data.hardware ?? []).map(item => ({
          dbId: item.id,
          type: item.type,

          x: item.x,
          y: item.y,
          width: item.width ?? 1,
          height: item.height ?? 1,

          working: item.state,
          comment: item.description || '',
          invNumber: item.inv_number,
          title: item.title,
          files: item.files ?? [],
          specs: item.specs ?? {}
        })),

        office_id: data.office_id,
        description: data.description,
      };
    },

    getEquipment(row, col) {
      return this.occupiedMap[`${row}-${col}`]?.item ?? null;
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

    formatSpecFieldValue(field, rawValue) {
      if (rawValue === null || rawValue === undefined || rawValue === '') return null;

      let value = rawValue;

      if (field.type === 'boolean-labels') {
        value = value ? field.trueLabel : field.falseLabel;
      }

      if (field.type === 'select') {
        value = String(value).toUpperCase();
      }

      if (field.suffix) {
        value = `${value} ${field.suffix}`;
      }

      return value;
    },

    getSpecIcon(key) {
      const icons = {
        cpu_model: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><rect width="16" height="16" x="4" y="4" rx="2" ry="2"/><path d="M9 9h6v6H9zm0-8v3m6-3v3M9 20v3m6-3v3m5-14h3m-3 5h3M1 9h3m-3 5h3"/></g></svg>',
        cpu_frequency_ghz: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.636 19.364a9 9 0 1 1 12.728 0M16 9l-4 4"/></svg>',
        cpu_cores: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l2.7 5.47L21 9.4l-4.5 4.38l1.06 6.2L12 17.1L6.44 20l1.06-6.2L3 9.4l6.3-.93z"/></svg>',
        ram_amount: '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="512" viewBox="0 0 640 512"><path fill="currentColor" d="M640 130.94V96c0-17.67-14.33-32-32-32H32C14.33 64 0 78.33 0 96v34.94c18.6 6.61 32 24.19 32 45.06s-13.4 38.45-32 45.06V320h640v-98.94c-18.6-6.61-32-24.19-32-45.06s13.4-38.45 32-45.06M224 256h-64V128h64zm128 0h-64V128h64zm128 0h-64V128h64zM0 448h64v-26.67c0-8.84 7.16-16 16-16s16 7.16 16 16V448h128v-26.67c0-8.84 7.16-16 16-16s16 7.16 16 16V448h128v-26.67c0-8.84 7.16-16 16-16s16 7.16 16 16V448h128v-26.67c0-8.84 7.16-16 16-16s16 7.16 16 16V448h64v-96H0z"/></svg>',
        ram_unit: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16M4 12h16M4 17h10"></path></svg>',
        storage_amount: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="6" rx="7" ry="3"></ellipse><path d="M5 6v12c0 1.66 3.13 3 7 3s7-1.34 7-3V6"></path><path d="M5 12c0 1.66 3.13 3 7 3s7-1.34 7-3"></path></svg>',
        storage_unit: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 7h14M5 12h9M5 17h14"></path></svg>',
        purchase_year: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="16" rx="2"></rect><path d="M16 3v4M8 3v4M3 10h18"></path></svg>',
        ports_count: '<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><path fill="currentColor" d="M496 192h-48v-48c0-8.8-7.2-16-16-16h-48V80c0-8.8-7.2-16-16-16H144c-8.8 0-16 7.2-16 16v48H80c-8.8 0-16 7.2-16 16v48H16c-8.8 0-16 7.2-16 16v224c0 8.8 7.2 16 16 16h80V320h32v128h64V320h32v128h64V320h32v128h64V320h32v128h80c8.8 0 16-7.2 16-16V208c0-8.8-7.2-16-16-16"/></svg>',
        managed: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 4v5c0 4.5-3 7.5-7 9c-4-1.5-7-4.5-7-9V7z"></path><path d="M9.5 12l1.7 1.7L14.8 10"></path></svg>'
      };

      return icons[key] || '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8"></circle><path d="M12 8h.01M11 12h1v4h1"></path></svg>';
    },

    getSpecsRows(item) {
      const specs = item?.specs ?? {};
      const fields = this.specFieldMap[item?.type] ?? [];

      return fields
          .map(field => {
            const value = this.formatSpecFieldValue(field, specs[field.key]);
            if (value === null) return null;

            return {
              key: field.key,
              label: field.label,
              value
            };
          })
          .filter(Boolean);
    },

    normalizeSpecsDraft() {
      const type = this.selectedCell?.data?.type;
      const fields = this.specFieldMap[type] ?? [];
      const normalized = {};

      for (const field of fields) {
        let value = this.specsDraft[field.key];

        if (value === '' || value === null || value === undefined) {
          continue;
        }

        if (field.type === 'int') {
          const parsed = Number.parseInt(value, 10);
          if (!Number.isNaN(parsed)) normalized[field.key] = parsed;
          continue;
        }

        if (field.type === 'float') {
          const parsed = Number.parseFloat(value);
          if (!Number.isNaN(parsed)) normalized[field.key] = parsed;
          continue;
        }

        if (field.type === 'select') {
          normalized[field.key] = String(value).toLowerCase();
          continue;
        }

        if (field.type === 'boolean-labels') {
          if (typeof value === 'boolean') normalized[field.key] = value;
          continue;
        }

        normalized[field.key] = value;
      }

      return normalized;
    },

    async saveSpecs() {
      if (!this.selectedCell?.data?.dbId) return;

      const payload = this.normalizeSpecsDraft();
      this.specsSaving = true;
      this.wsSuspendedUntil = Date.now() + 1000;

      try {
        await api.patch(`/hardware/${this.selectedCell.data.dbId}`, {
          specs: payload
        });

        this.selectedCell.data.specs = payload;
        this.specsDraft = JSON.parse(JSON.stringify(payload));
        this.specsEdit = false;

        this.notify.success('Характеристики сохранены');
      } catch (err) {
        this.notify.error('Не удалось сохранить характеристики');
      } finally {
        this.specsSaving = false;
      }
    },

    cancelSpecsEdit() {
      this.specsDraft = JSON.parse(JSON.stringify(this.selectedCell?.data?.specs ?? {}));
      this.specsEdit = false;
    },

    openSpecsModal() {
      if (!this.hasSpecsEditor) return;

      this.specsDraft = JSON.parse(JSON.stringify(this.selectedCell?.data?.specs ?? {}));
      this.specsEdit = false;
      this.showSpecsModal = true;
    },

    closeSpecsModal() {
      this.showSpecsModal = false;
      this.cancelSpecsEdit();
    },

    openModal(row, col) {
      if (!this.authStore.isAuthenticated) return;

      const eq = this.getEquipment(row, col);
      if (!eq) return;

      this.selectedCell = {
        row,
        col,
        key: `${row}-${col}`,
        data: eq
      };

      this.newInv_no = eq.invNumber;
      this.newHwTitle = eq.title;

      this.specsEdit = false;
      this.specsDraft = JSON.parse(JSON.stringify(eq.specs ?? {}));
      this.showSpecsModal = false;
      this.showStatusConfirmModal = false;
      this.pendingWorkingStatus = null;
      this.statusConfirmLoading = false;
    },

    closeModal() {
      this.closeStatusConfirmModal();
      this.selectedCell = null;

      this.invNumEdit = false;
      this.hwTitleEdit = false;
      this.newHwTitle = this.newInv_no = ``;

      this.specsEdit = false;
      this.specsDraft = {};
      this.showSpecsModal = false;
    },

    async requestWorkingStatus(status) {
      if (!this.selectedCell || this.selectedCell.data.working === status || this.statusConfirmLoading) return;

      if (this.skipStatusConfirmSession) {
        this.statusConfirmLoading = true;
        await this.applyWorkingStatus(status);
        this.statusConfirmLoading = false;
        return;
      }

      this.pendingWorkingStatus = status;
      this.showStatusConfirmModal = true;
    },

    closeStatusConfirmModal() {
      if (this.statusConfirmLoading) return;

      this.showStatusConfirmModal = false;
      this.pendingWorkingStatus = null;
    },

    updateStatusConfirmSessionPreference() {
      if (this.skipStatusConfirmSession) {
        sessionStorage.setItem('hw_skip_status_confirm_session', 'true');
        return;
      }

      sessionStorage.removeItem('hw_skip_status_confirm_session');
    },

    async confirmWorkingStatus() {
      if (this.pendingWorkingStatus === null) return;

      this.statusConfirmLoading = true;
      const isUpdated = await this.applyWorkingStatus(this.pendingWorkingStatus);

      if (isUpdated) {
        this.showStatusConfirmModal = false;
        this.pendingWorkingStatus = null;
      }

      this.statusConfirmLoading = false;
    },

    async applyWorkingStatus(status) {
      if (!this.selectedCell) return false;

      const description = status === true ? `` : this.selectedCell.data.comment;
      this.wsSuspendedUntil = Date.now() + 1000;

      try {
        await api.patch(`/hardware/${this.selectedCell.data.dbId}`, {
          state: status,
          description
        });

        this.selectedCell.data.working = status;

        if (status) {
          this.selectedCell.data.comment = ``;
        }

        return true;
      } catch (err) {
        this.notify.error(`РќРµ СѓРґР°Р»РѕСЃСЊ РёР·РјРµРЅРёС‚СЊ СЃРѕСЃС‚РѕСЏРЅРёРµ С‚РµРєСѓС‰РµРіРѕ РѕР±РѕСЂСѓРґРѕРІР°РЅРёСЏ!`);
        return false;
      }
    },

    async setWorkingStatus(status) {
      if (this.selectedCell)
      {
        let description = status === true ? `` : this.selectedCell.data.comment

        this.wsSuspendedUntil = Date.now() + 1000;

        await api.patch(`/hardware/${this.selectedCell.data.dbId}`, {state: status, description: description}
        ).then(res => {
          this.selectedCell.data.working = status;
        }).catch(err => {
          this.notify.error(`Не удалось изменить состояние текущего оборудования!`)
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
        this.wsSuspendedUntil = Date.now() + 1000;

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
    connectWebSocket() {
      if (!this.classroom?.number) {
        return;
      }

      if (this.ws) {
        this.ws.onclose = null;
        this.ws.close();
      }

      this.ws = new WebSocket(`${getWsUrl()}?audience_id=${this.classroom.number}`);

      this.ws.onopen = () => {
        this.wsConnected = true;
        this.wsError = false;
        this.wsReconnectAttempts = 0;
        this.reconnectDelay = 1000;
      };

      this.ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg?.audience_updated === this.classroom?.number) {
          this.scheduleRefresh();
        }
      };

      this.ws.onclose = () => {
        this.wsConnected = false;

        if (this.wsReconnectAttempts < this.maxReconnectAttempts) {
          this.wsReconnectAttempts++;
          const delay = this.reconnectDelay * this.wsReconnectAttempts;

          this.notify.warning(`Соединение потеряно. Переподключение №${this.wsReconnectAttempts} через ${delay / 1000} с...`);

          setTimeout(() => this.connectWebSocket(), delay);
        } else {
          this.wsError = true;
          this.notify.error("Не удалось восстановить соединение с сервером");
          router.push(`/`);
        }
      };
    },

    closeWebSocket()
    {
      if(this.ws)
      {
        clearTimeout(this.refreshTimer)
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
        this.wsSuspendedUntil = Date.now() + 1000;
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
      if(!this.havePermission)
      {
        this.isDragOver = false;
        this.notify.warning("У вас недостаточно прав для выполнения данного действия!")
        return;
      }

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
        this.wsSuspendedUntil = Date.now() + 1000;
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
      if (this.previewIndex !== null) {
        this.previewIndex = index;
        return;
      }

      this.previewIndex = index;
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', this.handlePreviewKeys);
    },

    // Закрыть
    closePreview() {
      this.previewIndex = null;
      if (!this.isWorkspace) document.body.style.overflow = ''; // Если workspace активен — НЕ возвращаем скролл
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
    },

    toggleWorkspace() {
      const next = !this.isWorkspace;
      this.isWorkspace = next;


      if (next) {
        document.body.style.overflow = 'hidden';

        // нативный fullscreen (опционально)
        if (this.workspaceWantsFullscreen) {
          this.requestFullscreenSafe();
        }
      } else {
        // если preview не открыт — возвращаем скролл
        if (this.previewIndex === null) document.body.style.overflow = '';

        if (document.fullscreenElement) {
          document.exitFullscreen?.();
        }
      }
    },

    requestFullscreenSafe() {
      const el = this.$refs.gridSection;
      if (!el) return;
      el.requestFullscreen?.().catch(() => {
        // браузер мог запретить — тогда останется CSS-оверлей
      });
    },

    toggleScaleMode() {
      this.scaleMode = this.scaleMode === 'auto' ? 'manual' : 'auto';
      if (this.scaleMode === 'manual') {
        // стартуем с 100%, чтобы было предсказуемо
        this.uiScale = 1.0;
      }
    },

  },

  async mounted() {
    this.skipStatusConfirmSession = sessionStorage.getItem('hw_skip_status_confirm_session') === 'true';
    await this.getAudience();
    this.connectWebSocket();
  },

  beforeUnmount() {
    this.closeWebSocket()
    this.audienceContext.clear()
  }
};
</script>

<template>
  <LoaderContainer v-if="loading" />

  <div v-if="!loading" class="page-viewer" :class="{ workspace: isWorkspace }">
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
      <div v-if="havePermission" class="stats-section">
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

      <div v-if="classroom" class="grid-section" ref="gridSection" :class="{ workspace: isWorkspace }">
        <div class="grid-header">
          <h2 class="grid-title">Состояние оборудования</h2>
          <div class="grid-tools">
            <button class="switch-fullscreen-btn" @click="toggleWorkspace">
              <svg v-if="!isWorkspace" xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
                <title>Полноэкранный режим</title>
                <path fill="currentColor" d="m290 236.4l43.9-43.9a8.01 8.01 0 0 0-4.7-13.6L169 160c-5.1-.6-9.5 3.7-8.9 8.9L179 329.1c.8 6.6 8.9 9.4 13.6 4.7l43.7-43.7L370 423.7c3.1 3.1 8.2 3.1 11.3 0l42.4-42.3c3.1-3.1 3.1-8.2 0-11.3zm352.7 187.3c3.1 3.1 8.2 3.1 11.3 0l133.7-133.6l43.7 43.7a8.01 8.01 0 0 0 13.6-4.7L863.9 169c.6-5.1-3.7-9.5-8.9-8.9L694.8 179c-6.6.8-9.4 8.9-4.7 13.6l43.9 43.9L600.3 370a8.03 8.03 0 0 0 0 11.3zM845 694.9c-.8-6.6-8.9-9.4-13.6-4.7l-43.7 43.7L654 600.3a8.03 8.03 0 0 0-11.3 0l-42.4 42.3a8.03 8.03 0 0 0 0 11.3L734 787.6l-43.9 43.9a8.01 8.01 0 0 0 4.7 13.6L855 864c5.1.6 9.5-3.7 8.9-8.9zm-463.7-94.6a8.03 8.03 0 0 0-11.3 0L236.3 733.9l-43.7-43.7a8.01 8.01 0 0 0-13.6 4.7L160.1 855c-.6 5.1 3.7 9.5 8.9 8.9L329.2 845c6.6-.8 9.4-8.9 4.7-13.6L290 787.6L423.7 654c3.1-3.1 3.1-8.2 0-11.3z"></path>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024"><title>Выйти из полноэкранного режима</title><path fill="currentColor" d="M391 240.9c-.8-6.6-8.9-9.4-13.6-4.7l-43.7 43.7L200 146.3a8.03 8.03 0 0 0-11.3 0l-42.4 42.3a8.03 8.03 0 0 0 0 11.3L280 333.6l-43.9 43.9a8.01 8.01 0 0 0 4.7 13.6L401 410c5.1.6 9.5-3.7 8.9-8.9zm10.1 373.2L240.8 633c-6.6.8-9.4 8.9-4.7 13.6l43.9 43.9L146.3 824a8.03 8.03 0 0 0 0 11.3l42.4 42.3c3.1 3.1 8.2 3.1 11.3 0L333.7 744l43.7 43.7A8.01 8.01 0 0 0 391 783l18.9-160.1c.6-5.1-3.7-9.4-8.8-8.8m221.8-204.2L783.2 391c6.6-.8 9.4-8.9 4.7-13.6L744 333.6L877.7 200c3.1-3.1 3.1-8.2 0-11.3l-42.4-42.3a8.03 8.03 0 0 0-11.3 0L690.3 279.9l-43.7-43.7a8.01 8.01 0 0 0-13.6 4.7L614.1 401c-.6 5.2 3.7 9.5 8.8 8.9M744 690.4l43.9-43.9a8.01 8.01 0 0 0-4.7-13.6L623 614c-5.1-.6-9.5 3.7-8.9 8.9L633 783.1c.8 6.6 8.9 9.4 13.6 4.7l43.7-43.7L824 877.7c3.1 3.1 8.2 3.1 11.3 0l42.4-42.3c3.1-3.1 3.1-8.2 0-11.3z"/></svg>
            </button>

            <button class="scale-type-btn" @click="toggleScaleMode">
              {{ scaleMode === 'auto' ? 'Масштаб: авто' : `Масштаб: ${Math.round(uiScale*100)}%` }}
            </button>

            <div v-if="scaleMode === 'manual'" class="scale-controls">
              <input type="range"
                     :min="uiScaleMin"
                     :max="uiScaleMax"
                     step="0.05"
                     v-model.number="uiScale" />
            </div>

          </div>
          <p v-if="authStore.isAuthenticated" class="grid-info">Кликните по ячейке для деталей</p>
        </div>

        <div class="grid-landmarks-shell">
          <span
              v-if="landmarkValues.north"
              class="grid-landmark-line is-north"
          >
            {{ landmarkValues.north }}
          </span>

          <div class="grid-landmark-main">
            <span
                v-if="landmarkValues.west"
                class="grid-landmark-side is-west"
            >
              {{ landmarkValues.west }}
            </span>

            <div class="grid-wrapper">
              <div class="equipment-grid" :class="gridDensityClass" :style="gridStyle">
                <div class="grid-stage">
                  <div class="grid-base">
                    <template v-for="row in classroom.gridSize.height" :key="`row-${row}`">
                      <div
                          v-for="col in classroom.gridSize.width"
                          :key="`cell-${row}-${col}`"
                          class="grid-cell"
                          :class="getCellClasses(row - 1, col - 1)"
                          @click="openModal(row - 1, col - 1)"
                      />
                    </template>
                  </div>

                  <div class="grid-overlay">
                    <div
                        v-for="item in classroom.equipment"
                        :key="item.dbId"
                        class="grid-equipment"
                        :class="{
                        broken: !item.working,
                        working: item.working,
                        'is-wide': item.width > item.height,
                        'is-tall': item.height >= item.width
                      }"
                        :style="{
                        gridColumn: `${item.x + 1} / span ${item.width}`,
                        gridRow: `${item.y + 1} / span ${item.height}`
                      }"
                        @click.stop="openModal(item.y, item.x)"
                    >
                      <div
                          class="equipment-icon"
                          :style="{ background: getEquipmentType(item.type).color }"
                          v-html="getEquipmentType(item.type).icon"
                      ></div>

                      <div class="equipment-label">
                        {{ getEquipmentType(item.type).name }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <span
                v-if="landmarkValues.east"
                class="grid-landmark-side is-east"
            >
              {{ landmarkValues.east }}
            </span>
          </div>

          <span
              v-if="landmarkValues.south"
              class="grid-landmark-line is-south"
          >
            {{ landmarkValues.south }}
          </span>
        </div>
      </div>
    </div>

    <Transition>
      <div v-if="selectedCell" class="modal active equipment-modal" @click.self="closeModal">
        <div class="modal-content equipment-modal-content">
          <div class="modal-close-upper">
            <button @click="closeModal" class="close">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>

          <h2 class="modal-title">
            {{ getEquipmentType(selectedCell.data.type).name }}
            <span class="modal-subtitle">Ряд {{ selectedCell.row + 1 }}, Место {{ selectedCell.col + 1 }}</span>
          </h2>

          <div class="modal-equipment-info">
            <div
                class="modal-equipment-icon"
                :style="{ background: getEquipmentType(selectedCell.data.type).color }"
                v-html="getEquipmentType(selectedCell.data.type).icon"
            ></div>
            <div class="modal-equipment-details">
              <div v-if="!hwTitleEdit">
                <h3>{{ selectedCell.data.title || getEquipmentType(selectedCell.data.type).name }}</h3>
                <svg v-if="havePermission" @click="hwTitleEdit = true" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="m16.475 5.408l2.117 2.117m-.756-3.982L12.109 9.27a2.118 2.118 0 0 0-.58 1.082L11 13l2.648-.53c.41-.082.786-.283 1.082-.579l5.727-5.727a1.853 1.853 0 1 0-2.621-2.621"/><path d="M19 15v3a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h3"/></g></svg>
              </div>

              <div v-if="hwTitleEdit" class="modal-equipment-inline-edit is-title">
                <input v-model="newHwTitle" class="modal-equipment-inline-input">
                <svg @click="saveHwTitle" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20"><path fill="currentColor" d="m15.3 5.3l-6.8 6.8l-2.8-2.8l-1.4 1.4l4.2 4.2l8.2-8.2z"/></svg>
              </div>

              <div v-if="invNumEdit" class="modal-equipment-inline-edit is-inv">
                <input v-model="newInv_no" class="modal-equipment-inline-input">
                <svg @click="saveInv_no" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20"><path fill="currentColor" d="m15.3 5.3l-6.8 6.8l-2.8-2.8l-1.4 1.4l4.2 4.2l8.2-8.2z"/></svg>
              </div>

              <div v-if="!invNumEdit">
                <p>Инвентарный №: {{ selectedCell.data.invNumber || `н\\д` }}</p>
                <svg v-if="havePermission" @click="invNumEdit = true" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24">
                  <path fill="currentColor"
                        d="M3.995 17.207V19.5a.5.5 0 0 0 .5.5h2.298a.5.5 0 0 0 .353-.146l9.448-9.448l-3-3l-9.452 9.448a.5.5 0 0 0-.147.353m10.837-11.04l3 3l1.46-1.46a1 1 0 0 0 0-1.414l-1.585-1.586a1 1 0 0 0-1.414 0z"/>
                </svg>
              </div>
            </div>

            <div v-if="hasSpecsEditor" class="specs-entry-group">
              <div class="specs-entry-chip" :class="specsEntryStateClass">
                <span class="specs-entry-chip-dot"></span>
                <span class="specs-entry-chip-text">
                  <span class="specs-entry-chip-count">{{ specsFilledCount }}/{{ specsTotalCount }}</span>
                  <span class="specs-entry-chip-caption">заполнено</span>
                </span>
              </div>

              <button
                  type="button"
                  class="specs-entry-btn"
                  @click="openSpecsModal"
              >
                <span class="specs-entry-btn-label">Характеристики</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M10 17a1 1 0 0 1-.7-1.7l3.59-3.59L9.3 8.12a1 1 0 0 1 1.4-1.42l4.3 4.3a1 1 0 0 1 0 1.4l-4.3 4.3A1 1 0 0 1 10 17"/>
                </svg>
              </button>
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
                :disabled="!selectedCell.data.working"
            ></textarea>
          </div>

          <div class="action-btns">
            <button
                class="action-btn fix-btn"
                :disabled="selectedCell.data.working || statusConfirmLoading"
                @click="requestWorkingStatus(true)"
                v-if="havePermission"
            >
              Исправно
            </button>
            <button
                class="action-btn break-btn"
                :disabled="!selectedCell.data.working || statusConfirmLoading"
                @click="requestWorkingStatus(false)"
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
              <button v-if="havePermission" class="hw-add-btn-small" @click="$refs.fileInput.click()" title="Прикрепить файл">
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

                <button v-if="havePermission" @click.stop="requestDeleteFile(file.id)" class="hw-delete-btn" title="Удалить">
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
      <div
          v-if="selectedCell && showStatusConfirmModal"
          class="status-confirm-overlay"
          @click.self="closeStatusConfirmModal"
      >
        <div class="status-confirm-sheet" :class="statusConfirmActionClass">
          <button
              type="button"
              class="status-confirm-close"
              :disabled="statusConfirmLoading"
              @click="closeStatusConfirmModal"
              aria-label="Закрыть подтверждение"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>

          <div class="status-confirm-hero">
            <div
                class="status-confirm-icon"
                :style="{ background: getEquipmentType(selectedCell.data.type).color }"
                v-html="getEquipmentType(selectedCell.data.type).icon"
            ></div>

            <div class="status-confirm-copy">
              <span class="status-confirm-kicker">{{ getEquipmentType(selectedCell.data.type).name }}</span>
              <h3 class="status-confirm-title">{{ statusConfirmTitle }}</h3>
              <p class="status-confirm-text">{{ statusConfirmDescription }}</p>
            </div>
          </div>

          <div class="status-confirm-equipment">
            <div class="status-confirm-equipment-name">{{ selectedEquipmentDisplayName }}</div>
            <div class="status-confirm-equipment-meta">
              <span>Ряд {{ selectedCell.row + 1 }}</span>
              <span>Место {{ selectedCell.col + 1 }}</span>
              <span>Инв. № {{ selectedCell.data.invNumber || 'н/д' }}</span>
            </div>
          </div>

          <div class="status-confirm-flow">
            <div class="status-confirm-state is-current">
              <span class="status-confirm-state-label">Сейчас</span>
              <strong>{{ statusConfirmCurrentLabel }}</strong>
            </div>

            <div class="status-confirm-arrow" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14"></path>
                <path d="m13 6l6 6l-6 6"></path>
              </svg>
            </div>

            <div class="status-confirm-state is-target" :class="statusConfirmActionClass">
              <span class="status-confirm-state-label">Станет</span>
              <strong>{{ statusConfirmTargetLabel }}</strong>
            </div>
          </div>

          <div class="status-confirm-note" :class="statusConfirmActionClass">
            <div class="status-confirm-note-icon">
              <svg v-if="statusConfirmTargetIsWorking" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 6L9 17l-5-5"></path>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="9"></circle>
                <path d="M12 8v5"></path>
                <circle cx="12" cy="16.5" r="0.7" fill="currentColor" stroke="none"></circle>
              </svg>
            </div>
            <p>{{ statusConfirmHint }}</p>
          </div>

          <label class="status-confirm-session-toggle">
            <input
                v-model="skipStatusConfirmSession"
                type="checkbox"
                @change="updateStatusConfirmSessionPreference"
            >
            <span class="status-confirm-session-switch" aria-hidden="true">
              <span class="status-confirm-session-switch-thumb"></span>
            </span>
            <span class="status-confirm-session-copy">
              <strong>Не требовать подтверждения в этой сессии</strong>
              <span>Дальше состояние оборудования будет меняться сразу, без этого окна.</span>
            </span>
          </label>

          <div class="status-confirm-actions">
            <button
                type="button"
                class="status-confirm-btn is-cancel"
                :disabled="statusConfirmLoading"
                @click="closeStatusConfirmModal"
            >
              Отмена
            </button>
            <button
                type="button"
                class="status-confirm-btn is-submit"
                :class="statusConfirmActionClass"
                :disabled="statusConfirmLoading"
                @click="confirmWorkingStatus"
            >
              {{ statusConfirmLoading ? 'Сохраняем...' : statusConfirmActionLabel }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition>
      <div
          v-if="selectedCell && hasSpecsEditor && showSpecsModal"
          class="modal active"
          @click.self="closeSpecsModal"
      >
        <div class="modal-content specs-modal-content">
          <div class="modal-close-upper">
            <button @click="closeSpecsModal" class="close">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>

          <div class="specs-modal-hero">
            <div class="specs-modal-hero-main">
              <div
                  class="specs-modal-icon"
                  :style="{ background: getEquipmentType(selectedCell.data.type).color }"
                  v-html="getEquipmentType(selectedCell.data.type).icon"
              ></div>

              <div class="specs-modal-hero-copy">
                <h2 class="specs-modal-heading">Характеристики</h2>
                <div class="specs-modal-name">{{ selectedEquipmentDisplayName }}</div>
                <p class="specs-modal-description">{{ specsTypeDescription }}</p>
              </div>
            </div>

            <div class="specs-modal-meta">
              <div class="specs-meta-pill">
                <div class="specs-meta-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4 7h16M4 12h16M4 17h10"></path>
                  </svg>
                </div>
                <div class="specs-meta-copy">
                  <span class="specs-meta-label">Тип</span>
                  <span class="specs-meta-value">{{ getEquipmentType(selectedCell.data.type).name }}</span>
                </div>
              </div>

              <div class="specs-meta-pill">
                <div class="specs-meta-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="4" y="6" width="16" height="12" rx="2"></rect>
                    <path d="M8 10h8M8 14h5"></path>
                  </svg>
                </div>
                <div class="specs-meta-copy">
                  <span class="specs-meta-label">Инвентарный №</span>
                  <span class="specs-meta-value">{{ selectedCell.data.invNumber || 'н/д' }}</span>
                </div>
              </div>

              <div class="specs-meta-pill">
                <div class="specs-meta-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="9"></circle>
                    <path d="M12 7v5l3 3"></path>
                  </svg>
                </div>
                <div class="specs-meta-copy">
                  <span class="specs-meta-label">Заполнение</span>
                  <span class="specs-meta-value">{{ specsFilledCount }}/{{ specsTotalCount }}</span>
                </div>
              </div>
            </div>

            <div class="specs-modal-progress">
              <div class="specs-modal-progress-head">
                <span>{{ specsStatusLabel }}</span>
                <span>{{ specsCompletionPercent }}%</span>
              </div>

              <div class="specs-modal-progress-track">
                <span :style="{ width: `${specsCompletionPercent}%` }"></span>
              </div>
            </div>
          </div>

          <div class="specs-card specs-card-modal">
            <div class="specs-header">
              <div class="specs-header-copy">
                <div class="specs-title">{{ specsEdit ? 'Поля для заполнения' : 'Обзор параметров' }}</div>
                <div class="specs-header-subtitle">
                  {{ specsEdit ? 'Редактирование характеристик выбранного устройства' : 'Актуальные технические данные по выбранному устройству' }}
                </div>
              </div>

              <div v-if="havePermission" class="specs-actions">
                <button
                    v-if="!specsEdit"
                    class="specs-btn specs-btn-secondary"
                    @click="specsEdit = true"
                >
                  Изменить
                </button>

                <template v-else>
                  <button
                      class="specs-btn specs-btn-secondary"
                      @click="cancelSpecsEdit"
                      :disabled="specsSaving"
                  >
                    Отмена
                  </button>

                  <button
                      class="specs-btn specs-btn-primary"
                      @click="saveSpecs"
                      :disabled="specsSaving"
                  >
                    {{ specsSaving ? 'Сохранение...' : 'Сохранить' }}
                  </button>
                </template>
              </div>
            </div>

            <div v-if="!specsEdit" class="specs-view">
              <div v-if="currentSpecsDisplayItems.length > 0" class="specs-grid">
                <div
                    v-for="item in currentSpecsDisplayItems"
                    :key="item.key"
                    class="spec-card"
                    :class="{ 'spec-card-pair': item.type === 'pair' }"
                >
                  <div class="spec-card-icon" v-html="getSpecIcon(item.iconKey)"></div>

                  <div v-if="item.type === 'pair'" class="spec-card-copy spec-card-copy-pair">
                    <div class="spec-card-pair-col">
                      <span class="spec-card-label">{{ item.leftLabel }}</span>
                      <span class="spec-card-value">{{ item.leftValue }}</span>
                    </div>

                    <div class="spec-card-pair-divider"></div>

                    <div class="spec-card-pair-col">
                      <span class="spec-card-label">{{ item.rightLabel }}</span>
                      <span class="spec-card-value">{{ item.rightValue }}</span>
                    </div>
                  </div>

                  <div v-else class="spec-card-copy">
                    <span class="spec-card-label">{{ item.label }}</span>
                    <span class="spec-card-value">{{ item.value }}</span>
                  </div>
                </div>
              </div>

              <div v-else class="specs-empty">
                <div class="specs-empty-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M7 3h7l5 5v13H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2"></path>
                    <path d="M14 3v5h5"></path>
                    <path d="M9 13h6M9 17h4"></path>
                  </svg>
                </div>
                <div class="specs-empty-title">Характеристики пока не заполнены</div>
                <div class="specs-empty-text">
                  Добавьте технические данные оборудования, чтобы карточка была полной и информативной.
                </div>
              </div>
            </div>

            <div v-else class="specs-form">
              <div class="specs-form-banner">
                <div class="specs-form-banner-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 20h9"></path>
                    <path d="M16.5 3.5a2.12 2.12 0 1 1 3 3L7 19l-4 1l1-4z"></path>
                  </svg>
                </div>

                <div class="specs-form-banner-copy">
                  <div class="specs-form-banner-title">Редактирование характеристик</div>
                  <div class="specs-form-banner-text">
                    Заполняйте только подтверждённые данные. Пустые поля можно оставить без значения.
                  </div>
                </div>
              </div>

              <div
                  v-for="group in currentSpecGroups"
                  :key="group.join('-')"
                  class="spec-form-group"
                  :class="{
                    'spec-form-group-double': group.length === 2,
                    'spec-form-group-switch': group.includes('ports_count') && group.includes('managed')
                  }"
              >
                <div
                    v-for="fieldKey in group"
                    :key="fieldKey"
                    class="spec-form-row"
                    :class="{
                      'spec-form-row-compact': fieldKey === 'ports_count',
                      'spec-form-row-switch': fieldKey === 'managed'
                    }"
                >
                  <label class="spec-form-label">
                    {{ currentSpecFieldMap[fieldKey].label }}
                  </label>

                  <input
                      v-if="currentSpecFieldMap[fieldKey].type === 'text'"
                      v-model="specsDraft[fieldKey]"
                      class="spec-input"
                      type="text"
                      :placeholder="currentSpecFieldMap[fieldKey].placeholder || ''"
                  />

                  <div
                      v-else-if="currentSpecFieldMap[fieldKey].type === 'int' || currentSpecFieldMap[fieldKey].type === 'float'"
                      class="spec-input-wrap"
                  >
                    <input
                        v-model="specsDraft[fieldKey]"
                        class="spec-input"
                        :class="{
                          'spec-input-with-suffix': currentSpecFieldMap[fieldKey].suffix,
                          'spec-input-ports': fieldKey === 'ports_count'
                        }"
                        type="number"
                        :min="currentSpecFieldMap[fieldKey].min"
                        :max="currentSpecFieldMap[fieldKey].max"
                        :step="currentSpecFieldMap[fieldKey].step || 1"
                    />
                    <span
                        v-if="currentSpecFieldMap[fieldKey].suffix"
                        class="spec-suffix">
                      {{ currentSpecFieldMap[fieldKey].suffix }}
                    </span>
                  </div>

                  <select
                      v-else-if="currentSpecFieldMap[fieldKey].type === 'select'"
                      v-model="specsDraft[fieldKey]"
                      class="spec-input spec-select"
                      :disabled="
                      (fieldKey === 'ram_unit' && !specsDraft.ram_amount) ||
                      (fieldKey === 'storage_unit' && !specsDraft.storage_amount)
                   "
                  >
                    <option value="">Не выбрано</option>
                    <option
                        v-for="option in currentSpecFieldMap[fieldKey].options"
                        :key="option"
                        :value="option"
                    >
                      {{ String(option).toUpperCase() }}
                    </option>
                  </select>

                  <div
                      v-else-if="currentSpecFieldMap[fieldKey].type === 'boolean-labels'"
                      class="boolean-switch"
                      :class="{ 'boolean-switch-compact': fieldKey === 'managed' }"
                  >
                    <template v-if="fieldKey === 'managed'">
                      <div class="bool-segmented">
                        <button
                            type="button"
                            class="bool-segment-btn"
                            :class="{ active: specsDraft[fieldKey] === true }"
                            @click="specsDraft[fieldKey] = true"
                        >
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 3l7 4v5c0 4.5-3 7.5-7 9c-4-1.5-7-4.5-7-9V7z"></path>
                            <path d="M9.5 12l1.7 1.7L14.8 10"></path>
                          </svg>
                          <span>{{ currentSpecFieldMap[fieldKey].trueLabel }}</span>
                        </button>

                        <button
                            type="button"
                            class="bool-segment-btn"
                            :class="{ active: specsDraft[fieldKey] === false }"
                            @click="specsDraft[fieldKey] = false"
                        >
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="4" y="7" width="16" height="10" rx="2"></rect>
                            <path d="M8 12h8"></path>
                          </svg>
                          <span>{{ currentSpecFieldMap[fieldKey].falseLabel }}</span>
                        </button>
                      </div>

                      <button
                          type="button"
                          class="bool-clear-btn"
                          :class="{ active: specsDraft[fieldKey] === undefined || specsDraft[fieldKey] === null || specsDraft[fieldKey] === '' }"
                          @click="delete specsDraft[fieldKey]"
                          title="Очистить значение"
                          aria-label="Очистить значение"
                      >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M18 6L6 18M6 6l12 12"></path>
                        </svg>
                      </button>
                    </template>

                    <template v-else>
                      <button
                          type="button"
                          class="bool-btn"
                          :class="{ active: specsDraft[fieldKey] === true }"
                          @click="specsDraft[fieldKey] = true"
                      >
                        {{ currentSpecFieldMap[fieldKey].trueLabel }}
                      </button>

                      <button
                          type="button"
                          class="bool-btn"
                          :class="{ active: specsDraft[fieldKey] === false }"
                          @click="specsDraft[fieldKey] = false"
                      >
                        {{ currentSpecFieldMap[fieldKey].falseLabel }}
                      </button>

                      <button
                          type="button"
                          class="bool-btn bool-btn-muted"
                          :class="{ active: specsDraft[fieldKey] === undefined || specsDraft[fieldKey] === null || specsDraft[fieldKey] === '' }"
                          @click="delete specsDraft[fieldKey]"
                      >
                        Не указано
                      </button>
                    </template>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <Transition>
      <div v-if="dropClassroomModalShow" class="modal">
        <div class="modal-content pt-1">
          <h2 class="modal-title">Удаление аудитории</h2>
          <p style="font-size: 16px; color: #64748b; margin-bottom: 24px;">
            Вы уверены, что хотите удалить <strong>аудиторию №{{ audienceId }}</strong>?
          </p>
          <div class="warning-box">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
            </svg>
            <p>Сетка оборудования будет удалена безвозвратно. Это действие нельзя отменить.</p>
          </div>
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

.page-viewer.workspace .top-header,
.page-viewer.workspace .stats-section {
  display: none;
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
  padding: 10px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.switch-fullscreen-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px;
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  will-change: auto;
}

.switch-fullscreen-btn:hover {
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4);
  transform: translateY(-2px);
}

.switch-fullscreen-btn:hover svg {
  transform: scale(1.1);
}

.switch-fullscreen-btn svg {
  width: 24px;
  height: 24px;
  transition: transform 0.3s ease;
  will-change: auto;
}

.header-btn svg {
  width: 18px;
  height: 18px;
}

.edit-btn {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
  border: 2px solid rgba(59, 130, 246, 0.3);
}

.edit-btn:hover {
  background: #3b82f6;
  color: #fff;
  transform: translateY(-2px);
}

.delete-btn {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 2px solid rgba(239, 68, 68, 0.3);
}

.delete-btn:hover {
  background: #ef4444;
  color: #fff;
  transform: translateY(-2px);
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

.grid-section.workspace {
  position: fixed;
  inset: 0;
  z-index: 100;        /* выше AppHeader */
  border-radius: 0;
  margin: 0;
  padding: 16px;
  overflow: auto;
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

.grid-tools {
  display: flex;
  gap: 1rem;
}

.scale-type-btn {
  padding: 8px 16px;
  background: white;
  border: 1.5px solid #3b82f6;
  border-radius: 12px;
  color: #3b82f6;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  min-width: 127px;
}

.scale-type-btn:hover {
  background: #3b82f6;
  color: white;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.25);
}

.scale-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f0f9ff;
  border-radius: 12px;
  border: 1px solid #bfdbfe;
  padding-left: 1rem;
  padding-right: 1rem;

  input[type="range"] {
    appearance: none;
    -webkit-appearance: none;
    width: 180px;
    height: 18px;
    padding: 0;
    margin: 0;
    border: none;
    border-radius: 999px;
    background: transparent;
    outline: none;
    cursor: pointer;
  }

  input[type="range"]::-webkit-slider-runnable-track {
    height: 6px;
    border: none;
    border-radius: 999px;
    background: linear-gradient(90deg, #93c5fd 0%, #dbeafe 100%);
  }

  input[type="range"]::-webkit-slider-thumb {
    appearance: none;
    -webkit-appearance: none;
    width: 18px;
    height: 18px;
    background: white;
    border: 2px solid #3b82f6;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 1px 4px rgba(59, 130, 246, 0.3);
    margin-top: -6px;
  }

  input[type="range"]::-webkit-slider-thumb:hover {
    transform: scale(1.15);
  }

  input[type="range"]::-moz-range-track {
    height: 6px;
    border: none;
    border-radius: 999px;
    background: linear-gradient(90deg, #93c5fd 0%, #dbeafe 100%);
  }

  input[type="range"]::-moz-range-thumb {
    width: 18px;
    height: 18px;
    background: white;
    border: 2px solid #3b82f6;
    border-radius: 50%;
    cursor: pointer;
    transition: transform 0.2s ease;
    box-shadow: 0 1px 4px rgba(59, 130, 246, 0.3);
  }
}

.grid-info {
  font-size: 14px;
  color: #64748b;
}

.grid-landmarks-shell {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.grid-landmark-main {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
}

.grid-landmark-main > .grid-wrapper {
  grid-column: 2;
  min-width: 0;
}

.grid-landmark-side.is-west {
  grid-column: 1;
}

.grid-landmark-side.is-east {
  grid-column: 3;
}

.grid-landmark-line,
.grid-landmark-side {
  color: #64748b;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  line-height: 1.3;
}

.grid-landmark-line {
  display: block;
  text-align: center;
  overflow-wrap: anywhere;
}

.grid-landmark-side {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  max-width: 22px;
  min-height: 100%;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  overflow-wrap: anywhere;
}

.grid-landmark-side.is-west {
  transform: rotate(180deg);
}

.grid-wrapper {
  display: flex;
  justify-content: center;
  overflow-x: auto;
  padding: 20px 0;
  -webkit-overflow-scrolling: touch;
}

.grid-stage {
  position: relative;
  display: inline-block;
  line-height: 0;
}

.equipment-grid {
  --ui-scale: 1;

  --cell-size: calc(90px * var(--ui-scale));
  --icon-div-size: calc(48px * var(--ui-scale));
  --icon-size: calc(26px * var(--ui-scale));
  --font-size: calc(11px * var(--ui-scale));
  --icon-div-mb: calc(6px * var(--ui-scale));
  --equipment-label-fw: 600;

  --grid-gap: calc(12px * var(--ui-scale));
  --grid-padding: calc(24px * var(--ui-scale));
  --equipment-padding: calc(10px * var(--ui-scale));

  position: relative;
  display: inline-block;
  padding: var(--grid-padding);
  background: #f8fafc;
  border-radius: 16px;
  border: 2px dashed #cbd5e1;
  box-sizing: border-box;
  user-select: none;
}

.equipment-grid.density-compact {
  --cell-size: calc(70px * var(--ui-scale));
  --icon-div-size: calc(42px * var(--ui-scale));
  --icon-size: calc(24px * var(--ui-scale));
  --font-size: calc(11px * var(--ui-scale));
  --icon-div-mb: calc(3px * var(--ui-scale));
  --equipment-label-fw: 500;

  --grid-gap: calc(8px * var(--ui-scale));
  --equipment-padding: calc(8px * var(--ui-scale));
}

.equipment-grid.density-tiny {
  --cell-size: calc(52px * var(--ui-scale));
  --icon-div-size: calc(34px * var(--ui-scale));
  --icon-size: calc(20px * var(--ui-scale));
  --font-size: calc(0px * var(--ui-scale));
  --icon-div-mb: calc(0px * var(--ui-scale));
  --equipment-label-fw: 500;

  --grid-gap: calc(6px * var(--ui-scale));
  --equipment-padding: calc(6px * var(--ui-scale));
}

.equipment-grid.density-tiny .equipment-label {
  display: none;
}

.grid-base,
.grid-overlay {
  display: grid;
  grid-template-columns: repeat(var(--grid-cols), var(--cell-size));
  grid-template-rows: repeat(var(--grid-rows), var(--cell-size));
  gap: var(--grid-gap);
}

.grid-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.grid-overlay .grid-equipment {
  pointer-events: auto;
}

.grid-equipment {
  width: 100%;
  height: 100%;
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  box-sizing: border-box;

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;

  cursor: pointer;
  position: relative;
  transition: all 0.3s ease;
  animation: fadeInCell 0.4s ease forwards;
}

.grid-equipment:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
  border-color: #3b82f6;
}

.grid-equipment:hover .equipment-icon {
  transform: scale(1.08);
}

.grid-equipment.working {
  background:
      linear-gradient(135deg, rgba(240, 253, 244, 0.98) 0%, rgba(220, 252, 231, 0.98) 100%);
  border-color: rgba(134, 239, 172, 0.5);
}

.grid-equipment.broken {
  background:
      linear-gradient(135deg, rgba(254, 242, 242, 0.98) 0%, rgba(254, 226, 226, 0.98) 100%);
  border-color: rgba(252, 165, 165, 0.5);
}

.grid-equipment.is-wide {
  flex-direction: row;
  gap: calc(10px * var(--ui-scale));
}

.grid-equipment.is-wide .equipment-icon {
  margin-bottom: 0;
}

.grid-equipment.is-tall {
  flex-direction: column;
}

.grid-cell {
  width: var(--cell-size);
  height: var(--cell-size);
  box-sizing: border-box;
  border-radius: 12px;
  border: 1.5px dashed #cbd5e1;
  background: #ffffff;
  transition: background 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
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

.grid-cell.occupied {
  border-style: solid;
}

.grid-cell.empty:hover {
  border-color: #94a3b8;
  background: #f8fafc;
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
  transition: transform 0.28s ease;
  will-change: transform;
  flex-shrink: 0;
  box-shadow:
      inset 0 1px 0 rgba(255,255,255,0.22),
      0 6px 14px rgba(15, 23, 42, 0.14);
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
  line-height: 1.15;
  text-align: center;
  color: #334155;
  word-break: break-word;
  overflow-wrap: anywhere;
  max-width: 100%;
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
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.modal-equipment-details {
  flex: 1;
  min-width: 0;
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
  min-width: 0;
  width: 100%;
}

.modal-equipment-details h3,
.modal-equipment-details p {
  min-width: 0;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.modal-equipment-details h3 {
  flex: 0 6 auto;
  max-width: 100%;
}

.modal-equipment-details p {
  flex: 0 1 auto;
  max-width: 100%;
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

.specs-entry-btn {
  border: 1px solid #bfdbfe;
  border-radius: 10px;
  padding: 10px 14px;
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.specs-entry-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(59, 130, 246, 0.16);
}

.specs-entry-btn svg {
  margin-left: 0;
  opacity: 1;
}

.specs-entry-btn-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.specs-entry-group {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  flex-shrink: 0;
  width: 176px;
}

.specs-entry-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  max-width: 100%;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid #dbeafe;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 8px 18px rgba(148, 163, 184, 0.12);
}

.specs-entry-chip-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #94a3b8;
  flex-shrink: 0;
}

.specs-entry-chip-text {
  min-width: 0;
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  color: #475569;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.specs-entry-chip-count {
  font-weight: 800;
}

.specs-entry-chip-caption {
  opacity: 0.82;
}

.specs-entry-chip.is-partial {
  border-color: #bfdbfe;
  background: rgba(239, 246, 255, 0.92);
}

.specs-entry-chip.is-partial .specs-entry-chip-dot {
  background: #2563eb;
}

.specs-entry-chip.is-complete {
  border-color: #86efac;
  background: rgba(240, 253, 244, 0.94);
}

.specs-entry-chip.is-complete .specs-entry-chip-dot {
  background: #16a34a;
}

.specs-entry-chip.is-empty {
  border-color: #cbd5e1;
  background: rgba(248, 250, 252, 0.94);
}

.specs-card {
  margin-bottom: 20px;
  padding: 22px;
  background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 250, 252, 0.96)),
      #f8fafc;
  border: 1px solid rgba(203, 213, 225, 0.92);
  border-radius: 22px;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
}

.specs-card-modal {
  margin-bottom: 0;
}

.specs-modal-content {
  padding-top: 0;
  max-width: 680px;
  max-height: calc(100vh - 40px);
  overflow-y: auto;
  background:
      radial-gradient(circle at top left, rgba(96, 165, 250, 0.18), transparent 34%),
      linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}

.specs-modal-hero {
  margin-bottom: 18px;
  padding: 2px 0 0;
}

.specs-modal-hero-main {
  display: flex;
  gap: 18px;
  align-items: center;
  margin-bottom: 18px;
}

.specs-modal-icon {
  width: 68px;
  height: 68px;
  border-radius: 20px;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 16px 30px rgba(37, 99, 235, 0.22);
  flex-shrink: 0;
}

.specs-modal-icon :deep(svg) {
  width: 34px;
  height: 34px;
}

.specs-modal-hero-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.specs-modal-heading {
  margin: 0;
  color: #0f172a;
  font-size: 30px;
  line-height: 1.05;
  font-weight: 800;
}

.specs-modal-name {
  margin-top: 8px;
  color: #1e293b;
  font-size: 17px;
  font-weight: 700;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.specs-modal-description {
  margin: 10px 0 0;
  color: #64748b;
  font-size: 14px;
  line-height: 1.55;
}

.specs-modal-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.specs-meta-pill {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 14px 15px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(191, 219, 254, 0.9);
  box-shadow: 0 10px 24px rgba(148, 163, 184, 0.12);
  min-width: 0;
}

.specs-meta-icon {
  width: 38px;
  height: 38px;
  border-radius: 14px;
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  color: #2563eb;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.specs-meta-icon svg {
  width: 20px;
  height: 20px;
}

.specs-meta-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.specs-meta-label {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.specs-meta-value {
  color: #0f172a;
  font-size: 14px;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.specs-modal-progress {
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(219, 234, 254, 0.95);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.55);
}

.specs-modal-progress-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  color: #334155;
  font-size: 13px;
  font-weight: 700;
}

.specs-modal-progress-track {
  height: 10px;
  border-radius: 999px;
  background: #dbeafe;
  overflow: hidden;
}

.specs-modal-progress-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.28);
}

.specs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}

.specs-header-copy {
  min-width: 0;
}

.specs-title {
  font-size: 13px;
  font-weight: 700;
  color: #334155;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.specs-header-subtitle {
  color: #64748b;
  font-size: 14px;
  line-height: 1.45;
}

.specs-actions {
  display: flex;
  gap: 8px;
}

.specs-btn {
  border: none;
  border-radius: 10px;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.specs-btn-secondary {
  background: #e2e8f0;
  color: #334155;
}

.specs-btn-secondary:hover {
  background: #cbd5e1;
}

.specs-btn-primary {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
}

.specs-btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(59, 130, 246, 0.28);
}

.specs-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.specs-view {
  display: flex;
  flex-direction: column;
}

.specs-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.spec-card {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  min-width: 0;
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid rgba(191, 219, 254, 0.9);
  background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(239, 246, 255, 0.88)),
      #ffffff;
  box-shadow: 0 10px 26px rgba(148, 163, 184, 0.14);
}

.spec-card-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  color: #1d4ed8;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.spec-card-icon :deep(svg) {
  width: 22px;
  height: 22px;
}

.spec-card-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.spec-card-copy-pair {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  gap: 14px;
  align-items: stretch;
}

.spec-card-pair-col {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.spec-card-pair-divider {
  width: 1px;
  background: linear-gradient(180deg, rgba(191, 219, 254, 0.15), rgba(148, 163, 184, 0.7), rgba(191, 219, 254, 0.15));
  border-radius: 999px;
}

.spec-card-label {
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.spec-card-value {
  color: #0f172a;
  font-size: 16px;
  line-height: 1.35;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.specs-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  padding: 34px 24px;
  border-radius: 20px;
  border: 1px dashed #bfdbfe;
  background: linear-gradient(180deg, rgba(239, 246, 255, 0.78), rgba(248, 250, 252, 0.92));
}

.specs-empty-icon {
  width: 56px;
  height: 56px;
  border-radius: 18px;
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  color: #1d4ed8;
  display: flex;
  align-items: center;
  justify-content: center;
}

.specs-empty-icon svg {
  width: 28px;
  height: 28px;
}

.specs-empty-title {
  color: #0f172a;
  font-size: 16px;
  font-weight: 800;
}

.specs-empty-text {
  color: #64748b;
  font-size: 14px;
  line-height: 1.6;
  max-width: 380px;
}

.specs-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.specs-form-banner {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  padding: 16px 18px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.92), rgba(239, 246, 255, 0.88));
  border: 1px solid rgba(147, 197, 253, 0.9);
}

.specs-form-banner-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.22);
}

.specs-form-banner-icon svg {
  width: 22px;
  height: 22px;
}

.specs-form-banner-title {
  color: #0f172a;
  font-size: 15px;
  font-weight: 800;
  margin-bottom: 4px;
}

.specs-form-banner-text {
  color: #475569;
  font-size: 13px;
  line-height: 1.55;
}

.spec-form-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.spec-form-label {
  font-size: 13px;
  font-weight: 700;
  color: #334155;
}

.spec-input-wrap {
  position: relative;
}

.spec-input {
  width: 100%;
  min-height: 44px;
  padding: 12px 14px;
  border: 1px solid #cbd5e1;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.92);
  color: #0f172a;
  font-size: 14px;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.spec-input:focus {
  outline: none;
  border-color: #60a5fa;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.12);
}

.spec-select {
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  padding-right: 46px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20' fill='none'%3E%3Cpath d='m5 7.5l5 5l5-5' stroke='%2364748b' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
  background-size: 16px 16px;
}

.spec-input-wrap .spec-input-with-suffix {
  padding-right: 37px;
}

.spec-suffix {
  position: absolute;
  right: 0.8rem;
  top: 50%;
  transform: translateY(-50%);
  color: #64748b;
  font-size: 13px;
  pointer-events: none;
}

.boolean-switch {
  display: inline-flex;
  gap: 8px;
  flex-wrap: wrap;
}

.boolean-switch-compact {
  width: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
}

.bool-segmented {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  min-width: 0;
}

.bool-segment-btn {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 46px;
  padding: 12px 14px;
  border: 1px solid #cbd5e1;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.92);
  color: #334155;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.bool-segment-btn svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.bool-segment-btn span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bool-segment-btn.active {
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  border-color: #60a5fa;
  color: #1d4ed8;
  box-shadow: 0 10px 20px rgba(96, 165, 250, 0.18);
}

.bool-clear-btn {
  width: 40px;
  height: 40px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  background: rgba(248, 250, 252, 0.94);
  color: #64748b;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.bool-clear-btn svg {
  width: 16px;
  height: 16px;
}

.bool-clear-btn.active {
  background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
  border-color: #94a3b8;
  color: #334155;
}

.spec-input-ports {
  text-align: center;
  padding-left: 10px;
  padding-right: 10px;
}

.bool-btn {
  border: 1px solid #cbd5e1;
  border-radius: 14px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.92);
  color: #334155;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.bool-btn.active {
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  border-color: #60a5fa;
  color: #1d4ed8;
  box-shadow: 0 10px 20px rgba(96, 165, 250, 0.18);
}

.spec-form-group {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(226, 232, 240, 0.98);
}

.spec-form-group-double {
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.spec-form-group-switch {
  grid-template-columns: 112px minmax(0, 1fr);
  align-items: start;
}

.spec-form-row-compact {
  max-width: 112px;
}

.spec-form-row-switch {
  min-width: 0;
}

.bool-btn-muted {
  background: #f8fafc;
  color: #64748b;
  border-color: #cbd5e1;
}

.bool-btn-muted.active {
  background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
  border-color: #94a3b8;
  color: #334155;
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

.status-confirm-overlay {
  position: fixed;
  inset: 0;
  z-index: 2100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(10px);
  animation: fadeIn 0.2s ease;
}

.status-confirm-sheet {
  position: relative;
  width: min(100%, 560px);
  padding: 28px;
  border-radius: 28px;
  background:
      radial-gradient(circle at top right, rgba(59, 130, 246, 0.12), transparent 34%),
      radial-gradient(circle at 12% 14%, rgba(148, 163, 184, 0.1), transparent 28%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.98));
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 32px 70px rgba(15, 23, 42, 0.2);
  animation: scaleIn 0.2s ease;
  overflow: hidden;
}

.status-confirm-sheet.is-working {
  box-shadow:
      0 32px 70px rgba(15, 23, 42, 0.2),
      0 0 0 1px rgba(16, 185, 129, 0.06);
}

.status-confirm-sheet.is-broken {
  box-shadow:
      0 32px 70px rgba(15, 23, 42, 0.2),
      0 0 0 1px rgba(239, 68, 68, 0.05);
}

.status-confirm-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 40px;
  height: 40px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.78);
  color: #64748b;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.status-confirm-close:hover:not(:disabled) {
  color: #0f172a;
  background: white;
}

.status-confirm-close:disabled {
  cursor: wait;
  opacity: 0.7;
}

.status-confirm-close svg {
  width: 18px;
  height: 18px;
}

.status-confirm-hero {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 18px;
}

.status-confirm-icon {
  width: 64px;
  height: 64px;
  border-radius: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 14px 28px rgba(37, 99, 235, 0.2);
  flex-shrink: 0;
}

.status-confirm-icon :deep(svg) {
  width: 30px;
  height: 30px;
}

.status-confirm-copy {
  min-width: 0;
}

.status-confirm-kicker {
  display: inline-block;
  margin-bottom: 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #64748b;
}

.status-confirm-title {
  margin: 0 0 8px;
  padding-right: 48px;
  font-size: 26px;
  line-height: 1.05;
  letter-spacing: -0.03em;
  color: #0f172a;
}

.status-confirm-text {
  margin: 0;
  font-size: 15px;
  line-height: 1.6;
  color: #475569;
}

.status-confirm-equipment {
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(241, 245, 249, 0.82);
  border: 1px solid rgba(226, 232, 240, 0.95);
}

.status-confirm-equipment-name {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 8px;
  overflow-wrap: anywhere;
}

.status-confirm-equipment-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.status-confirm-equipment-meta span {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.86);
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
}

.status-confirm-flow {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  margin: 18px 0;
}

.status-confirm-state {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px 18px;
  border-radius: 20px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  background: rgba(255, 255, 255, 0.92);
}

.status-confirm-state-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #94a3b8;
}

.status-confirm-state strong {
  font-size: 17px;
  color: #0f172a;
}

.status-confirm-state.is-target.is-working {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(110, 231, 183, 0.12));
  border-color: rgba(16, 185, 129, 0.28);
}

.status-confirm-state.is-target.is-broken {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.12), rgba(251, 113, 133, 0.12));
  border-color: rgba(239, 68, 68, 0.24);
}

.status-confirm-arrow {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(226, 232, 240, 0.75);
  color: #64748b;
}

.status-confirm-arrow svg {
  width: 18px;
  height: 18px;
}

.status-confirm-note {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 6px;
  border-radius: 14px;
  margin-bottom: 20px;
  background: rgba(241, 245, 249, 0.95);
  border: 1px solid rgba(226, 232, 240, 0.95);
}

.status-confirm-note.is-working {
  background: linear-gradient(135deg, rgba(236, 253, 245, 0.96), rgba(209, 250, 229, 0.94));
  border-color: rgba(16, 185, 129, 0.2);
}

.status-confirm-note.is-broken {
  background: linear-gradient(135deg, rgba(255, 241, 242, 0.96), rgba(255, 228, 230, 0.94));
  border-color: rgba(239, 68, 68, 0.16);
}

.status-confirm-note-icon {
  width: 36px;
  height: 36px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.8);
}

.status-confirm-note.is-working .status-confirm-note-icon {
  color: #059669;
}

.status-confirm-note.is-broken .status-confirm-note-icon {
  color: #dc2626;
}

.status-confirm-note-icon svg {
  width: 18px;
  height: 18px;
}

.status-confirm-note p {
  margin: 0;
  font-size: 14px;
  line-height: 1.55;
  color: #475569;
}

.status-confirm-session-toggle {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  margin-bottom: 20px;
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(226, 232, 240, 0.95);
  cursor: pointer;
  user-select: none;
}

.status-confirm-session-toggle input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.status-confirm-session-switch {
  position: relative;
  width: 46px;
  height: 28px;
  margin-top: 2px;
  flex-shrink: 0;
  border-radius: 999px;
  background: #cbd5e1;
  transition: background-color 0.22s ease, box-shadow 0.22s ease;
}

.status-confirm-session-switch-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: white;
  box-shadow: 0 3px 10px rgba(15, 23, 42, 0.16);
  transition: transform 0.22s ease;
}

.status-confirm-session-toggle input:checked + .status-confirm-session-switch {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  box-shadow: 0 8px 18px rgba(37, 99, 235, 0.18);
}

.status-confirm-session-toggle input:checked + .status-confirm-session-switch .status-confirm-session-switch-thumb {
  transform: translateX(18px);
}

.status-confirm-session-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.status-confirm-session-copy strong {
  font-size: 14px;
  color: #0f172a;
}

.status-confirm-session-copy span {
  font-size: 13px;
  line-height: 1.5;
  color: #64748b;
}

.status-confirm-actions {
  display: flex;
  gap: 12px;
}

.status-confirm-btn {
  flex: 1;
  min-height: 50px;
  border-radius: 16px;
  border: none;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
}

.status-confirm-btn:disabled {
  cursor: wait;
  opacity: 0.72;
  transform: none;
}

.status-confirm-btn.is-cancel {
  background: #eef2f7;
  color: #475569;
}

.status-confirm-btn.is-cancel:hover:not(:disabled) {
  background: #e2e8f0;
}

.status-confirm-btn.is-submit {
  color: white;
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.12);
}

.status-confirm-btn.is-submit.is-working {
  background: linear-gradient(135deg, #10b981, #059669);
}

.status-confirm-btn.is-submit.is-broken {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}

.status-confirm-btn.is-submit:hover:not(:disabled) {
  transform: translateY(-1px);
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

/* Модалка подтверждения удаления аудитории */
.warning-box {
  background: linear-gradient(135deg, #fff5f5 0%, #ffe5e5 100%);
  border: 1px solid #ff6b6b;
  padding: 16px 20px;
  border-radius: 12px;
  margin-bottom: 32px;
  display: flex;
  align-items: start;
  gap: 12px;
}

.warning-box p {
  font-size: 14px;
  color: #dc2626;
  line-height: 1.5;
  margin: 0;
}

.warning-box svg {
  width: 20px;
  height: 20px;
  color: #e41c1c;
  flex-shrink: 0;
  margin-top: 2px;
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
  padding: 10px 5px 0 0;
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
  .equipment-grid {
    --cell-size: calc(70px * var(--ui-scale));
    --icon-div-size: calc(40px * var(--ui-scale));
    --icon-size: calc(22px * var(--ui-scale));
    --font-size: calc(11px * var(--ui-scale));
    --grid-gap: calc(8px * var(--ui-scale));
  }

  .grid-wrapper {
    justify-content: start;
  }

  .header-container {
    flex-wrap: wrap;
  }

  .classroom-info {
    width: 100%;
    margin-bottom: 16px;
  }
}

@media (max-width: 768px) {
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

  .equipment-label {
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
  }

  .scale-type-btn,
  .scale-controls {
    display: none;
  }

  .status-confirm-overlay {
    align-items: center;
    padding: 16px 12px;
  }

  .status-confirm-sheet {
    width: min(100%, 440px);
    max-width: 440px;
    max-height: min(78vh, 680px);
    overflow-y: auto;
    padding: 18px 16px 14px;
    border-radius: 24px;
    scrollbar-width: none;
  }

  .status-confirm-sheet::-webkit-scrollbar {
    display: none;
  }

  .status-confirm-close {
    top: 12px;
    right: 12px;
    width: 34px;
    height: 34px;
    border-radius: 12px;
  }

  .status-confirm-close svg {
    width: 16px;
    height: 16px;
  }

  .status-confirm-hero {
    gap: 12px;
    margin-bottom: 14px;
  }

  .status-confirm-icon {
    width: 52px;
    height: 52px;
    border-radius: 18px;
  }

  .status-confirm-icon :deep(svg) {
    width: 24px;
    height: 24px;
  }

  .status-confirm-kicker {
    display: none;
  }

  .status-confirm-title {
    font-size: 20px;
    line-height: 1.08;
    padding-right: 28px;
    margin-bottom: 4px;
  }

  .status-confirm-text {
    font-size: 13px;
    line-height: 1.45;
  }

  .status-confirm-equipment {
    padding: 12px 14px;
    border-radius: 16px;
  }

  .status-confirm-equipment-name {
    font-size: 16px;
    margin-bottom: 6px;
  }

  .status-confirm-equipment-meta {
    gap: 6px;
  }

  .status-confirm-equipment-meta span {
    padding: 5px 8px;
    font-size: 11px;
  }

  .status-confirm-flow {
    grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
    gap: 8px;
    margin: 14px 0;
  }

  .status-confirm-state {
    padding: 12px 10px;
    border-radius: 16px;
    text-align: center;
    align-items: center;
  }

  .status-confirm-state-label {
    font-size: 10px;
  }

  .status-confirm-state strong {
    font-size: 15px;
  }

  .status-confirm-arrow {
    width: 34px;
    height: 34px;
    border-radius: 12px;
  }

  .status-confirm-arrow svg {
    width: 16px;
    height: 16px;
    transform: none;
  }

  .status-confirm-note {
    padding: 12px 14px;
    gap: 10px;
    border-radius: 16px;
    margin-bottom: 14px;
  }

  .status-confirm-note-icon {
    width: 30px;
    height: 30px;
    border-radius: 11px;
  }

  .status-confirm-note-icon svg {
    width: 16px;
    height: 16px;
  }

  .status-confirm-note p {
    font-size: 12px;
    line-height: 1.45;
  }

  .status-confirm-session-toggle {
    gap: 10px;
    padding: 12px 14px;
    margin-bottom: 14px;
    border-radius: 16px;
  }

  .status-confirm-session-switch {
    width: 40px;
    height: 24px;
    margin-top: 1px;
  }

  .status-confirm-session-switch-thumb {
    top: 3px;
    left: 3px;
    width: 18px;
    height: 18px;
  }

  .status-confirm-session-toggle input:checked + .status-confirm-session-switch .status-confirm-session-switch-thumb {
    transform: translateX(16px);
  }

  .status-confirm-session-copy {
    gap: 2px;
  }

  .status-confirm-session-copy strong {
    font-size: 13px;
  }

  .status-confirm-session-copy span {
    font-size: 11px;
    line-height: 1.4;
  }

  .status-confirm-actions {
    display: grid;
    grid-template-columns: minmax(0, 0.92fr) minmax(0, 1.08fr);
    gap: 10px;
  }

  .status-confirm-btn {
    min-height: 44px;
    border-radius: 14px;
    font-size: 14px;
  }

  .grid-info {
    display: none;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .grid-wrapper {
    justify-content: flex-start;
  }

  .equipment-grid {
    --cell-size: calc(60px * var(--ui-scale));
    --icon-div-size: calc(36px * var(--ui-scale));
    --icon-size: calc(20px * var(--ui-scale));
    --font-size: calc(9px * var(--ui-scale));
    --grid-gap: calc(8px * var(--ui-scale));
  }

  .grid-section {
    padding: 20px;
  }

  .grid-landmarks-shell {
    gap: 8px;
  }

  .grid-landmark-main {
    grid-template-columns: 18px minmax(0, 1fr) 18px;
    gap: 8px;
  }

  .grid-landmark-main > .grid-wrapper {
    grid-column: 2;
  }

  .grid-landmark-line,
  .grid-landmark-side {
    font-size: 10px;
    letter-spacing: 0.1em;
  }

  .grid-landmark-side {
    min-width: 18px;
    max-width: 18px;
  }

  .modal-content {
    padding: 14px;
  }

  .equipment-modal {
    padding: 12px;
  }

  .equipment-modal .modal-content {
    width: min(100%, 460px);
    max-width: 460px;
    max-height: calc(100vh - 24px);
    max-height: calc(100dvh - 24px);
    overflow-y: auto;
    padding: 12px 14px 16px;
    border-radius: 22px;
    scrollbar-width: none;
    overscroll-behavior: contain;
  }

  .equipment-modal .modal-content::-webkit-scrollbar {
    display: none;
  }

  .equipment-modal .modal-close-upper {
    padding-top: 0;
    margin-bottom: 4px;
  }

  .equipment-modal .modal-close-upper button {
    width: 36px;
    height: 36px;
    margin: 0;
    border-radius: 12px;
  }

  .equipment-modal .modal-title {
    font-size: 20px;
    line-height: 1.08;
    margin-bottom: 12px;
  }

  .equipment-modal .modal-subtitle {
    font-size: 12px;
  }

  .modal-equipment-info {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .equipment-modal .modal-equipment-info {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr);
    align-items: start;
    gap: 12px;
    padding: 14px;
    margin-bottom: 14px;
    border-radius: 16px;
  }

  .equipment-modal .modal-equipment-icon {
    width: 52px;
    height: 52px;
    border-radius: 16px;
  }

  .equipment-modal .modal-equipment-icon :deep(svg) {
    width: 26px;
    height: 26px;
  }

  .equipment-modal .modal-equipment-details h3 {
    font-size: 16px;
    margin-bottom: 4px;
  }

  .equipment-modal .modal-equipment-details p {
    font-size: 13px;
    line-height: 1.45;
  }

  .equipment-modal .modal-equipment-details div input {
    width: 100%;
    min-height: 38px;
    padding: 8px 10px;
    font-size: 13px;
    border-radius: 10px;
  }

  .equipment-modal .modal-equipment-inline-edit {
    width: auto;
    max-width: 100%;
    align-items: center;
    gap: 6px;
  }

  .equipment-modal .modal-equipment-inline-input {
    width: clamp(148px, 62vw, 220px);
    max-width: 100%;
    flex: 0 1 auto;
    min-height: 30px;
    height: 30px;
    padding: 2px 8px;
    font-size: 12px;
    line-height: 1;
    border-radius: 8px;
    border-width: 1px;
    box-sizing: border-box;
  }

  .equipment-modal .modal-equipment-inline-edit.is-inv .modal-equipment-inline-input {
    width: clamp(118px, 48vw, 176px);
  }

  .equipment-modal .modal-equipment-inline-edit :deep(svg) {
    width: 16px;
    height: 16px;
    margin-left: 2px;
  }

  .specs-entry-btn {
    width: 100%;
    justify-content: center;
    min-width: 0;
  }

  .specs-entry-group {
    width: 100%;
    display: grid;
    grid-template-columns: auto minmax(0, 1fr);
    align-items: center;
    gap: 8px;
  }

  .equipment-modal .specs-entry-group {
    grid-column: 1 / -1;
  }

  .specs-entry-chip {
    align-self: center;
    justify-self: start;
  }

  .equipment-modal .specs-entry-chip {
    max-width: 100%;
  }

  .equipment-modal .specs-entry-btn {
    min-height: 42px;
    padding: 10px 12px;
    border-radius: 12px;
  }

  .equipment-modal .status-badge {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    padding: 8px 12px;
    margin-bottom: 14px;
    border-radius: 14px;
    font-size: 12px;
    text-align: center;
  }

  .equipment-modal .form-group {
    margin-bottom: 14px;
  }

  .equipment-modal .form-label {
    margin-bottom: 6px;
    font-size: 12px;
  }

  .equipment-modal .form-textarea {
    min-height: 88px;
    padding: 12px 14px;
    border-radius: 14px;
    font-size: 14px;
  }

  .equipment-modal .action-btns {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    margin-top: 16px;
  }

  .equipment-modal .action-btns > .action-btn:only-child {
    grid-column: 1 / -1;
  }

  .equipment-modal .action-btn {
    min-height: 44px;
    padding: 12px 10px;
    border-radius: 14px;
    font-size: 14px;
  }

  .equipment-modal .hw-files-section {
    margin-top: 14px;
    padding-top: 12px;
    min-height: 0;
  }

  .equipment-modal .hw-section-header {
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 8px;
  }

  .equipment-modal .hw-section-title {
    font-size: 13px;
  }

  .equipment-modal .hw-add-btn-small {
    padding: 5px 9px;
    border-radius: 10px;
    font-size: 12px;
  }

  .equipment-modal .hw-files-grid {
    gap: 10px;
    max-height: 156px;
    margin-bottom: 10px;
    padding: 6px 2px 0 0;
  }

  .equipment-modal .hw-file-card {
    width: 88px;
    height: 88px;
    border-radius: 12px;
  }

  .equipment-modal .hw-no-files {
    padding: 14px 0;
    border-radius: 12px;
    font-size: 12px;
  }

  .specs-modal-hero-main {
    flex-direction: column;
  }

  .specs-modal-meta,
  .specs-grid,
  .spec-form-group-double {
    grid-template-columns: 1fr;
  }

  .spec-form-group-switch {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .specs-header {
    flex-direction: column;
    align-items: stretch;
  }

  .specs-actions {
    width: 100%;
  }

  .specs-actions .specs-btn {
    flex: 1;
    justify-content: center;
  }

  .boolean-switch-compact {
    grid-template-columns: 1fr;
  }

  .bool-clear-btn {
    width: 100%;
    height: 38px;
  }

  .spec-form-row-compact {
    max-width: 132px;
  }

  .spec-form-row-switch {
    width: 100%;
  }

  .spec-card-copy-pair {
    grid-template-columns: minmax(0, 1fr) auto minmax(72px, auto);
    gap: 10px;
    align-items: center;
  }

  .spec-card-pair-col:last-child {
    align-items: flex-end;
    text-align: right;
  }

  .spec-card {
    padding: 14px;
  }

  .modal-close-upper {
    padding-top: 0;
  }

  .modal-close-upper button {
    margin: 0;
  }
}

@media (max-width: 480px) {
  .equipment-modal {
    padding: 10px;
  }

  .equipment-modal .modal-content {
    max-height: calc(100vh - 20px);
    max-height: calc(100dvh - 20px);
    padding: 12px 12px 14px;
    border-radius: 20px;
  }

  .equipment-modal .modal-title {
    font-size: 18px;
  }

  .grid-landmark-line,
  .grid-landmark-side {
    font-size: 9px;
    letter-spacing: 0.08em;
  }

  .grid-landmark-side {
    min-width: 16px;
    max-width: 16px;
  }

  .equipment-modal .modal-equipment-info {
    padding: 12px;
    gap: 10px;
  }

  .equipment-modal .modal-equipment-icon {
    width: 48px;
    height: 48px;
    border-radius: 14px;
  }

  .equipment-modal .modal-equipment-icon :deep(svg) {
    width: 24px;
    height: 24px;
  }

  .equipment-modal .modal-equipment-inline-input {
    width: clamp(136px, 58vw, 196px);
    min-height: 28px;
    height: 28px;
    padding: 1px 7px;
    font-size: 11px;
    line-height: 1;
    border-radius: 8px;
  }

  .equipment-modal .modal-equipment-inline-edit.is-inv .modal-equipment-inline-input {
    width: clamp(112px, 44vw, 156px);
  }

  .equipment-modal .modal-equipment-inline-edit :deep(svg) {
    width: 15px;
    height: 15px;
  }

  .equipment-modal .status-badge {
    padding: 7px 10px;
    font-size: 11px;
  }

  .equipment-modal .action-btn {
    font-size: 13px;
  }

  .equipment-modal .hw-file-card {
    width: 80px;
    height: 80px;
  }

  .equipment-grid {
    --cell-size: calc(55px * var(--ui-scale));
    --icon-div-size: calc(30px * var(--ui-scale));
    --icon-size: calc(18px * var(--ui-scale));
    --grid-gap: calc(4px * var(--ui-scale));
  }

  .specs-entry-group {
    grid-template-columns: auto minmax(0, 1fr);
    gap: 6px;
  }

  .specs-entry-chip {
    padding: 5px 8px;
  }

  .specs-entry-chip-caption {
    display: none;
  }

  .specs-entry-chip-text {
    font-size: 11px;
  }

  .specs-entry-btn {
    padding: 10px 12px;
    font-size: 12px;
  }

  .spec-form-group-switch {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .spec-form-row-compact {
    max-width: 124px;
  }

  .bool-segment-btn {
    min-height: 44px;
    padding: 11px 12px;
    font-size: 13px;
  }

  .spec-form-row-switch {
    width: 100%;
  }

  .spec-card-copy-pair {
    gap: 8px;
  }

  .spec-card-pair-col {
    gap: 4px;
  }

  .spec-card-label {
    font-size: 11px;
    letter-spacing: 0.03em;
  }

  .spec-card-value {
    font-size: 14px;
  }

  .spec-card-pair-divider {
    width: 1px;
    height: 100%;
  }
}
</style>
