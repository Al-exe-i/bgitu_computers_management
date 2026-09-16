<script>
import api from "@/services/api.js";
import router from "@/router/index.js";
import { officeBackLocation, preserveAudienceOrigin } from '@/utils/officeNavigation.js';
import {useNotificationsStore} from "@/stores/notifications.js";
import LoaderContainer from "@/components/Common/LoaderContainer.vue";
import TrustedSvgIcon from "@/components/Common/TrustedSvgIcon.vue";
import {useAuthStore} from "@/stores/auth.js";
import {getApiUrl, getRealtimeClientId, getSseUrl, withSseParams} from "@/config/api.js";
import {
  OPERATING_SYSTEM_OPTIONS,
  OS_EDITION_OPTIONS,
  SOFTWARE_OPTIONS,
  SOFTWARE_PRESETS,
} from "@/config/hardwareSpecifications.js";
import {useAudienceContext} from "@/stores/officeCtx.js";
import {markRaw} from "vue";

const MAX_HW_FILE_SIZE = 100 * 1024 * 1024;
const ALLOWED_HW_FILE_TYPES = ['image/', 'video/'];
const MAX_INSTALLED_SOFTWARE_ITEMS = 100;
const MAX_SOFTWARE_NAME_LENGTH = 128;

export default {
  name: 'AudienceView',
  components: { LoaderContainer, TrustedSvgIcon},
  props: ['audiencePublicId'],
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

      operatingSystemOptions: markRaw(OPERATING_SYSTEM_OPTIONS),
      osEditionOptions: markRaw(OS_EDITION_OPTIONS),
      softwareOptions: markRaw(SOFTWARE_OPTIONS),
      softwarePresets: markRaw(SOFTWARE_PRESETS),

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
          {
            key: 'operating_system',
            label: 'Операционная система',
            type: 'os-choice',
            options: OPERATING_SYSTEM_OPTIONS
          },
          {
            key: 'os_edition',
            label: 'Редакция / дистрибутив',
            type: 'dependent-select',
            emptyLabel: 'Сначала выберите ОС'
          },
          {
            key: 'installed_software',
            label: 'Установленные программы',
            type: 'software-checklist',
            maxItems: MAX_INSTALLED_SOFTWARE_ITEMS,
            itemMaxLength: MAX_SOFTWARE_NAME_LENGTH,
            placeholder: 'Другая программа'
          },
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
      specListInputs: {},
      collapsedSpecSections: {},
      specsSaving: false,
      showSpecsModal: false,

      /* Шаблоны характеристик */
      specTemplates: [],
      templatesLoading: false,
      specTemplatesExpanded: false,
      selectedTemplateId: '',
      newTemplateName: '',
      templateSaving: false,
      templateApplyingAll: false,
      customSoftwareExpanded: false,
      pendingWorkingStatus: null,
      statusConfirmLoading: false,
      statusConfirmDurationMs: 5000,

      /* Компактный список неисправностей текущего оборудования */
      problemDraft: [],
      maxProblems: 8,
      showUnsavedProblemsConfirm: false,
      unsavedProblemsSaving: false,
      statusConfirmRemainingMs: 0,
      statusConfirmStartedAt: 0,
      statusConfirmTimerId: null,
      statusConfirmEndTimerId: null,
      statusConfirmRunId: 0,

      /* Раздел файлов оборудования в модалке */
      isDragOver: false,
      showConfirmModal: false,
      fileToDeleteId: null,
      dontAskAgain: false,

      /* Realtime events */
      refreshTimer: null,
      refreshDebounceMs: 400,
      refreshQueuedDuringStatus: false,
      wsSuspendedUntil: 0,

      eventSource: null,
      wsConnected: false,
      wsError: false,
      wsReconnectAttempts: 0,
      maxReconnectAttempts: 3,
      reconnectDelay: 3000,
      reconnectTimer: null,
      isUnmounted: false,

      /* Preview */
      previewIndex: null,
      previewTriggerElement: null,
      previewZoom: 1,
      previewZoomMin: 0.5,
      previewZoomMax: 4,
      previewZoomStep: 0.25,
      previewPanX: 0,
      previewPanY: 0,
      previewIsPanning: false,
      previewPointerId: null,
      previewPointerStartX: 0,
      previewPointerStartY: 0,
      previewPanStartX: 0,
      previewPanStartY: 0,
      equipmentModalLeaving: false,
      viewportScrollLocked: false,
      viewportScrollLockMode: null,
      viewportScrollLockFrame: null,
      viewportScrollY: 0,
      viewportScrollSnapshot: null,
      viewportResizeHandler: null,
      viewportTouchStartY: 0,
      gridLabelMaxLength: 15,
      gridLabelResizeHandler: null
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

    previewZoomLabel() {
      return `${Math.round(this.previewZoom * 100)}%`;
    },

    previewImageStyle() {
      return {
        transform: `translate3d(${this.previewPanX}px, ${this.previewPanY}px, 0) scale(${this.previewZoom})`,
      };
    },

    // Админ или специалист ОИ + авторизован
    havePermission()
    {
      const user = this.authStore.user;
      return this.authStore.isAuthenticated && user && user.role < 2;
    },

    canUploadHardwareFiles()
    {
      return this.authStore.isAuthenticated;
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

    currentSpecSections() {
      const type = this.selectedCell?.data?.type;
      const computeGroups = [
        { key: 'processor', fields: ['cpu_model'], full: true },
        { key: 'processor-details', fields: ['cpu_frequency_ghz', 'cpu_cores'] },
        { key: 'memory', fields: ['ram_amount', 'ram_unit'] },
        { key: 'storage', fields: ['storage_amount', 'storage_unit'] },
        { key: 'purchase', fields: ['purchase_year'] },
      ];

      if (type === 'computer') {
        return [
          {
            key: 'hardware',
            title: 'Аппаратная часть',
            description: 'Процессор, память и накопитель',
            groups: computeGroups,
          },
          {
            key: 'system',
            title: 'Система и ПО',
            description: 'Операционная система и установленные программы',
            groups: [
              {
                key: 'operating-system',
                fields: ['operating_system', 'os_edition'],
                full: true,
                variant: 'os',
              },
              {
                key: 'software',
                fields: ['installed_software'],
                full: true,
                variant: 'software',
              },
            ],
          },
        ];
      }

      if (type === 'server') {
        return [{
          key: 'hardware',
          title: 'Аппаратная часть',
          description: 'Процессор, память и накопитель',
          groups: computeGroups,
        }];
      }

      if (type === 'switch') {
        return [{
          key: 'network',
          title: 'Сетевые параметры',
          description: 'Порты и режим управления',
          groups: [{
            key: 'switch-parameters',
            fields: ['ports_count', 'managed'],
            full: true,
            variant: 'switch',
          }],
        }];
      }

      return [];
    },

    currentSpecGroups() {
      return this.currentSpecSections.flatMap(section =>
          section.groups.map(group => group.fields)
      );
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

          if (field.type === 'software-checklist') {
            const values = this.normalizeSpecList(specs[fieldKey]);
            if (!values.length) continue;

            items.push({
              key: fieldKey,
              type: 'list',
              iconKey: fieldKey,
              label: field.label,
              values
            });
            continue;
          }

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

      if (type === 'computer') {
        return 'Процессор, память, накопитель, операционная система и установленное ПО';
      }

      if (type === 'server') {
        return 'Процессор, оперативная память, накопитель и год закупки';
      }

      if (type === 'switch') {
        return 'Порты, тип управления и базовые сетевые параметры устройства';
      }

      return 'Технические характеристики оборудования.';
    },

    statusConfirmTargetLabel() {
      if (this.pendingWorkingStatus === true) return 'Исправно';
      if (this.pendingWorkingStatus === false) return 'Неисправно';
      return '';
    },

    statusConfirmActionClass() {
      return this.pendingWorkingStatus === true ? 'is-working' : 'is-broken';
    },

    statusConfirmIsPending() {
      return this.pendingWorkingStatus !== null;
    },

    statusConfirmRemainingSeconds() {
      return Math.max(0, Math.ceil(this.statusConfirmRemainingMs / 1000));
    },

    statusConfirmProgressStyle() {
      // Полосу отсчёта рисует одна CSS-анимация на всю длительность —
      // сюда передаём только её время, без ежекадрового пересчёта ширины
      return {
        '--sc-duration': `${this.statusConfirmDurationMs}ms`
      };
    },

    statusConfirmIsUrgent() {
      return this.statusConfirmIsPending && this.statusConfirmRemainingMs <= 2000;
    },

    problemDraftItems() {
      return this.problemDraft
        .map(item => item.trim())
        .filter(Boolean);
    },

    problemDraftText() {
      return this.problemDraftItems.join('\n');
    },

    unsavedProblemCount() {
      return this.problemDraftItems.length;
    },

    hasUnsavedWorkingProblems() {
      if (!this.selectedCell?.data?.working) return false;
      if (!this.problemDraftText) return false;

      return this.problemDraftText !== String(this.selectedCell.data.comment ?? '').trim();
    },

  },

  watch: {
    async audiencePublicId() {
      this.loading = true;
      this.classroom = null;
      this.closeRealtime();
      document.title = 'Аудитория';
      await this.getAudience({ keepModal: false });
      this.connectRealtime();
    },

    isWorkspace() {
      this.scheduleViewportScrollLock();
    },

    selectedCell() {
      this.scheduleViewportScrollLock();
    },

    previewIndex(nextIndex, previousIndex) {
      this.scheduleViewportScrollLock();
      if (nextIndex !== previousIndex) this.resetPreviewTransform();
    },

    showConfirmModal() {
      this.scheduleViewportScrollLock();
    },

    showUnsavedProblemsConfirm() {
      this.scheduleViewportScrollLock();
    },

    showSpecsModal() {
      this.scheduleViewportScrollLock();
    },

    dropClassroomModalShow() {
      this.scheduleViewportScrollLock();
    },
  },

  methods: {
    getApiUrl,

    shouldLockViewportScroll() {
      return (
          this.isWorkspace ||
          this.selectedCell !== null ||
          this.equipmentModalLeaving ||
          this.previewIndex !== null ||
          this.showConfirmModal ||
          this.showUnsavedProblemsConfirm ||
          this.showSpecsModal ||
          this.dropClassroomModalShow
      );
    },

    getViewportScrollLockMode() {
      const hasBlockingModal =
          this.selectedCell !== null ||
          this.equipmentModalLeaving ||
          this.previewIndex !== null ||
          this.showConfirmModal ||
          this.showUnsavedProblemsConfirm ||
          this.showSpecsModal ||
          this.dropClassroomModalShow;

      return this.isWorkspace && !hasBlockingModal ? 'layout' : 'events';
    },

    scheduleViewportScrollLock() {
      if (this.viewportScrollLockFrame !== null) {
        window.cancelAnimationFrame(this.viewportScrollLockFrame);
        this.viewportScrollLockFrame = null;
      }

      this.$nextTick(() => {
        if (this.viewportScrollLockFrame !== null) {
          window.cancelAnimationFrame(this.viewportScrollLockFrame);
        }

        this.viewportScrollLockFrame = window.requestAnimationFrame(() => {
          this.viewportScrollLockFrame = null;
          this.syncViewportScrollLock();
        });
      });
    },

    onEquipmentModalEnter() {
      this.equipmentModalLeaving = false;
      this.scheduleViewportScrollLock();
    },

    onEquipmentModalBeforeLeave() {
      this.equipmentModalLeaving = true;
      this.scheduleViewportScrollLock();
    },

    onEquipmentModalAfterLeave() {
      this.equipmentModalLeaving = false;
      this.scheduleViewportScrollLock();
    },

    syncViewportScrollLock() {
      if (this.shouldLockViewportScroll()) {
        const lockMode = this.getViewportScrollLockMode();

        if (this.viewportScrollLocked && this.viewportScrollLockMode !== lockMode) {
          this.unlockViewportScroll();
        }

        this.lockViewportScroll(lockMode);
      } else {
        this.unlockViewportScroll();
      }
    },

    updateModalViewportMetrics() {
      const height = window.visualViewport?.height || window.innerHeight;
      const top = window.visualViewport?.offsetTop || 0;
      document.documentElement.style.setProperty('--audience-modal-vh', `${height}px`);
      document.documentElement.style.setProperty('--audience-modal-top', `${top}px`);
    },

    prepareEventsOnlyModalLock() {
      const html = document.documentElement;
      const body = document.body;

      this.viewportScrollY = window.scrollY || html.scrollTop || body.scrollTop || 0;
      this.updateModalViewportMetrics();
      html.style.setProperty('--audience-scroll-lock-offset', `${this.viewportScrollY}px`);
      body.classList.add('audience-modal-events-locked');
    },

    attachViewportScrollLockListeners() {
      if (this.viewportResizeHandler) return;

      this.viewportResizeHandler = () => {
        if (this.viewportScrollLocked) {
          this.updateModalViewportMetrics();
          this.$nextTick(() => this.clampPreviewPan());
        }
      };

      window.addEventListener('resize', this.viewportResizeHandler, { passive: true });
      window.addEventListener('orientationchange', this.viewportResizeHandler, { passive: true });
      window.visualViewport?.addEventListener('resize', this.viewportResizeHandler, { passive: true });
      window.visualViewport?.addEventListener('scroll', this.viewportResizeHandler, { passive: true });
      window.addEventListener('scroll', this.handleLockedWindowScroll, { passive: true });
      window.addEventListener('wheel', this.handleLockedWheel, { passive: false, capture: true });
      window.addEventListener('touchstart', this.handleLockedTouchStart, { passive: true, capture: true });
      window.addEventListener('touchmove', this.handleLockedTouchMove, { passive: false, capture: true });
      window.addEventListener('keydown', this.handleModalKeydown);
    },

    detachViewportScrollLockListeners() {
      if (!this.viewportResizeHandler) {
        window.removeEventListener('keydown', this.handleModalKeydown);
        window.removeEventListener('scroll', this.handleLockedWindowScroll);
        window.removeEventListener('wheel', this.handleLockedWheel, true);
        window.removeEventListener('touchstart', this.handleLockedTouchStart, true);
        window.removeEventListener('touchmove', this.handleLockedTouchMove, true);
        return;
      }

      window.removeEventListener('resize', this.viewportResizeHandler);
      window.removeEventListener('orientationchange', this.viewportResizeHandler);
      window.visualViewport?.removeEventListener('resize', this.viewportResizeHandler);
      window.visualViewport?.removeEventListener('scroll', this.viewportResizeHandler);
      window.removeEventListener('scroll', this.handleLockedWindowScroll);
      window.removeEventListener('wheel', this.handleLockedWheel, true);
      window.removeEventListener('touchstart', this.handleLockedTouchStart, true);
      window.removeEventListener('touchmove', this.handleLockedTouchMove, true);
      window.removeEventListener('keydown', this.handleModalKeydown);
      this.viewportResizeHandler = null;
    },

    getScrollLockContainer(target) {
      const scrollableSelectors = [
        '.equipment-modal-content',
        '.specs-modal-content',
        '.hw-confirm-box',
        '.hw-lb-content',
        '.modal-content',
        '.modal',
        '.grid-section.workspace'
      ].join(',');
      let element = target instanceof Element ? target : target?.parentElement;
      let fallback = null;

      while (element && element !== document.body) {
        if (element.matches(scrollableSelectors)) {
          fallback ??= element;

          if (element.scrollHeight > element.clientHeight || element.scrollWidth > element.clientWidth) {
            return element;
          }
        }

        element = element.parentElement;
      }

      return fallback;
    },

    shouldPreventLockedScroll(container, deltaY) {
      if (!container) return true;
      if (Math.abs(deltaY) < 1) return false;

      const hasVerticalScroll = container.scrollHeight > container.clientHeight + 1;
      if (!hasVerticalScroll) return true;

      const scrollTop = container.scrollTop;
      const maxScrollTop = container.scrollHeight - container.clientHeight;
      const isScrollingUp = deltaY < 0;
      const isScrollingDown = deltaY > 0;

      return (
          (isScrollingUp && scrollTop <= 0) ||
          (isScrollingDown && scrollTop >= maxScrollTop - 1)
      );
    },

    handleLockedWindowScroll() {
      if (!this.viewportScrollLocked) return;
      if (this.viewportScrollLockMode !== 'layout') return;

      if (Math.abs(window.scrollY - this.viewportScrollY) > 1) {
        window.scrollTo(0, this.viewportScrollY);
      }
    },

    handleLockedWheel(event) {
      if (!this.viewportScrollLocked) return;

      const container = this.getScrollLockContainer(event.target);
      if (event.cancelable && this.shouldPreventLockedScroll(container, event.deltaY)) {
        event.preventDefault();
      }
    },

    handleLockedTouchStart(event) {
      this.viewportTouchStartY = event.touches?.[0]?.clientY ?? 0;
    },

    handleLockedTouchMove(event) {
      if (!this.viewportScrollLocked || !event.touches?.length) return;

      const currentY = event.touches[0].clientY;
      const deltaY = this.viewportTouchStartY - currentY;
      this.viewportTouchStartY = currentY;

      const container = this.getScrollLockContainer(event.target);
      if (event.cancelable && this.shouldPreventLockedScroll(container, deltaY)) {
        event.preventDefault();
      }
    },

    lockViewportScroll(lockMode = this.getViewportScrollLockMode()) {
      if (this.viewportScrollLocked) return;

      const html = document.documentElement;
      const body = document.body;
      const app = document.getElementById('app');
      const scrollbarWidth = Math.max(0, window.innerWidth - html.clientWidth);

      this.viewportScrollY = window.scrollY || html.scrollTop || body.scrollTop || 0;
      this.viewportScrollSnapshot = {
        lockMode,
        htmlOverflow: html.style.overflow,
        htmlOverscrollBehavior: html.style.overscrollBehavior,
        modalViewportHeight: html.style.getPropertyValue('--audience-modal-vh'),
        modalViewportTop: html.style.getPropertyValue('--audience-modal-top'),
        modalScrollOffset: html.style.getPropertyValue('--audience-scroll-lock-offset'),
        bodyPosition: body.style.position,
        bodyTop: body.style.top,
        bodyLeft: body.style.left,
        bodyRight: body.style.right,
        bodyWidth: body.style.width,
        bodyBoxSizing: body.style.boxSizing,
        bodyOverflow: body.style.overflow,
        bodyOverscrollBehavior: body.style.overscrollBehavior,
        bodyPaddingRight: body.style.paddingRight,
        appPosition: app?.style.position ?? '',
        appTop: app?.style.top ?? '',
        appLeft: app?.style.left ?? '',
        appRight: app?.style.right ?? '',
        appWidth: app?.style.width ?? '',
        appBoxSizing: app?.style.boxSizing ?? '',
        appOverflow: app?.style.overflow ?? '',
        appPaddingRight: app?.style.paddingRight ?? '',
      };
      this.viewportScrollLocked = true;
      this.viewportScrollLockMode = lockMode;

      this.updateModalViewportMetrics();
      this.attachViewportScrollLockListeners();
      html.style.setProperty('--audience-scroll-lock-offset', `${this.viewportScrollY}px`);

      if (lockMode !== 'layout') {
        body.classList.add('audience-modal-events-locked');
        return;
      }

      html.classList.add('audience-viewport-locked');
      body.classList.add('audience-viewport-locked');
      html.style.overflow = 'hidden';
      html.style.overscrollBehavior = 'none';
      body.style.overflow = 'hidden';
      body.style.overscrollBehavior = 'none';

      if (app) {
        app.classList.add('audience-app-viewport-locked');
        app.style.position = 'fixed';
        app.style.top = `-${this.viewportScrollY}px`;
        app.style.left = '0';
        app.style.right = '0';
        app.style.width = '100%';
        app.style.boxSizing = 'border-box';
        app.style.overflow = 'hidden';
      }

      if (scrollbarWidth > 0) {
        if (app) {
          app.style.paddingRight = `${scrollbarWidth}px`;
        } else {
          body.style.paddingRight = `${scrollbarWidth}px`;
        }
      }
    },

    unlockViewportScroll() {
      const html = document.documentElement;
      const body = document.body;
      const app = document.getElementById('app');
      const snapshot = this.viewportScrollSnapshot;
      const lockMode = this.viewportScrollLockMode || snapshot?.lockMode;

      if (!this.viewportScrollLocked) {
        html.classList.remove('audience-viewport-locked');
        body.classList.remove('audience-viewport-locked');
        body.classList.remove('audience-modal-events-locked');
        app?.classList.remove('audience-app-viewport-locked');
        this.detachViewportScrollLockListeners();
        return;
      }

      const scrollY = this.viewportScrollY;

      if (snapshot?.modalViewportHeight) {
        html.style.setProperty('--audience-modal-vh', snapshot.modalViewportHeight);
      } else {
        html.style.removeProperty('--audience-modal-vh');
      }

      if (snapshot?.modalViewportTop) {
        html.style.setProperty('--audience-modal-top', snapshot.modalViewportTop);
      } else {
        html.style.removeProperty('--audience-modal-top');
      }

      html.style.removeProperty('--audience-scroll-lock-offset');

      html.classList.remove('audience-viewport-locked');
      body.classList.remove('audience-viewport-locked');
      body.classList.remove('audience-modal-events-locked');
      app?.classList.remove('audience-app-viewport-locked');

      if (lockMode === 'layout') {
        html.style.overflow = snapshot?.htmlOverflow ?? '';
        html.style.overscrollBehavior = snapshot?.htmlOverscrollBehavior ?? '';
        body.style.position = snapshot?.bodyPosition ?? '';
        body.style.top = snapshot?.bodyTop ?? '';
        body.style.left = snapshot?.bodyLeft ?? '';
        body.style.right = snapshot?.bodyRight ?? '';
        body.style.width = snapshot?.bodyWidth ?? '';
        body.style.boxSizing = snapshot?.bodyBoxSizing ?? '';
        body.style.overflow = snapshot?.bodyOverflow ?? '';
        body.style.overscrollBehavior = snapshot?.bodyOverscrollBehavior ?? '';
        body.style.paddingRight = snapshot?.bodyPaddingRight ?? '';

        if (app) {
          app.style.position = snapshot?.appPosition ?? '';
          app.style.top = snapshot?.appTop ?? '';
          app.style.left = snapshot?.appLeft ?? '';
          app.style.right = snapshot?.appRight ?? '';
          app.style.width = snapshot?.appWidth ?? '';
          app.style.boxSizing = snapshot?.appBoxSizing ?? '';
          app.style.overflow = snapshot?.appOverflow ?? '';
          app.style.paddingRight = snapshot?.appPaddingRight ?? '';
        }
      }

      this.viewportScrollLocked = false;
      this.viewportScrollLockMode = null;
      this.viewportScrollY = 0;
      this.viewportScrollSnapshot = null;
      this.detachViewportScrollLockListeners();
      window.scrollTo(0, scrollY);
    },

    clearViewportScrollLock() {
      if (this.viewportScrollLockFrame !== null) {
        window.cancelAnimationFrame(this.viewportScrollLockFrame);
        this.viewportScrollLockFrame = null;
      }

      this.unlockViewportScroll();
    },

    handleModalKeydown(event) {
      if (event.defaultPrevented || event.isComposing) return;

      if (this.previewIndex !== null) {
        if (event.key === 'Tab') {
          this.trapPreviewFocus(event);
        } else if (event.key === 'Escape') {
          event.preventDefault();
          this.closePreview();
        } else if (event.key === 'ArrowRight') {
          event.preventDefault();
          this.nextPreview();
        } else if (event.key === 'ArrowLeft') {
          event.preventDefault();
          this.prevPreview();
        } else if (this.isPreviewImage && ['Equal', 'NumpadAdd'].includes(event.code)) {
          event.preventDefault();
          this.zoomPreviewIn();
        } else if (this.isPreviewImage && ['Minus', 'NumpadSubtract'].includes(event.code)) {
          event.preventDefault();
          this.zoomPreviewOut();
        } else if (this.isPreviewImage && ['Digit0', 'Numpad0'].includes(event.code)) {
          event.preventDefault();
          this.resetPreviewTransform();
        }
        return;
      }

      if (event.key !== 'Escape') return;

      if (this.showUnsavedProblemsConfirm) {
        event.preventDefault();
        this.cancelUnsavedProblemsClose();
        return;
      }

      if (this.showConfirmModal) {
        event.preventDefault();
        this.closeConfirmModal();
        return;
      }

      if (this.showSpecsModal) {
        event.preventDefault();
        this.closeSpecsModal();
        return;
      }

      if (this.statusConfirmIsPending) {
        event.preventDefault();
        this.closeStatusConfirmModal();
        return;
      }

      if (this.dropClassroomModalShow) {
        event.preventDefault();
        this.dropClassroomModalShow = false;
        this.scheduleViewportScrollLock();
        return;
      }

      if (this.selectedCell) {
        event.preventDefault();
        this.closeModal();
        return;
      }

      if (this.isWorkspace) {
        event.preventDefault();
        this.toggleWorkspace();
      }
    },

    async getAudience({ keepModal = true } = {}) {
      const modalState = keepModal && this.selectedCell
          ? {
            row: this.selectedCell.row,
            col: this.selectedCell.col,
            showSpecsModal: this.showSpecsModal
          }
          : null;

      try {
        const res = await api.get(`/audiences/${this.audiencePublicId}`);

        // Realtime refresh must not recreate the equipment modal while the
        // confirmation countdown is active: that would reset its timers.
        if (keepModal && (this.statusConfirmIsPending || this.statusConfirmLoading)) {
          this.refreshQueuedDuringStatus = true;
          return;
        }

        this.classroom = this.mapBackendToFrontend(res.data);
        this.loading = false;
        this.updatePageTitle();

        this.audienceContext.setOffice(this.classroom.office_id);

        // если модалка открыта — можно просто переоткрыть на те же координаты
        if (modalState) {
          const { row, col, showSpecsModal } = modalState;
          this.closeModal({ force: true });
          this.openModal(row, col);

          if (showSpecsModal && this.hasSpecsEditor) {
            this.showSpecsModal = true;
            this.specsDraft = this.createSpecsDraft(this.selectedCell?.data?.specs);
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

      if (this.statusConfirmIsPending || this.statusConfirmLoading) {
        this.refreshQueuedDuringStatus = true;
        return;
      }

      if (this.refreshTimer) clearTimeout(this.refreshTimer);
      this.refreshTimer = setTimeout(() => {
        this.refreshTimer = null;

        if (this.statusConfirmIsPending || this.statusConfirmLoading) {
          this.refreshQueuedDuringStatus = true;
          return;
        }

        this.getAudience({ keepModal: true });
      }, this.refreshDebounceMs);
    },

    flushQueuedRefreshAfterStatus() {
      if (!this.refreshQueuedDuringStatus || this.statusConfirmIsPending || this.statusConfirmLoading) {
        return;
      }

      this.refreshQueuedDuringStatus = false;

      if (this.refreshTimer) {
        clearTimeout(this.refreshTimer);
      }

      const suspensionLeft = Math.max(0, this.wsSuspendedUntil - Date.now());
      const delay = Math.max(this.refreshDebounceMs, suspensionLeft);

      this.refreshTimer = setTimeout(() => {
        this.refreshTimer = null;
        this.getAudience({ keepModal: true });
      }, delay);
    },

    mapBackendToFrontend(data) {
      return {
        id: data.id,
        publicId: data.public_id,
        number: data.number ?? data.id,
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

    updatePageTitle() {
      if (!this.classroom) {
        document.title = 'Аудитория';
        return;
      }

      const number = this.classroom.number ?? this.classroom.id;
      document.title = `Аудитория №${number}`;
    },

    getEquipment(row, col) {
      return this.occupiedMap[`${row}-${col}`]?.item ?? null;
    },

    getEquipmentType(id) {
      return this.equipmentTypes[id];
    },

    getEquipmentDisplayName(item) {
      const fallback = this.getEquipmentType(item?.type)?.name || 'Оборудование';
      return String(item?.title || fallback).trim() || fallback;
    },

    formatEquipmentGridLabel(item) {
      const label = this.getEquipmentDisplayName(item);
      const chars = Array.from(label);
      const maxLength = this.gridLabelMaxLength || 15;

      if (chars.length <= maxLength) {
        return label;
      }

      return `${chars.slice(0, Math.max(1, maxLength - 1)).join('').trimEnd()}…`;
    },

    updateGridLabelLimit() {
      const width = window.innerWidth || document.documentElement.clientWidth || 0;

      if (width <= 480) {
        this.gridLabelMaxLength = 10;
        return;
      }

      if (width <= 768) {
        this.gridLabelMaxLength = 12;
        return;
      }

      this.gridLabelMaxLength = 15;
    },

    normalizeSpecList(rawValue) {
      if (!Array.isArray(rawValue)) return [];

      const result = [];
      const seen = new Set();

      for (const item of rawValue) {
        if (typeof item !== 'string') continue;

        const normalized = item.trim();
        if (!normalized) continue;

        const deduplicationKey = normalized.toLocaleLowerCase('ru-RU');
        if (seen.has(deduplicationKey)) continue;

        seen.add(deduplicationKey);
        result.push(normalized);
      }

      return result;
    },

    parseSpecListInput(rawValue) {
      return String(rawValue || '')
          .split(/[;\r\n]+/)
          .map(item => item.trim())
          .filter(Boolean);
    },

    getSpecListValues(fieldKey) {
      return this.normalizeSpecList(this.specsDraft[fieldKey]);
    },

    createSpecsDraft(rawSpecs, hardwareType = this.selectedCell?.data?.type) {
      const source = rawSpecs && typeof rawSpecs === 'object' ? rawSpecs : {};
      const draft = JSON.parse(JSON.stringify(source));

      if (hardwareType !== 'computer' || typeof draft.operating_system !== 'string') {
        return draft;
      }

      const rawOperatingSystem = draft.operating_system.trim();
      const normalizedOperatingSystem = rawOperatingSystem.toLocaleLowerCase('ru-RU');
      const family = this.operatingSystemOptions.find(
          option => option.value === normalizedOperatingSystem
      );

      if (family) {
        draft.operating_system = family.value;
        return draft;
      }

      for (const option of this.operatingSystemOptions) {
        const edition = (this.osEditionOptions[option.value] ?? []).find(
            item => item.toLocaleLowerCase('ru-RU') === normalizedOperatingSystem
        );

        if (!edition) continue;

        draft.operating_system = option.value;
        if (!draft.os_edition) draft.os_edition = edition;
        break;
      }

      return draft;
    },

    getOsEditionOptions(operatingSystem = this.specsDraft.operating_system) {
      return this.osEditionOptions[operatingSystem] ?? [];
    },

    selectOperatingSystem(operatingSystem) {
      if (this.specsDraft.operating_system === operatingSystem) {
        delete this.specsDraft.operating_system;
        delete this.specsDraft.os_edition;
        return;
      }

      this.specsDraft.operating_system = operatingSystem;

      if (!this.getOsEditionOptions(operatingSystem).includes(this.specsDraft.os_edition)) {
        delete this.specsDraft.os_edition;
      }
    },

    isSpecSectionCollapsed(sectionKey) {
      return this.collapsedSpecSections[sectionKey] === true;
    },

    toggleSpecSection(sectionKey) {
      this.collapsedSpecSections[sectionKey] = !this.isSpecSectionCollapsed(sectionKey);
    },

    isSoftwareSelected(fieldKey, software) {
      return this.getSpecListValues(fieldKey).includes(software);
    },

    toggleSoftwareItem(fieldKey, software) {
      const current = this.getSpecListValues(fieldKey);

      if (current.includes(software)) {
        this.specsDraft[fieldKey] = current.filter(item => item !== software);
        if (!this.specsDraft[fieldKey].length) delete this.specsDraft[fieldKey];
        return;
      }

      const field = this.currentSpecFieldMap[fieldKey];
      const maxItems = field?.maxItems ?? MAX_INSTALLED_SOFTWARE_ITEMS;
      if (current.length >= maxItems) {
        this.notify.warning(`Можно указать не более ${maxItems} программ`);
        return;
      }

      this.specsDraft[fieldKey] = [...current, software];
    },

    getCustomSoftwareValues(fieldKey) {
      const catalog = new Set(this.softwareOptions.map(option => option.value));
      return this.getSpecListValues(fieldKey).filter(item => !catalog.has(item));
    },

    removeSpecListValue(fieldKey, value) {
      const nextItems = this.getSpecListValues(fieldKey).filter(item => item !== value);

      if (nextItems.length) {
        this.specsDraft[fieldKey] = nextItems;
      } else {
        delete this.specsDraft[fieldKey];
      }
    },

    applySoftwarePreset(fieldKey, preset) {
      const catalog = new Set(this.softwareOptions.map(option => option.value));
      const customItems = this.getSpecListValues(fieldKey).filter(item => !catalog.has(item));
      this.specsDraft[fieldKey] = this.normalizeSpecList([...preset.items, ...customItems]);
    },

    isSoftwarePresetActive(fieldKey, preset) {
      const catalog = new Set(this.softwareOptions.map(option => option.value));
      const selectedCatalogItems = this.getSpecListValues(fieldKey)
          .filter(item => catalog.has(item));

      if (selectedCatalogItems.length !== preset.items.length) return false;
      return preset.items.every(item => selectedCatalogItems.includes(item));
    },

    clearSoftware(fieldKey) {
      delete this.specsDraft[fieldKey];
      this.specListInputs[fieldKey] = '';
      this.customSoftwareExpanded = false;
    },

    openCustomSoftwareInput() {
      this.customSoftwareExpanded = true;
      this.$nextTick(() => this.$refs.customSoftwareInput?.focus());
    },

    addSpecListItem(fieldKey) {
      const field = this.currentSpecFieldMap[fieldKey];
      if (!field) return;

      const candidates = this.parseSpecListInput(this.specListInputs[fieldKey]);
      if (!candidates.length) return;

      const maxLength = field.itemMaxLength ?? MAX_SOFTWARE_NAME_LENGTH;
      if (candidates.some(item => Array.from(item).length > maxLength)) {
        this.notify.warning(`Название программы должно быть не длиннее ${maxLength} символов`);
        return;
      }

      const current = this.getSpecListValues(fieldKey);
      const merged = this.normalizeSpecList([...current, ...candidates]);
      const maxItems = field.maxItems ?? MAX_INSTALLED_SOFTWARE_ITEMS;

      if (merged.length > maxItems) {
        this.notify.warning(`Можно указать не более ${maxItems} программ`);
        return;
      }

      this.specsDraft[fieldKey] = merged;
      this.specListInputs[fieldKey] = '';
      this.customSoftwareExpanded = false;
    },

    removeSpecListItem(fieldKey, index) {
      const nextItems = this.getSpecListValues(fieldKey)
          .filter((_, itemIndex) => itemIndex !== index);

      if (nextItems.length) {
        this.specsDraft[fieldKey] = nextItems;
        return;
      }

      delete this.specsDraft[fieldKey];
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

      if (field.type === 'software-checklist') {
        const values = this.normalizeSpecList(rawValue);
        return values.length ? values.join(', ') : null;
      }

      let value = rawValue;

      if (field.type === 'os-choice') {
        const option = this.operatingSystemOptions.find(item => item.value === rawValue);
        value = option?.label ?? rawValue;
      }

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
        operating_system: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="14" rx="2"></rect><path d="M8 21h8M12 18v3M7 9h3M7 13h6"></path></svg>',
        os_edition: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 3h10l4 4v10l-4 4H7l-4-4V7z"></path><path d="M8 12h8M12 8v8"></path></svg>',
        installed_software: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="2"></rect><rect x="14" y="3" width="7" height="7" rx="2"></rect><rect x="3" y="14" width="7" height="7" rx="2"></rect><path d="M17.5 14v7M14 17.5h7"></path></svg>',
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

        if (field.type === 'software-checklist') {
          const pendingItems = this.parseSpecListInput(this.specListInputs[field.key]);
          const normalizedItems = this.normalizeSpecList([
            ...(Array.isArray(value) ? value : []),
            ...pendingItems,
          ]);

          if (normalizedItems.length) normalized[field.key] = normalizedItems;
          continue;
        }

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

        if (field.type === 'os-choice' || field.type === 'dependent-select') {
          normalized[field.key] = String(value);
          continue;
        }

        if (field.type === 'boolean-labels') {
          if (typeof value === 'boolean') normalized[field.key] = value;
          continue;
        }

        if (field.type === 'text') {
          const textValue = String(value).trim();
          if (textValue) normalized[field.key] = textValue;
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
        this.specsDraft = this.createSpecsDraft(payload);
        this.specListInputs = {};
        this.customSoftwareExpanded = false;
        this.specsEdit = false;

        this.notify.success('Характеристики сохранены');
      } catch (err) {
        this.notify.error('Не удалось сохранить характеристики');
      } finally {
        this.specsSaving = false;
      }
    },

    cancelSpecsEdit() {
      this.specsDraft = this.createSpecsDraft(this.selectedCell?.data?.specs);
      this.specListInputs = {};
      this.customSoftwareExpanded = false;
      this.specsEdit = false;
    },

    openSpecsModal() {
      if (!this.hasSpecsEditor) return;

      this.prepareEventsOnlyModalLock();
      this.specsDraft = this.createSpecsDraft(this.selectedCell?.data?.specs);
      this.specListInputs = {};
      this.collapsedSpecSections = {};
      this.specsEdit = false;
      this.showSpecsModal = true;

      this.specTemplatesExpanded = false;
      this.customSoftwareExpanded = false;
      this.selectedTemplateId = '';
      this.newTemplateName = '';
      this.fetchSpecTemplates();
    },

    closeSpecsModal() {
      this.showSpecsModal = false;
      this.specTemplatesExpanded = false;
      this.cancelSpecsEdit();
    },

    async fetchSpecTemplates() {
      const type = this.selectedCell?.data?.type;
      // Шаблоны — админский инструмент (эндпоинт требует admin)
      if (!type || !this.havePermission) {
        this.specTemplates = [];
        return;
      }

      this.templatesLoading = true;
      try {
        const res = await api.get('/spec-templates', { params: { hardware_type: type } });
        this.specTemplates = Array.isArray(res.data) ? res.data : [];
      } catch (err) {
        this.specTemplates = [];
      } finally {
        this.templatesLoading = false;
      }
    },

    findSelectedTemplate() {
      return this.specTemplates.find(tpl => tpl.id === this.selectedTemplateId) ?? null;
    },

    // Подставить характеристики из шаблона в черновик текущего устройства
    applySpecTemplate() {
      const tpl = this.findSelectedTemplate();
      if (!tpl) return;

      this.specsDraft = this.createSpecsDraft(tpl.specs);
      this.specListInputs = {};
      this.customSoftwareExpanded = false;
      this.specsEdit = true;
      this.notify.success(`Шаблон «${tpl.name}» подставлен — проверьте и сохраните`);
    },

    // Сохранить текущий черновик характеристик как новый шаблон
    async saveSpecsAsTemplate() {
      const name = this.newTemplateName.trim();
      if (!name) {
        this.notify.warning('Введите название шаблона');
        return;
      }

      const type = this.selectedCell?.data?.type;
      if (!type) return;

      this.templateSaving = true;
      try {
        const payload = this.normalizeSpecsDraft();
        const res = await api.post('/spec-templates', {
          name,
          hardware_type: type,
          specs: payload,
        });

        this.specTemplates.push(res.data);
        this.selectedTemplateId = res.data.id;
        this.newTemplateName = '';
        this.specsDraft = this.createSpecsDraft(payload, type);
        this.specListInputs = {};
        this.notify.success('Шаблон сохранён');
      } catch (err) {
        this.notify.error('Не удалось сохранить шаблон');
      } finally {
        this.templateSaving = false;
      }
    },

    async deleteSpecTemplate() {
      const tpl = this.findSelectedTemplate();
      if (!tpl) return;

      try {
        await api.delete(`/spec-templates/${tpl.id}`);
        this.specTemplates = this.specTemplates.filter(item => item.id !== tpl.id);
        this.selectedTemplateId = '';
        this.notify.success('Шаблон удалён');
      } catch (err) {
        this.notify.error('Не удалось удалить шаблон');
      }
    },

    // Применить шаблон сразу ко всему оборудованию того же типа в аудитории
    async applyTemplateToAll() {
      const tpl = this.findSelectedTemplate();
      if (!tpl) {
        this.notify.warning('Сначала выберите шаблон');
        return;
      }

      const type = this.selectedCell?.data?.type;
      const targets = (this.classroom?.equipment ?? []).filter(eq => eq.type === type && eq.dbId);
      if (targets.length === 0) {
        this.notify.info('В аудитории нет оборудования этого типа');
        return;
      }

      this.templateApplyingAll = true;
      this.wsSuspendedUntil = Date.now() + 1500 + targets.length * 60;
      const templateSpecs = this.createSpecsDraft(tpl.specs, type);

      let applied = 0;
      try {
        for (const eq of targets) {
          try {
            await api.patch(`/hardware/${eq.dbId}`, { specs: templateSpecs });
            eq.specs = JSON.parse(JSON.stringify(templateSpecs));
            applied += 1;
          } catch (err) {
            // пропускаем сбойную единицу, продолжаем с остальными
          }
        }

        this.specsDraft = this.createSpecsDraft(templateSpecs, type);
        this.specListInputs = {};
        if (this.selectedCell?.data) {
          this.selectedCell.data.specs = JSON.parse(JSON.stringify(templateSpecs));
        }

        if (applied === targets.length) {
          this.notify.success(`Шаблон применён ко всем (${applied}) ед. оборудования`);
        } else {
          this.notify.warning(`Применено к ${applied} из ${targets.length} ед. оборудования`);
        }
      } finally {
        this.templateApplyingAll = false;
      }
    },

    openModal(row, col) {
      if (!this.authStore.isAuthenticated) return;

      const eq = this.getEquipment(row, col);
      if (!eq) return;

      this.statusConfirmRunId += 1;
      this.clearStatusConfirmTimers();
      this.prepareEventsOnlyModalLock();

      this.selectedCell = {
        row,
        col,
        key: `${row}-${col}`,
        data: eq
      };

      this.newInv_no = eq.invNumber;
      this.newHwTitle = eq.title;

      this.problemDraft = this.parseProblems(eq.comment);

      this.specsEdit = false;
      this.specsDraft = this.createSpecsDraft(eq.specs, eq.type);
      this.specListInputs = {};
      this.specTemplatesExpanded = false;
      this.customSoftwareExpanded = false;
      this.showSpecsModal = false;
      this.pendingWorkingStatus = null;
      this.statusConfirmLoading = false;
      this.scheduleViewportScrollLock();
    },

    closeModal(options = {}) {
      const force = options?.force === true;

      if (this.unsavedProblemsSaving) return;

      if (!force && this.hasUnsavedWorkingProblems) {
        this.closeStatusConfirmModal();
        this.showUnsavedProblemsConfirm = true;
        this.scheduleViewportScrollLock();
        return;
      }

      this.forceCloseEquipmentModal();
    },

    forceCloseEquipmentModal() {
      this.closeStatusConfirmModal();
      this.previewIndex = null;
      this.previewTriggerElement = null;
      this.selectedCell = null;
      this.showUnsavedProblemsConfirm = false;
      this.unsavedProblemsSaving = false;
      this.pendingWorkingStatus = null;
      this.statusConfirmLoading = false;

      this.invNumEdit = false;
      this.hwTitleEdit = false;
      this.newHwTitle = this.newInv_no = ``;

      this.specsEdit = false;
      this.specsDraft = {};
      this.showSpecsModal = false;
      this.showConfirmModal = false;
      this.fileToDeleteId = null;
      this.dontAskAgain = false;
      this.scheduleViewportScrollLock();
    },

    cancelUnsavedProblemsClose() {
      if (this.unsavedProblemsSaving) return;
      this.showUnsavedProblemsConfirm = false;
      this.scheduleViewportScrollLock();
    },

    discardUnsavedProblemsAndClose() {
      if (this.unsavedProblemsSaving) return;
      this.showUnsavedProblemsConfirm = false;
      this.forceCloseEquipmentModal();
    },

    async saveUnsavedProblemsAndClose() {
      if (!this.selectedCell || this.unsavedProblemsSaving) return;

      if (!this.hasUnsavedWorkingProblems) {
        this.discardUnsavedProblemsAndClose();
        return;
      }

      if (this.problemDraftText.length > 255) {
        this.notify.warning('Список неисправностей слишком длинный (макс. 255 символов)');
        return;
      }

      this.unsavedProblemsSaving = true;
      try {
        const saved = await this.applyWorkingStatus(false);
        if (!saved) return;

        this.showUnsavedProblemsConfirm = false;
        this.forceCloseEquipmentModal();
      } finally {
        this.unsavedProblemsSaving = false;
      }
    },

    openDropClassroomModal() {
      this.prepareEventsOnlyModalLock();
      this.dropClassroomModalShow = true;
    },

    async requestWorkingStatus(status) {
      if (!this.selectedCell || this.selectedCell.data.working === status || this.statusConfirmLoading) return;

      if (status === false) {
        this.syncProblemsToComment();
        if ((this.selectedCell.data.comment ?? '').length > 255) {
          this.notify.warning('Список неисправностей слишком длинный (макс. 255 символов)');
          return;
        }
      }

      if (this.refreshTimer) {
        clearTimeout(this.refreshTimer);
        this.refreshTimer = null;
        this.refreshQueuedDuringStatus = true;
      }

      this.pendingWorkingStatus = status;
      this.startStatusConfirmCountdown();
    },

    closeStatusConfirmModal() {
      if (this.statusConfirmLoading) return;

      this.statusConfirmRunId += 1;
      this.clearStatusConfirmTimers();
      this.pendingWorkingStatus = null;
      this.statusConfirmStartedAt = 0;
      this.statusConfirmRemainingMs = 0;
      this.flushQueuedRefreshAfterStatus();
    },

    async confirmWorkingStatus(expectedRunId = null) {
      const runId = Number.isInteger(expectedRunId)
          ? expectedRunId
          : this.statusConfirmRunId;

      if (
          runId !== this.statusConfirmRunId ||
          this.pendingWorkingStatus === null ||
          this.statusConfirmLoading
      ) return;

      const status = this.pendingWorkingStatus;
      this.clearStatusConfirmTimers();
      this.statusConfirmRemainingMs = 0;
      this.statusConfirmLoading = true;

      try {
        await this.applyWorkingStatus(status);
      } finally {
        if (runId !== this.statusConfirmRunId) return;

        this.statusConfirmRunId += 1;
        this.pendingWorkingStatus = null;
        this.statusConfirmStartedAt = 0;
        this.statusConfirmRemainingMs = 0;
        this.statusConfirmLoading = false;
        this.flushQueuedRefreshAfterStatus();
      }
    },

    startStatusConfirmCountdown() {
      this.clearStatusConfirmTimers();
      const runId = ++this.statusConfirmRunId;
      this.statusConfirmStartedAt = Date.now();
      this.statusConfirmRemainingMs = this.statusConfirmDurationMs;
      // Таймер нужен только для цифры секунд и флага «срочно» — полоса едет на CSS,
      // поэтому частоту можно снизить (стабильнее, меньше реактивных обновлений)
      this.statusConfirmTimerId = window.setInterval(
          () => this.updateStatusConfirmCountdown(runId),
          250
      );
      this.statusConfirmEndTimerId = window.setTimeout(
          () => this.confirmWorkingStatus(runId),
          this.statusConfirmDurationMs
      );
    },

    updateStatusConfirmCountdown(runId) {
      if (runId !== this.statusConfirmRunId) return;
      if (this.pendingWorkingStatus === null || !this.statusConfirmStartedAt) return;

      const elapsedMs = Date.now() - this.statusConfirmStartedAt;
      this.statusConfirmRemainingMs = Math.max(0, this.statusConfirmDurationMs - elapsedMs);
    },

    clearStatusConfirmTimers() {
      if (this.statusConfirmTimerId !== null) {
        window.clearInterval(this.statusConfirmTimerId);
        this.statusConfirmTimerId = null;
      }

      if (this.statusConfirmEndTimerId !== null) {
        window.clearTimeout(this.statusConfirmEndTimerId);
        this.statusConfirmEndTimerId = null;
      }
    },

    async applyWorkingStatus(status) {
      if (!this.selectedCell) return false;

      this.syncProblemsToComment();

      const cell = this.selectedCell;
      const hardwareId = cell.data.dbId;
      const description = status === true ? `` : cell.data.comment;
      this.wsSuspendedUntil = Date.now() + 1000;

      try {
        await api.patch(`/hardware/${hardwareId}`, {
          state: status,
          description
        });

        if (this.selectedCell?.data?.dbId !== hardwareId) return true;

        this.selectedCell.data.working = status;

        if (status) {
          this.selectedCell.data.comment = ``;
          this.problemDraft = [];
        }

        return true;
      } catch (err) {
        this.notify.error(`Не удалось изменить состояние текущего оборудования!`);
        return false;
      }
    },

    /* ── Компактный список неисправностей ── */

    parseProblems(text) {
      return String(text ?? '')
        .split('\n')
        .map(item => item.trim())
        .filter(Boolean);
    },

    // Собираем список обратно в строку description (по одной проблеме на строку)
    syncProblemsToComment() {
      if (!this.selectedCell) return;
      this.selectedCell.data.comment = this.problemDraftText;
    },

    async addProblem() {
      if (this.problemDraft.length >= this.maxProblems) return;
      this.problemDraft.push('');
      await this.$nextTick();

      const scrollNode = this.$refs.problemScroll;
      if (!scrollNode) return;

      if (typeof scrollNode.scrollTo === 'function') {
        scrollNode.scrollTo({
          top: scrollNode.scrollHeight,
          behavior: 'smooth',
        });
      } else {
        scrollNode.scrollTop = scrollNode.scrollHeight;
      }

      const inputs = scrollNode.querySelectorAll('.problem-input');
      const nextInput = inputs[inputs.length - 1];
      try {
        nextInput?.focus({ preventScroll: true });
      } catch {
        nextInput?.focus();
      }
    },

    async removeProblem(index) {
      this.problemDraft.splice(index, 1);
      await this.persistProblemsIfBroken();
    },

    async onProblemBlur() {
      await this.persistProblemsIfBroken();
    },

    onProblemEnter(index) {
      // Enter на последней непустой строке — добавляем следующую проблему
      if (index === this.problemDraft.length - 1 && this.problemDraft[index].trim()) {
        this.addProblem();
      }
    },

    // Для уже неисправного оборудования список сохраняется автоматически,
    // без отдельной кнопки. У исправного — копится локально до пометки «Неисправно».
    async persistProblemsIfBroken() {
      if (!this.selectedCell || this.selectedCell.data.working) return;

      this.syncProblemsToComment();
      const description = this.selectedCell.data.comment ?? '';
      if (description.length > 255) {
        this.notify.warning('Список неисправностей слишком длинный (макс. 255 символов)');
        return;
      }

      const hardwareId = this.selectedCell.data.dbId;
      this.wsSuspendedUntil = Date.now() + 1000;

      try {
        await api.patch(`/hardware/${hardwareId}`, { description });
      } catch (err) {
        this.notify.error('Не удалось сохранить список неисправностей');
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
      router.push(officeBackLocation(this.classroom, this.$route.query));
    },

    editClassroom() {
      router.push({
        name: 'ChangeAudience',
        params: { audiencePublicId: this.classroom.publicId },
        query: preserveAudienceOrigin(this.$route.query),
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
      await api.delete(`/audiences/${this.classroom.publicId}`).then((response) => {
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
    /* Realtime events */
    connectRealtime() {
      if (this.isUnmounted || !this.classroom?.id) {
        return;
      }

      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }

      if (this.eventSource) {
        this.eventSource.onopen = null;
        this.eventSource.onerror = null;
        this.eventSource.close();
      }

      this.eventSource = new EventSource(
          withSseParams(getSseUrl(), {
            audience_id: this.classroom.id,
            client_id: getRealtimeClientId(`audience:${this.classroom.id}`),
          })
      );

      this.eventSource.onopen = () => {
        this.wsConnected = true;
        this.wsError = false;
        this.wsReconnectAttempts = 0;
        this.reconnectDelay = 1000;
      };

      const handleRealtimeEvent = (event) => {
        const msg = JSON.parse(event.data);
        const audienceId = msg?.audience_updated ?? msg?.audience_id;
        if (Number(audienceId) === Number(this.classroom?.id)) {
          this.scheduleRefresh();
        }
      };

      this.eventSource.addEventListener('audience_updated', handleRealtimeEvent);
      this.eventSource.onmessage = handleRealtimeEvent;

      this.eventSource.onerror = () => {
        if (this.isUnmounted) return;

        this.wsConnected = false;
        this.eventSource?.close();

        if (this.wsReconnectAttempts < this.maxReconnectAttempts) {
          this.wsReconnectAttempts++;
          const delay = this.reconnectDelay * this.wsReconnectAttempts;

          this.notify.warning(`Соединение потеряно. Переподключение №${this.wsReconnectAttempts} через ${delay / 1000} с...`);

          this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connectRealtime();
          }, delay);
        } else {
          this.wsError = true;
          this.notify.error("Не удалось восстановить соединение с сервером");
          router.push(`/`);
        }
      };
    },

    closeRealtime()
    {
      clearTimeout(this.refreshTimer)
      this.refreshTimer = null;
      this.refreshQueuedDuringStatus = false;

      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }

      if(this.eventSource)
      {
        this.eventSource.onopen = null;
        this.eventSource.onmessage = null;
        this.eventSource.onerror = null;
        this.wsConnected = false;
        this.eventSource.close()
        this.eventSource = null;
      }
    },
    /* Файлы оборудования */
    validateHardwareFiles(files) {
      const validFiles = [];
      const rejectedByType = [];
      const rejectedBySize = [];

      for (const file of files) {
        const hasAllowedType = ALLOWED_HW_FILE_TYPES.some((prefix) => file.type?.startsWith(prefix));

        if (!hasAllowedType) {
          rejectedByType.push(file.name);
          continue;
        }

        if (file.size > MAX_HW_FILE_SIZE) {
          rejectedBySize.push(file.name);
          continue;
        }

        validFiles.push(file);
      }

      if (rejectedByType.length) {
        this.notify.warning('Можно загружать только изображения и видео.');
      }

      if (rejectedBySize.length) {
        this.notify.warning('Файл слишком большой. Максимальный размер — 100 МБ.');
      }

      return validFiles;
    },

    async uploadFiles(files) {
      if (!this.canUploadHardwareFiles)
      {
        this.notify.warning("У вас недостаточно прав для загрузки файлов");
        return;
      }

      const validFiles = this.validateHardwareFiles(files);
      if (!validFiles.length) return;

      const formData = new FormData();
      validFiles.forEach(file => formData.append('files', file));

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
      if(!this.canUploadHardwareFiles)
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
        this.prepareEventsOnlyModalLock();
        this.fileToDeleteId = fileId;
        this.dontAskAgain = false; // Сбрасываем чекбокс
        this.showConfirmModal = true;
        this.scheduleViewportScrollLock();
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
      this.scheduleViewportScrollLock();
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
    openPreview(index, event = null) {
      const files = this.selectedCell?.data?.files;
      if (!files?.[index]) return;

      if (this.previewIndex !== null) {
        this.previewIndex = index;
        return;
      }

      this.previewTriggerElement = event?.currentTarget ?? document.activeElement;
      this.prepareEventsOnlyModalLock();
      this.previewIndex = index;
      this.scheduleViewportScrollLock();
      this.$nextTick(() => this.$refs.lightboxDialog?.focus({ preventScroll: true }));
    },

    // Закрыть
    closePreview() {
      const trigger = this.previewTriggerElement;
      this.previewIndex = null;
      this.previewTriggerElement = null;
      this.scheduleViewportScrollLock();
      this.$nextTick(() => {
        if (trigger?.isConnected && typeof trigger.focus === 'function') {
          trigger.focus({ preventScroll: true });
        }
      });
    },

    trapPreviewFocus(event) {
      const dialog = this.$refs.lightboxDialog;
      if (!dialog) return;

      const focusable = Array.from(dialog.querySelectorAll(
          'button:not([disabled]), video[controls], [tabindex]:not([tabindex="-1"])'
      )).filter((element) => element.getClientRects().length > 0);

      if (!focusable.length) {
        event.preventDefault();
        dialog.focus({ preventScroll: true });
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement;

      if (event.shiftKey && (active === first || active === dialog || !dialog.contains(active))) {
        event.preventDefault();
        last.focus({ preventScroll: true });
      } else if (!event.shiftKey && (active === last || active === dialog || !dialog.contains(active))) {
        event.preventDefault();
        first.focus({ preventScroll: true });
      }
    },

    resetPreviewTransform() {
      this.previewZoom = 1;
      this.previewPanX = 0;
      this.previewPanY = 0;
      this.previewIsPanning = false;
      this.previewPointerId = null;
    },

    setPreviewZoom(value) {
      const nextZoom = Math.min(
          this.previewZoomMax,
          Math.max(this.previewZoomMin, Math.round(value * 100) / 100),
      );

      this.previewZoom = nextZoom;
      if (nextZoom <= 1) {
        this.previewPanX = 0;
        this.previewPanY = 0;
      }

      this.$nextTick(() => this.clampPreviewPan());
    },

    zoomPreviewIn() {
      this.setPreviewZoom(this.previewZoom + this.previewZoomStep);
    },

    zoomPreviewOut() {
      this.setPreviewZoom(this.previewZoom - this.previewZoomStep);
    },

    togglePreviewZoom() {
      if (this.previewZoom > 1) {
        this.resetPreviewTransform();
        return;
      }

      this.setPreviewZoom(2);
    },

    handlePreviewWheel(event) {
      if (!this.isPreviewImage || !event.deltaY) return;

      event.preventDefault();
      this.setPreviewZoom(this.previewZoom - event.deltaY * 0.002);
    },

    getPreviewPanLimits() {
      const image = this.$refs.previewImage;
      const frame = this.$refs.previewMediaFrame;

      if (!image || !frame || this.previewZoom <= 1) {
        return { x: 0, y: 0 };
      }

      return {
        x: Math.max(0, (image.offsetWidth * this.previewZoom - frame.clientWidth) / 2),
        y: Math.max(0, (image.offsetHeight * this.previewZoom - frame.clientHeight) / 2),
      };
    },

    setPreviewPan(x, y) {
      const limits = this.getPreviewPanLimits();
      this.previewPanX = Math.min(limits.x, Math.max(-limits.x, x));
      this.previewPanY = Math.min(limits.y, Math.max(-limits.y, y));
    },

    clampPreviewPan() {
      if (!this.isPreviewImage) return;
      this.setPreviewPan(this.previewPanX, this.previewPanY);
    },

    startPreviewPan(event) {
      if (this.previewZoom <= 1 || (event.pointerType === 'mouse' && event.button !== 0)) return;

      event.preventDefault();
      this.previewIsPanning = true;
      this.previewPointerId = event.pointerId;
      this.previewPointerStartX = event.clientX;
      this.previewPointerStartY = event.clientY;
      this.previewPanStartX = this.previewPanX;
      this.previewPanStartY = this.previewPanY;
      event.currentTarget.setPointerCapture?.(event.pointerId);
    },

    movePreviewPan(event) {
      if (!this.previewIsPanning || event.pointerId !== this.previewPointerId) return;

      event.preventDefault();
      this.setPreviewPan(
          this.previewPanStartX + event.clientX - this.previewPointerStartX,
          this.previewPanStartY + event.clientY - this.previewPointerStartY,
      );
    },

    finishPreviewPan(event) {
      if (event.pointerId !== this.previewPointerId) return;

      if (event.currentTarget.hasPointerCapture?.(event.pointerId)) {
        event.currentTarget.releasePointerCapture(event.pointerId);
      }
      this.previewIsPanning = false;
      this.previewPointerId = null;
      this.clampPreviewPan();
    },

    prepareVideoThumbnail(event) {
      const video = event.currentTarget;
      if (!video || video.dataset.thumbnailPrepared === 'true') return;

      video.dataset.thumbnailPrepared = 'true';
      const duration = Number(video.duration);
      const firstFrameTime = Number.isFinite(duration) && duration > 0
          ? Math.min(0.05, duration / 2)
          : 0.05;

      try {
        video.currentTime = firstFrameTime;
      } catch {
        this.markVideoThumbnailReady(event);
      }
    },

    markVideoThumbnailReady(event) {
      event.currentTarget?.classList.add('is-ready');
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

    toggleWorkspace() {
      const next = !this.isWorkspace;
      this.isWorkspace = next;


      if (next) {
        this.scheduleViewportScrollLock();

        this.$nextTick(() => {
          this.$refs.gridSection?.scrollTo?.({ top: 0, left: 0 });
        });

        // нативный fullscreen (опционально)
        if (this.workspaceWantsFullscreen) {
          this.requestFullscreenSafe();
        }
      } else {
        this.scheduleViewportScrollLock();

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

    handlePageLifecycleEnd() {
      this.closeRealtime();
    },

  },

  async mounted() {
    this.isUnmounted = false;
    this.updateGridLabelLimit();
    this.gridLabelResizeHandler = () => this.updateGridLabelLimit();
    window.addEventListener('resize', this.gridLabelResizeHandler, { passive: true });
    window.addEventListener('orientationchange', this.gridLabelResizeHandler, { passive: true });
    window.addEventListener('pagehide', this.handlePageLifecycleEnd);
    await this.getAudience();
    this.connectRealtime();
  },

  beforeUnmount() {
    this.isUnmounted = true;
    this.statusConfirmRunId += 1;
    if (this.gridLabelResizeHandler) {
      window.removeEventListener('resize', this.gridLabelResizeHandler);
      window.removeEventListener('orientationchange', this.gridLabelResizeHandler);
      this.gridLabelResizeHandler = null;
    }
    window.removeEventListener('pagehide', this.handlePageLifecycleEnd);
    this.clearStatusConfirmTimers();
    this.clearViewportScrollLock();
    this.closeRealtime()
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


        <div v-if="authStore.isAuthenticated || havePermission" class="header-actions">
          <button v-if="havePermission" class="header-btn edit-btn" @click="editClassroom">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Редактировать
          </button>
          <button v-if="havePermission" class="header-btn delete-btn" @click="openDropClassroomModal">
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
          <p v-if="authStore.isAuthenticated" class="grid-info">
            Кликните по ячейке для деталей
          </p>
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
                      >
                        <TrustedSvgIcon :svg="getEquipmentType(item.type).icon" />
                      </div>

                      <div
                          class="equipment-label"
                          :title="getEquipmentDisplayName(item)"
                      >
                        {{ formatEquipmentGridLabel(item) }}
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

    <Teleport to="body">
      <Transition
          name="modal-fade"
          @before-enter="onEquipmentModalEnter"
          @before-leave="onEquipmentModalBeforeLeave"
          @after-leave="onEquipmentModalAfterLeave"
          @leave-cancelled="onEquipmentModalEnter"
      >
        <div v-if="selectedCell" class="modal active equipment-modal audience-equipment-modal" @click.self="closeModal">
        <div class="modal-content equipment-modal-content">
          <div class="modal-close-upper">
            <button type="button" @click="closeModal" class="close" aria-label="Закрыть" title="Закрыть (Esc)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>

          <header class="equipment-modal-heading">
            <div class="equipment-modal-heading-copy">
              <span class="equipment-modal-kicker">Оборудование</span>
              <h2 class="modal-title">
                {{ getEquipmentType(selectedCell.data.type).name }}
                <span class="modal-subtitle">Ряд {{ selectedCell.row + 1 }}, место {{ selectedCell.col + 1 }}</span>
              </h2>
            </div>

            <div
                class="status-badge"
                :class="selectedCell.data.working ? 'working' : 'broken'"
                role="status"
                :aria-label="`Текущий статус: ${selectedCell.data.working ? 'исправно' : 'неисправно'}`"
            >
              {{ selectedCell.data.working ? 'Исправно' : 'Неисправно' }}
            </div>
          </header>

          <div class="modal-equipment-info">
            <div
                class="modal-equipment-icon"
                :style="{ background: getEquipmentType(selectedCell.data.type).color }"
            >
              <TrustedSvgIcon :svg="getEquipmentType(selectedCell.data.type).icon" />
            </div>
            <div class="modal-equipment-details">
              <div v-if="!hwTitleEdit">
                <h3>{{ selectedCell.data.title || getEquipmentType(selectedCell.data.type).name }}</h3>
                <button
                    v-if="havePermission"
                    type="button"
                    class="modal-inline-icon-button"
                    aria-label="Изменить название"
                    title="Изменить название"
                    @click="hwTitleEdit = true"
                >
                  <svg viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="m16.475 5.408l2.117 2.117m-.756-3.982L12.109 9.27a2.118 2.118 0 0 0-.58 1.082L11 13l2.648-.53c.41-.082.786-.283 1.082-.579l5.727-5.727a1.853 1.853 0 1 0-2.621-2.621"/><path d="M19 15v3a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h3"/></g></svg>
                </button>
              </div>

              <div v-if="hwTitleEdit" class="modal-equipment-inline-edit is-title">
                <input v-model="newHwTitle" class="modal-equipment-inline-input" aria-label="Название оборудования">
                <button type="button" class="modal-inline-icon-button is-save" aria-label="Сохранить название" title="Сохранить" @click="saveHwTitle">
                  <svg viewBox="0 0 20 20"><path fill="currentColor" d="m15.3 5.3l-6.8 6.8l-2.8-2.8l-1.4 1.4l4.2 4.2l8.2-8.2z"/></svg>
                </button>
              </div>

              <div v-if="invNumEdit" class="modal-equipment-inline-edit is-inv">
                <input v-model="newInv_no" class="modal-equipment-inline-input" aria-label="Инвентарный номер">
                <button type="button" class="modal-inline-icon-button is-save" aria-label="Сохранить инвентарный номер" title="Сохранить" @click="saveInv_no">
                  <svg viewBox="0 0 20 20"><path fill="currentColor" d="m15.3 5.3l-6.8 6.8l-2.8-2.8l-1.4 1.4l4.2 4.2l8.2-8.2z"/></svg>
                </button>
              </div>

              <div v-if="!invNumEdit">
                <p>Инвентарный №: {{ selectedCell.data.invNumber || `н\\д` }}</p>
                <button
                    v-if="havePermission"
                    type="button"
                    class="modal-inline-icon-button"
                    aria-label="Изменить инвентарный номер"
                    title="Изменить инвентарный номер"
                    @click="invNumEdit = true"
                >
                  <svg viewBox="0 0 24 24">
                    <path fill="currentColor" d="M3.995 17.207V19.5a.5.5 0 0 0 .5.5h2.298a.5.5 0 0 0 .353-.146l9.448-9.448l-3-3l-9.452 9.448a.5.5 0 0 0-.147.353m10.837-11.04l3 3l1.46-1.46a1 1 0 0 0 0-1.414l-1.585-1.586a1 1 0 0 0-1.414 0z"/>
                  </svg>
                </button>
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

          <div class="form-group equipment-modal-section">
            <div class="problem-header">
              <label class="form-label">Неисправности</label>
              <button
                  v-if="authStore.isAuthenticated"
                  type="button"
                  class="problem-add"
                  :disabled="problemDraft.length >= maxProblems"
                  :title="problemDraft.length >= maxProblems ? 'Достигнут лимит неисправностей' : 'Добавить проблему'"
                  aria-label="Добавить проблему"
                  @click="addProblem"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
                  <path d="M12 5v14M5 12h14"></path>
                </svg>
              </button>
            </div>

            <!-- Компактный список: «Проблема 1», «Проблема 2»… -->
            <div class="problem-list">
              <div
                  ref="problemScroll"
                  class="problem-list-scroll"
                  :class="{ 'is-empty': problemDraft.length === 0 }"
              >
                <div
                    v-for="(problem, index) in problemDraft"
                    :key="index"
                    class="problem-row"
                >
                  <span class="problem-index">{{ index + 1 }}</span>
                  <input
                      v-model="problemDraft[index]"
                      class="problem-input"
                      type="text"
                      maxlength="120"
                      :placeholder="`Проблема ${index + 1}`"
                      :disabled="!authStore.isAuthenticated"
                      @blur="onProblemBlur"
                      @keyup.enter="onProblemEnter(index)"
                  />
                  <button
                      v-if="authStore.isAuthenticated"
                      type="button"
                      class="problem-remove"
                      title="Удалить проблему"
                      @click="removeProblem(index)"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                      <path d="M18 6 6 18M6 6l12 12"></path>
                    </svg>
                  </button>
                </div>

                <div v-if="problemDraft.length === 0" class="problem-empty">
                  {{ authStore.isAuthenticated ? 'Список пуст — добавьте найденные неисправности' : 'Неисправности не указаны' }}
                </div>
              </div>
            </div>
          </div>

          <div
              v-if="statusConfirmIsPending || selectedCell.data.working || havePermission"
              class="action-btns status-action-zone"
          >
            <template v-if="!statusConfirmIsPending">
            <button
                v-if="havePermission && !selectedCell.data.working"
                type="button"
                class="action-btn fix-btn"
                :disabled="statusConfirmLoading"
                aria-label="Отметить оборудование исправным"
                @click="requestWorkingStatus(true)"
            >
              <svg class="action-btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M20 6 9 17l-5-5"/>
              </svg>
              <span>Отметить исправным</span>
            </button>
            <button
                v-if="selectedCell.data.working"
                type="button"
                class="action-btn break-btn"
                :disabled="statusConfirmLoading"
                aria-label="Отметить оборудование неисправным"
                @click="requestWorkingStatus(false)"
            >
              <svg class="action-btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M12 8v5"/>
                <path d="M12 17h.01"/>
                <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/>
              </svg>
              <span>Отметить неисправным</span>
            </button>
            </template>

            <div
                v-else
                class="status-inline-confirm"
                :class="[statusConfirmActionClass, { 'is-urgent': statusConfirmIsUrgent }]"
                :style="statusConfirmProgressStyle"
                aria-live="polite"
            >
              <span class="status-inline-progress" aria-hidden="true"></span>
              <span class="status-inline-mark" aria-hidden="true">
                <svg v-if="pendingWorkingStatus === true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M20 6 9 17l-5-5"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 8v5"/>
                  <path d="M12 17h.01"/>
                  <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/>
                </svg>
              </span>
              <span class="status-inline-copy">
                <span class="status-inline-kicker">Подтверждение</span>
                <span class="status-inline-label">
                  <span>{{ statusConfirmTargetLabel }} через</span>
                  <span class="status-inline-countdown">
                    <strong>{{ statusConfirmRemainingSeconds }}</strong>
                    <span>сек.</span>
                  </span>
                </span>
              </span>
              <button type="button" class="status-inline-btn" :disabled="statusConfirmLoading" @click="closeStatusConfirmModal">
                Отмена
              </button>
              <button type="button" class="status-inline-btn is-primary" :disabled="statusConfirmLoading" @click="confirmWorkingStatus">
                {{ statusConfirmLoading ? '...' : 'Сейчас' }}
              </button>
            </div>
          </div>
          <!-- Список файлов (фото и видео) -->
          <div
              class="hw-files-section equipment-modal-section"
              @dragenter.prevent="isDragOver = true"
              @dragover.prevent
          >
            <!-- Заголовок и кнопка ручного добавления -->
            <div class="hw-section-header">
              <span class="hw-section-title">Вложения ({{ selectedCell.data.files ? selectedCell.data.files.length : 0 }})</span>
              <!-- Компактная кнопка для ручного выбора -->
              <button v-if="canUploadHardwareFiles" type="button" class="hw-add-btn-small" @click="$refs.fileInput.click()" title="Прикрепить файл">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
                </svg>
                Добавить
              </button>
            </div>

            <!-- Сетка файлов -->
            <div v-if="selectedCell.data.files && selectedCell.data.files.length > 0" class="hw-files-grid">
              <div
                  v-for="(file, index) in selectedCell.data.files"
                  :key="file.id"
                  class="hw-file-card"
                  role="button"
                  tabindex="0"
                  :aria-label="`Открыть вложение ${index + 1}`"
                  @click="openPreview(index, $event)"
                  @keydown.enter.prevent="openPreview(index, $event)"
                  @keydown.space.prevent="openPreview(index, $event)"
              >

                <img v-if="file.file_type.startsWith('image/')" :src="resolveFileUrl(file.url)" class="hw-file-preview" alt="" />

                <video v-else class="hw-file-preview" muted playsinline preload="metadata">
                  <source :src="getVideoStreamUrl(file.id)" :type="file.file_type">
                </video>

                <button v-if="havePermission" type="button" @click.stop="requestDeleteFile(file.id)" class="hw-delete-btn" title="Удалить" aria-label="Удалить вложение">
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
    </Teleport>

    <Teleport to="body">
      <Transition>
        <div
            v-if="showUnsavedProblemsConfirm && selectedCell"
            class="unsaved-problems-overlay audience-unsaved-problems-overlay"
            @click.self="cancelUnsavedProblemsClose"
        >
          <section
              class="unsaved-problems-dialog"
              role="dialog"
              aria-modal="true"
              aria-labelledby="unsaved-problems-title"
          >

            <div class="unsaved-problems-copy">
              <h3 id="unsaved-problems-title">Сохранить добавленные проблемы?</h3>
              <p>
                Вы добавили {{ unsavedProblemCount }} {{ unsavedProblemCount === 1 ? 'проблему' : 'проблемы' }},
                но оборудование всё ещё отмечено как исправное. Если просто закрыть окно, список не сохранится.
              </p>
            </div>

            <div class="unsaved-problems-actions">
              <button
                  type="button"
                  class="unsaved-problems-btn is-muted"
                  :disabled="unsavedProblemsSaving"
                  @click="discardUnsavedProblemsAndClose"
              >
                Закрыть без сохранения
              </button>
              <button
                  type="button"
                  class="unsaved-problems-btn"
                  :disabled="unsavedProblemsSaving"
                  @click="cancelUnsavedProblemsClose"
              >
                Вернуться
              </button>
              <button
                  type="button"
                  class="unsaved-problems-btn is-primary"
                  :disabled="unsavedProblemsSaving"
                  @click="saveUnsavedProblemsAndClose"
              >
                {{ unsavedProblemsSaving ? 'Сохраняем...' : 'Пометить неисправным' }}
              </button>
            </div>
          </section>
        </div>
      </Transition>
    </Teleport>

    <Teleport to="body">
      <div
          v-if="selectedCell && hasSpecsEditor && showSpecsModal"
          class="modal active specs-modal-overlay audience-specs-modal-overlay"
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
              >
                <TrustedSvgIcon :svg="getEquipmentType(selectedCell.data.type).icon" />
              </div>

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
                    :class="{
                      'spec-card-pair': item.type === 'pair',
                      'spec-card-list': item.type === 'list'
                    }"
                >
                  <div class="spec-card-icon">
                    <TrustedSvgIcon :svg="getSpecIcon(item.iconKey)" />
                  </div>

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

                  <div v-else-if="item.type === 'list'" class="spec-card-copy spec-card-copy-list">
                    <div class="spec-card-list-heading">
                      <span class="spec-card-label">{{ item.label }}</span>
                      <span class="spec-card-list-count">{{ item.values.length }}</span>
                    </div>

                    <div class="spec-card-tags">
                      <span
                          v-for="value in item.values"
                          :key="value"
                          class="spec-card-tag"
                          :title="value"
                      >
                        {{ value }}
                      </span>
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
              <!-- Шаблоны характеристик: применить готовый набор к одному
                   устройству или сразу ко всем такого же типа в аудитории -->
              <div
                  class="specs-template-panel"
                  :class="{ 'is-expanded': specTemplatesExpanded }"
              >
                <button
                    type="button"
                    class="specs-template-toggle"
                    :aria-expanded="specTemplatesExpanded"
                    @click="specTemplatesExpanded = !specTemplatesExpanded"
                >
                  <span class="specs-template-toggle-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="3" y="3" width="7" height="7" rx="1.5"></rect>
                      <rect x="14" y="3" width="7" height="7" rx="1.5"></rect>
                      <rect x="3" y="14" width="7" height="7" rx="1.5"></rect>
                      <rect x="14" y="14" width="7" height="7" rx="1.5"></rect>
                    </svg>
                  </span>

                  <span class="specs-template-toggle-copy">
                    <strong>Шаблоны конфигурации</strong>
                    <small>{{ specTemplates.length ? `${specTemplates.length} сохранено` : 'Применить или сохранить набор полей' }}</small>
                  </span>

                  <svg class="specs-template-chevron" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="m6 8l4 4l4-4"></path>
                  </svg>
                </button>

                <Transition name="specs-template-reveal">
                  <div v-if="specTemplatesExpanded" class="specs-template-body">
                    <div class="specs-template-row">
                      <select v-model="selectedTemplateId" class="spec-input spec-select specs-template-select">
                        <option value="">{{ specTemplates.length ? '— выберите шаблон —' : 'Шаблоны ещё не созданы' }}</option>
                        <option v-for="tpl in specTemplates" :key="tpl.id" :value="tpl.id">{{ tpl.name }}</option>
                      </select>
                      <button
                          type="button"
                          class="specs-btn specs-btn-secondary"
                          :disabled="!selectedTemplateId"
                          @click="applySpecTemplate"
                      >
                        Применить
                      </button>
                      <button
                          type="button"
                          class="specs-btn specs-btn-ghost-danger"
                          :disabled="!selectedTemplateId"
                          title="Удалить шаблон"
                          @click="deleteSpecTemplate"
                      >
                        Удалить
                      </button>
                    </div>

                    <button
                        type="button"
                        class="specs-template-apply-all"
                        :disabled="!selectedTemplateId || templateApplyingAll"
                        @click="applyTemplateToAll"
                    >
                      {{ templateApplyingAll
                        ? 'Применение…'
                        : `Применить ко всем «${getEquipmentType(selectedCell.data.type).name}» в этой аудитории` }}
                    </button>

                    <div class="specs-template-save">
                      <input
                          v-model="newTemplateName"
                          class="spec-input"
                          type="text"
                          maxlength="64"
                          placeholder="Название нового шаблона"
                      />
                      <button
                          type="button"
                          class="specs-btn specs-btn-primary"
                          :disabled="templateSaving || !newTemplateName.trim()"
                          @click="saveSpecsAsTemplate"
                      >
                        {{ templateSaving ? 'Сохранение…' : 'Сохранить как шаблон' }}
                      </button>
                    </div>
                  </div>
                </Transition>
              </div>

              <section
                  v-for="section in currentSpecSections"
                  :key="section.key"
                  class="spec-form-section"
                  :class="{ 'is-collapsed': isSpecSectionCollapsed(section.key) }"
              >
                <button
                    type="button"
                    class="spec-form-section-toggle"
                    :aria-expanded="!isSpecSectionCollapsed(section.key)"
                    :aria-controls="`spec-section-${section.key}`"
                    @click="toggleSpecSection(section.key)"
                >
                  <span class="spec-form-section-icon" aria-hidden="true">
                    <svg v-if="section.key === 'hardware'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="6" y="6" width="12" height="12" rx="2"></rect>
                      <path d="M9 9h6v6H9zM9 2v4m6-4v4M9 18v4m6-4v4M2 9h4m12 0h4M2 15h4m12 0h4"></path>
                    </svg>
                    <svg v-else-if="section.key === 'system'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="3" y="4" width="18" height="16" rx="3"></rect>
                      <path d="M3 8h18M7 6h.01M10 6h.01m-3 7l2 2l-2 2m5 0h5"></path>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="3" y="6" width="18" height="12" rx="3"></rect>
                      <path d="M7 10h2m2 0h2m2 0h2M7 14h10"></path>
                    </svg>
                  </span>
                  <span class="spec-form-section-copy">
                    <strong>{{ section.title }}</strong>
                    <small>{{ section.description }}</small>
                  </span>
                  <svg class="spec-form-section-chevron" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <path d="m6 8l4 4l4-4"></path>
                  </svg>
                </button>

                <div
                    :id="`spec-section-${section.key}`"
                    class="spec-form-section-body"
                    :class="{ 'is-collapsed': isSpecSectionCollapsed(section.key) }"
                    :aria-hidden="isSpecSectionCollapsed(section.key)"
                    :inert="isSpecSectionCollapsed(section.key)"
                >
                  <div class="spec-form-section-body-inner">
                    <div class="spec-form-section-grid">
                  <div
                      v-for="group in section.groups"
                      :key="group.key"
                      class="spec-form-group"
                      :class="{
                        'spec-form-group-double': group.fields.length === 2,
                        'spec-form-group-full': group.full,
                        'spec-form-group-os': group.variant === 'os',
                        'spec-form-group-software': group.variant === 'software',
                        'spec-form-group-switch': group.variant === 'switch'
                      }"
                  >
                <div
                    v-for="fieldKey in group.fields"
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
                      :maxlength="currentSpecFieldMap[fieldKey].maxLength || null"
                      :placeholder="currentSpecFieldMap[fieldKey].placeholder || ''"
                  />

                  <div
                      v-else-if="currentSpecFieldMap[fieldKey].type === 'os-choice'"
                      class="spec-os-choice"
                      role="radiogroup"
                      :aria-label="currentSpecFieldMap[fieldKey].label"
                  >
                    <button
                        v-for="option in currentSpecFieldMap[fieldKey].options"
                        :key="option.value"
                        type="button"
                        role="radio"
                        class="spec-os-option"
                        :class="{ 'is-active': specsDraft[fieldKey] === option.value }"
                        :aria-label="option.label"
                        :aria-checked="specsDraft[fieldKey] === option.value"
                        :title="specsDraft[fieldKey] === option.value ? 'Снять выбор' : option.label"
                        @click="selectOperatingSystem(option.value)"
                    >
                      <span class="spec-os-option-icon" :class="`is-${option.value}`">
                        <TrustedSvgIcon :svg="option.icon" />
                      </span>
                      <span v-if="!option.iconOnly">{{ option.label }}</span>
                    </button>
                  </div>

                  <select
                      v-else-if="currentSpecFieldMap[fieldKey].type === 'dependent-select'"
                      v-model="specsDraft[fieldKey]"
                      class="spec-input spec-select"
                      :disabled="!specsDraft.operating_system"
                  >
                    <option value="">
                      {{ specsDraft.operating_system ? 'Не выбрано' : currentSpecFieldMap[fieldKey].emptyLabel }}
                    </option>
                    <option
                        v-for="option in getOsEditionOptions()"
                        :key="option"
                        :value="option"
                    >
                      {{ option }}
                    </option>
                  </select>

                  <div
                      v-else-if="currentSpecFieldMap[fieldKey].type === 'software-checklist'"
                      class="software-editor"
                  >
                    <div class="software-presets">
                      <div class="software-presets-head">
                        <span>Наборы ПО</span>
                        <small>Выберите готовый состав</small>
                      </div>

                      <div class="software-preset-list">
                        <button
                            v-for="preset in softwarePresets"
                            :key="preset.id"
                            type="button"
                            class="software-preset-btn"
                            :class="{ 'is-active': isSoftwarePresetActive(fieldKey, preset) }"
                            :aria-pressed="isSoftwarePresetActive(fieldKey, preset)"
                            @click="applySoftwarePreset(fieldKey, preset)"
                        >
                          {{ preset.label }}
                        </button>
                      </div>
                    </div>

                    <div class="software-selection-head">
                      <span>{{ getSpecListValues(fieldKey).length }} выбрано</span>
                      <button
                          v-if="getSpecListValues(fieldKey).length"
                          type="button"
                          class="software-clear-btn"
                          @click="clearSoftware(fieldKey)"
                      >
                        Очистить
                      </button>
                    </div>

                    <div class="software-options" role="group" aria-label="Каталог программ">
                      <label
                          v-for="software in softwareOptions"
                          :key="software.value"
                          class="software-option"
                          :class="{ 'is-selected': isSoftwareSelected(fieldKey, software.value) }"
                          :title="software.value"
                      >
                        <input
                            type="checkbox"
                            :checked="isSoftwareSelected(fieldKey, software.value)"
                            @change="toggleSoftwareItem(fieldKey, software.value)"
                        />
                        <span class="software-option-check" aria-hidden="true">
                          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="m4 8l2.5 2.5L12 5"></path>
                          </svg>
                        </span>
                        <span class="software-option-label">{{ software.label }}</span>
                      </label>
                    </div>

                    <div v-if="getCustomSoftwareValues(fieldKey).length" class="software-custom-list">
                      <span
                          v-for="item in getCustomSoftwareValues(fieldKey)"
                          :key="item"
                          class="spec-list-chip"
                      >
                        <span class="spec-list-chip-text" :title="item">{{ item }}</span>
                        <button
                            type="button"
                            class="spec-list-remove"
                            :aria-label="`Удалить программу «${item}»`"
                            @click="removeSpecListValue(fieldKey, item)"
                        >
                          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                            <path d="M6 6l8 8M14 6l-8 8"></path>
                          </svg>
                        </button>
                      </span>
                    </div>

                    <Transition name="software-custom">
                      <div v-if="customSoftwareExpanded" class="spec-list-add-row software-custom-input">
                        <input
                            ref="customSoftwareInput"
                            v-model="specListInputs[fieldKey]"
                            class="spec-input spec-list-input"
                            type="text"
                            :maxlength="currentSpecFieldMap[fieldKey].itemMaxLength"
                            :placeholder="currentSpecFieldMap[fieldKey].placeholder"
                            @keydown.enter.prevent="addSpecListItem(fieldKey)"
                            @keydown.esc.prevent="customSoftwareExpanded = false"
                        />
                        <button
                            type="button"
                            class="spec-list-add-btn"
                            aria-label="Добавить программу"
                            :disabled="!String(specListInputs[fieldKey] || '').trim()"
                            @click="addSpecListItem(fieldKey)"
                        >
                          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                            <path d="M10 4v12M4 10h12"></path>
                          </svg>
                          <span>Добавить</span>
                        </button>
                      </div>
                    </Transition>

                    <button
                        v-if="!customSoftwareExpanded"
                        type="button"
                        class="software-custom-trigger"
                        @click="openCustomSoftwareInput"
                    >
                      <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                        <path d="M9 3v12M3 9h12"></path>
                      </svg>
                      Другая программа
                    </button>

                    <div class="spec-list-hint software-limit-hint">
                      До {{ currentSpecFieldMap[fieldKey].maxItems }} программ, включая собственные
                    </div>
                  </div>

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
              </section>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="dropClassroomModalShow" class="modal audience-drop-classroom-overlay">
        <div class="modal-content pt-1">
          <h2 class="modal-title">Удаление аудитории</h2>
          <p style="font-size: 16px; color: #64748b; margin-bottom: 24px;">
            Вы уверены, что хотите удалить <strong>аудиторию №{{ classroom.number }}</strong>?
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
    </Teleport>

    <Teleport to="body">
      <Transition>
        <div v-if="showConfirmModal" class="hw-confirm-overlay audience-file-confirm-overlay" @click.self="closeConfirmModal">
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
      </Transition>
    </Teleport>

    <Teleport to="body">
      <Transition name="hw-lightbox-fade">
        <div
            v-if="previewIndex !== null && selectedCell"
            ref="lightboxDialog"
            class="hw-lightbox audience-lightbox-overlay"
            role="dialog"
            aria-modal="true"
            tabindex="-1"
            :aria-label="`Предпросмотр вложений: ${selectedEquipmentDisplayName}`"
            @click.self="closePreview"
        >
          <div class="hw-lb-shell" @click.self="closePreview">
          <header class="hw-lb-header">
            <div class="hw-lb-context">
              <span class="hw-lb-kind-icon" aria-hidden="true">
                <svg v-if="isPreviewImage" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="4" width="18" height="16" rx="3"></rect>
                  <circle cx="8.5" cy="9" r="1.5"></circle>
                  <path d="m4 17 4.5-4.5 3.5 3 2.5-2.5 5.5 5"></path>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="5" width="14" height="14" rx="3"></rect>
                  <path d="m17 10 4-2v8l-4-2z"></path>
                </svg>
              </span>
              <span class="hw-lb-context-copy">
                <strong>{{ selectedEquipmentDisplayName }}</strong>
                <span class="hw-lb-meta" aria-live="polite">
                  <span>{{ isPreviewImage ? 'Фото' : 'Видео' }}</span>
                  <span class="hw-lb-meta-separator" aria-hidden="true"></span>
                  <span>{{ previewIndex + 1 }} из {{ selectedCell.data.files.length }}</span>
                </span>
              </span>
            </div>

            <button
                type="button"
                class="hw-lb-close"
                aria-label="Закрыть предпросмотр"
                title="Закрыть (Esc)"
                @click="closePreview"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M6 6l12 12M18 6 6 18"></path>
              </svg>
            </button>
          </header>

          <main class="hw-lb-content" @click.stop>
            <div
                class="hw-lb-stage"
                :class="{ 'is-video': isPreviewVideo, 'is-image-zoomed': isPreviewImage && previewZoom !== 1 }"
                @wheel="handlePreviewWheel"
            >
              <Transition name="hw-ambient-swap">
                <div
                    v-if="isPreviewImage"
                    :key="`ambient-${currentPreviewFile.id}`"
                    class="hw-lb-ambient"
                    aria-hidden="true"
                >
                  <img :src="resolveFileUrl(currentPreviewFile.url)" alt="" draggable="false" />
                </div>
              </Transition>
              <div class="hw-lb-stage-shade" aria-hidden="true"></div>

              <button
                  v-if="selectedCell.data.files.length > 1"
                  type="button"
                  class="hw-lb-nav hw-lb-prev"
                  aria-label="Предыдущее вложение"
                  title="Предыдущее вложение (←)"
                  @click.stop="prevPreview"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="m14.5 5-7 7 7 7"></path>
                </svg>
              </button>

              <div ref="previewMediaFrame" class="hw-lb-media-frame">
                <Transition name="hw-media-swap" mode="out-in">
                  <img
                      v-if="isPreviewImage"
                      ref="previewImage"
                      :key="`image-${currentPreviewFile.id}`"
                      :src="resolveFileUrl(currentPreviewFile.url)"
                      :alt="`Фото оборудования ${selectedEquipmentDisplayName}`"
                      class="hw-lb-image"
                      :class="{
                        'is-pannable': previewZoom > 1,
                        'is-panning': previewIsPanning
                      }"
                      :style="previewImageStyle"
                      title="Двойной клик — увеличить или вписать"
                      draggable="false"
                      @load="clampPreviewPan"
                      @dblclick.stop="togglePreviewZoom"
                      @pointerdown="startPreviewPan"
                      @pointermove="movePreviewPan"
                      @pointerup="finishPreviewPan"
                      @pointercancel="finishPreviewPan"
                  />

                  <video
                      v-else-if="isPreviewVideo"
                      :key="`video-${currentPreviewFile.id}`"
                      :src="getVideoStreamUrl(currentPreviewFile.id)"
                      controls
                      autoplay
                      playsinline
                      preload="metadata"
                      class="hw-lb-video"
                  ></video>
                </Transition>
              </div>

              <div
                  v-if="isPreviewImage"
                  class="hw-lb-zoom"
                  role="group"
                  aria-label="Масштаб изображения"
                  @dblclick.stop
              >
                <button
                    type="button"
                    class="hw-lb-zoom-btn"
                    :disabled="previewZoom <= previewZoomMin"
                    aria-label="Уменьшить изображение"
                    title="Уменьшить (−)"
                    @click.stop="zoomPreviewOut"
                >
                  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                    <path d="M5 10h10"></path>
                  </svg>
                </button>
                <button
                    type="button"
                    class="hw-lb-zoom-value"
                    :class="{ 'is-fit': previewZoom === 1 }"
                    aria-label="Вписать изображение в экран"
                    title="Вписать в экран (0)"
                    @click.stop="resetPreviewTransform"
                >
                  {{ previewZoomLabel }}
                </button>
                <button
                    type="button"
                    class="hw-lb-zoom-btn"
                    :disabled="previewZoom >= previewZoomMax"
                    aria-label="Увеличить изображение"
                    title="Увеличить (+)"
                    @click.stop="zoomPreviewIn"
                >
                  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                    <path d="M5 10h10M10 5v10"></path>
                  </svg>
                </button>
              </div>

              <button
                  v-if="selectedCell.data.files.length > 1"
                  type="button"
                  class="hw-lb-nav hw-lb-next"
                  aria-label="Следующее вложение"
                  title="Следующее вложение (→)"
                  @click.stop="nextPreview"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="m9.5 5 7 7-7 7"></path>
                </svg>
              </button>
            </div>
          </main>

          <footer v-if="selectedCell.data.files.length > 1" class="hw-lb-footer">
            <div class="hw-lb-filmstrip" aria-label="Список вложений">
              <button
                  v-for="(file, index) in selectedCell.data.files"
                  :key="`preview-thumb-${file.id}`"
                  type="button"
                  class="hw-lb-thumb"
                  :class="{ 'is-active': index === previewIndex }"
                  :aria-label="`Открыть вложение ${index + 1}`"
                  :aria-current="index === previewIndex ? 'true' : undefined"
                  @click="openPreview(index)"
              >
                <img
                    v-if="file.file_type.startsWith('image/')"
                    :src="resolveFileUrl(file.url)"
                    alt=""
                    loading="lazy"
                    draggable="false"
                />
                <template v-else>
                  <video
                      :src="getVideoStreamUrl(file.id)"
                      class="hw-lb-thumb-video"
                      muted
                      playsinline
                      preload="metadata"
                      tabindex="-1"
                      aria-hidden="true"
                      @loadedmetadata="prepareVideoThumbnail"
                      @loadeddata="markVideoThumbnailReady"
                      @seeked="markVideoThumbnailReady"
                  ></video>
                  <span class="hw-lb-video-thumb" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M8.2 6.8a1 1 0 0 1 1.53-.85l7.2 4.7a1 1 0 0 1 0 1.7l-7.2 4.7a1 1 0 0 1-1.53-.84z"></path>
                    </svg>
                  </span>
                </template>
              </button>
            </div>
          </footer>
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>

</template>

<style scoped>
.page-viewer {
  background-size: 400% 400%;
  animation: gradientShift 20s ease infinite;
  min-height: 100vh;
  padding-bottom: 40px;
  overflow-x: clip;
}

.page-viewer.workspace .top-header,
.page-viewer.workspace .stats-section {
  display: none;
}

@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
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
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 900;        /* выше AppHeader, ниже модалок */
  border-radius: 0;
  margin: 0;
  padding: 16px;
  overflow: auto;
  width: 100vw;
  max-width: 100vw;
  height: 100vh;
  height: 100dvh;
  height: var(--audience-modal-vh, 100dvh);
  max-height: 100vh;
  max-height: 100dvh;
  max-height: var(--audience-modal-vh, 100dvh);
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  transform: none;
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
  display: block;
  font-size: var(--font-size);
  font-weight: var(--equipment-label-fw);
  line-height: 1.15;
  text-align: center;
  color: #334155;
  max-width: min(100%, 15ch);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Modal */
:global(html.audience-viewport-locked),
:global(body.audience-viewport-locked) {
  overflow: hidden !important;
  overscroll-behavior: none;
}

:global(#app.audience-app-viewport-locked) .modal,
:global(#app.audience-app-viewport-locked) .hw-lightbox {
  transform: translate3d(0, var(--audience-scroll-lock-offset, 0px), 0);
}

:global(body > .audience-equipment-modal),
:global(body > .audience-specs-modal-overlay),
:global(body > .audience-unsaved-problems-overlay),
:global(body > .audience-drop-classroom-overlay),
:global(body > .audience-file-confirm-overlay),
:global(body > .audience-lightbox-overlay) {
  position: fixed !important;
  inset: auto 0 0 0 !important;
  top: var(--audience-modal-top, 0px) !important;
  width: 100vw !important;
  height: var(--audience-modal-vh, 100dvh) !important;
  transform: none !important;
}

:global(body.audience-modal-events-locked > .audience-equipment-modal),
:global(body.audience-modal-events-locked > .audience-specs-modal-overlay),
:global(body.audience-modal-events-locked > .audience-unsaved-problems-overlay),
:global(body.audience-modal-events-locked > .audience-drop-classroom-overlay),
:global(body.audience-modal-events-locked > .audience-file-confirm-overlay),
:global(body.audience-modal-events-locked > .audience-lightbox-overlay) {
  position: absolute !important;
  top: var(--audience-scroll-lock-offset, 0px) !important;
  bottom: auto !important;
  min-height: var(--audience-modal-vh, 100dvh) !important;
}

.modal {
  position: fixed;
  z-index: 1000;
  inset: 0;
  left: 0;
  top: var(--audience-modal-top, 0px);
  width: 100vw;
  height: 100vh;
  height: 100dvh;
  height: var(--audience-modal-vh, 100dvh);
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  backdrop-filter: blur(4px);
  overflow-y: auto;
  overscroll-behavior: contain;
}

.equipment-modal {
  align-items: center;
  overflow-y: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
}

.specs-modal-overlay {
  z-index: 2400;
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

.equipment-modal-content {
  position: relative;
  margin: 0;
  padding-top: 20px;
  max-height: calc(100vh - 40px);
  max-height: calc(100dvh - 40px);
  max-height: calc(var(--audience-modal-vh, 100dvh) - 40px);
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
}

.equipment-modal .modal-close-upper {
  position: absolute;
  top: 16px;
  right: 12px;
  z-index: 4;
  padding: 0;
}

.equipment-modal .modal-close-upper button {
  margin: 0;
}

.equipment-modal .modal-title {
  margin-top: 0;
  padding-right: 52px;
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
  max-height: calc(100dvh - 40px);
  max-height: calc(var(--audience-modal-vh, 100dvh) - 40px);
  overflow-y: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
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

.specs-btn-ghost-danger {
  background: rgba(254, 226, 226, 0.7);
  color: #dc2626;
}

.specs-btn-ghost-danger:hover:not(:disabled) {
  background: rgba(254, 202, 202, 0.9);
}

/* ── Панель шаблонов характеристик ── */
.specs-template-panel {
  border: 1px solid #dbe4ee;
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.82);
  overflow: hidden;
  transition: border-color 0.18s ease, background-color 0.18s ease;
}

.specs-template-panel.is-expanded {
  border-color: #bfdbfe;
  background: rgba(248, 250, 252, 0.96);
}

.specs-template-toggle {
  width: 100%;
  min-height: 52px;
  padding: 8px 12px;
  border: 0;
  background: transparent;
  color: #334155;
  display: flex;
  align-items: center;
  gap: 10px;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.16s ease;
}

.specs-template-toggle:hover {
  background: rgba(219, 234, 254, 0.48);
}

.specs-template-toggle:focus-visible {
  outline: 3px solid rgba(59, 130, 246, 0.22);
  outline-offset: -3px;
}

.specs-template-toggle-icon {
  width: 32px;
  height: 32px;
  flex: 0 0 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: #eaf2ff;
  color: #2563eb;
}

.specs-template-toggle-icon svg {
  width: 18px;
  height: 18px;
}

.specs-template-toggle-copy {
  min-width: 0;
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 2px;
}

.specs-template-toggle-copy strong {
  color: #1e293b;
  font-size: 13px;
  font-weight: 700;
}

.specs-template-toggle-copy small {
  overflow: hidden;
  color: #64748b;
  font-size: 11px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.specs-template-chevron {
  width: 18px;
  height: 18px;
  flex: 0 0 18px;
  color: #64748b;
  transition: transform 0.2s ease;
}

.specs-template-panel.is-expanded .specs-template-chevron {
  transform: rotate(180deg);
}

.specs-template-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  border-top: 1px solid #e2e8f0;
}

.specs-template-reveal-enter-active,
.specs-template-reveal-leave-active {
  transition: opacity 0.16s ease, transform 0.16s ease;
}

.specs-template-reveal-enter-from,
.specs-template-reveal-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.specs-template-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.specs-template-select {
  flex: 1;
  min-width: 160px;
}

.specs-template-apply-all {
  width: 100%;
  border: 1px solid rgba(96, 165, 250, 0.7);
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 13px;
  font-weight: 700;
  color: #1d4ed8;
  background: rgba(219, 234, 254, 0.6);
  cursor: pointer;
  transition: all 0.2s ease;
}

.specs-template-apply-all:hover:not(:disabled) {
  background: rgba(191, 219, 254, 0.9);
  transform: translateY(-1px);
}

.specs-template-apply-all:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.specs-template-save {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  border-top: 1px solid rgba(148, 163, 184, 0.3);
  padding-top: 12px;
}

.specs-template-save .spec-input {
  flex: 1;
  min-width: 160px;
}

:global(html[data-theme='dark']) .specs-template-panel {
  border-color: rgba(51, 65, 85, 0.96);
  background: rgba(15, 23, 42, 0.72);
}

:global(html[data-theme='dark']) .specs-template-apply-all {
  border-color: rgba(96, 165, 250, 0.45);
  color: #bfdbfe;
  background: rgba(37, 99, 235, 0.18);
}

:global(html[data-theme='dark']) .specs-template-apply-all:hover:not(:disabled) {
  background: rgba(37, 99, 235, 0.3);
}

:global(html[data-theme='dark']) .specs-btn-ghost-danger {
  background: rgba(127, 29, 29, 0.35);
  color: #fca5a5;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-template-panel) {
  background: rgba(15, 23, 42, 0.72) !important;
  border-color: rgba(51, 65, 85, 0.96) !important;
  box-shadow: inset 0 1px 0 rgba(148, 163, 184, 0.06) !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-template-panel.is-expanded) {
  border-color: rgba(59, 130, 246, 0.52) !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-template-toggle) {
  color: #cbd5e1;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-template-toggle:hover) {
  background: rgba(30, 41, 59, 0.78);
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-template-toggle-icon) {
  background: rgba(37, 99, 235, 0.2);
  color: #93c5fd;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-template-toggle-copy strong) {
  color: #dbe4ef;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-template-toggle-copy small),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-template-chevron) {
  color: #8291a7;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-template-body) {
  border-top-color: rgba(51, 65, 85, 0.9);
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-template-save) {
  border-top-color: rgba(51, 65, 85, 0.9) !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-template-panel .spec-input) {
  background:
      linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(2, 6, 23, 0.76)),
      #020617 !important;
  border-color: rgba(71, 85, 105, 0.94) !important;
  color: #dbe4ef !important;
  box-shadow: inset 0 1px 0 rgba(148, 163, 184, 0.08) !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-template-panel .spec-input::placeholder) {
  color: #64748b !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-template-panel .spec-input:focus) {
  border-color: rgba(96, 165, 250, 0.9) !important;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.16) !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-template-panel .spec-select) {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20' fill='none'%3E%3Cpath d='m5 7.5l5 5l5-5' stroke='%23dbe4ef' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") !important;
  background-repeat: no-repeat !important;
  background-position: right 14px center !important;
  background-size: 16px 16px !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-template-apply-all) {
  background:
      linear-gradient(135deg, rgba(37, 99, 235, 0.28), rgba(14, 165, 233, 0.12)),
      rgba(15, 23, 42, 0.7) !important;
  border-color: rgba(96, 165, 250, 0.48) !important;
  color: #bfdbfe !important;
  box-shadow: inset 0 1px 0 rgba(191, 219, 254, 0.08) !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-template-apply-all:hover:not(:disabled)) {
  background:
      linear-gradient(135deg, rgba(37, 99, 235, 0.36), rgba(14, 165, 233, 0.18)),
      rgba(15, 23, 42, 0.84) !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-template-panel .specs-btn-ghost-danger) {
  background: rgba(127, 29, 29, 0.38) !important;
  color: #fca5a5 !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-template-panel .specs-btn-ghost-danger:hover:not(:disabled)) {
  background: rgba(153, 27, 27, 0.48) !important;
  color: #fecaca !important;
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

.spec-card-list {
  grid-column: 1 / -1;
}

.spec-card-copy-list {
  gap: 10px;
}

.spec-card-list-heading {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spec-card-list-count {
  min-width: 24px;
  height: 20px;
  padding: 0 7px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 11px;
  font-weight: 800;
}

.spec-card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  max-height: 112px;
  overflow-y: auto;
  padding-right: 4px;
}

.spec-card-tag {
  max-width: 100%;
  overflow: hidden;
  padding: 6px 9px;
  border: 1px solid #d7e2f0;
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.82);
  color: #334155;
  font-size: 12px;
  font-weight: 650;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  gap: 12px;
}

.spec-form-section {
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  overflow: hidden;
  transition: border-color 0.18s ease, background-color 0.18s ease;
}

.spec-form-section-toggle {
  width: 100%;
  min-height: 56px;
  padding: 12px 14px;
  border: 0;
  background: transparent;
  color: #334155;
  display: flex;
  align-items: center;
  gap: 10px;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.16s ease;
}

.spec-form-section-toggle:hover {
  background: rgba(239, 246, 255, 0.72);
}

.spec-form-section-toggle:focus-visible {
  outline: 3px solid rgba(59, 130, 246, 0.22);
  outline-offset: -3px;
}

.spec-form-section-icon {
  width: 32px;
  height: 32px;
  flex: 0 0 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: #eaf2ff;
  color: #2563eb;
}

.spec-form-section-icon svg {
  width: 18px;
  height: 18px;
}

.spec-form-section-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.spec-form-section-copy strong {
  color: #1e293b;
  font-size: 14px;
  font-weight: 750;
  line-height: 1.25;
}

.spec-form-section-copy small {
  color: #64748b;
  font-size: 11px;
  font-weight: 500;
  line-height: 1.35;
}

.spec-form-section-chevron {
  width: 18px;
  height: 18px;
  flex: 0 0 18px;
  margin-left: auto;
  color: #64748b;
  transition: transform 0.2s ease, color 0.16s ease;
}

.spec-form-section.is-collapsed .spec-form-section-chevron {
  transform: rotate(-90deg);
}

.spec-form-section-body {
  display: grid;
  grid-template-rows: 1fr;
  opacity: 1;
  transition:
      grid-template-rows 0.22s cubic-bezier(0.22, 1, 0.36, 1),
      opacity 0.16s ease;
}

.spec-form-section-body.is-collapsed {
  grid-template-rows: 0fr;
  opacity: 0;
}

.spec-form-section-body-inner {
  min-height: 0;
  overflow: hidden;
}

@media (prefers-reduced-motion: reduce) {
  .spec-form-section-body,
  .spec-form-section-chevron {
    transition: none;
  }
}

.spec-form-section-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 14px;
  padding: 0 14px 14px;
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
  font-size: 12px;
  font-weight: 700;
  color: #334155;
}

.spec-input-wrap {
  position: relative;
}

.spec-input {
  width: 100%;
  min-height: 42px;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 11px;
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

.spec-os-choice {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 7px;
}

.spec-os-option {
  min-width: 0;
  min-height: 42px;
  padding: 7px 9px;
  border: 1px solid #cbd5e1;
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.92);
  color: #475569;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  font-size: 12px;
  font-weight: 650;
  cursor: pointer;
  transition: border-color 0.16s ease, background-color 0.16s ease, color 0.16s ease;
}

.spec-os-option:hover:not(.is-active) {
  border-color: #94a3b8;
  background: #f8fafc;
  color: #1e293b;
}

.spec-os-option.is-active {
  border-color: #60a5fa;
  background: #eaf2ff;
  color: #1d4ed8;
  box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.08);
}

.spec-os-option:focus-visible,
.software-option:has(input:focus-visible),
.software-preset-btn:focus-visible,
.software-clear-btn:focus-visible,
.software-custom-trigger:focus-visible {
  outline: 3px solid rgba(59, 130, 246, 0.22);
  outline-offset: 2px;
}

.spec-os-option-icon {
  width: 20px;
  height: 20px;
  flex: 0 0 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.spec-os-option-icon :deep(svg) {
  width: 18px;
  height: 18px;
}

.spec-os-option-icon.is-macos :deep(svg) {
  width: 60px;
  height: 40px;
}

.spec-os-option-icon.is-macos {
  width: 36px;
  flex-basis: 36px;
}

.spec-os-option-icon.is-linux :deep(svg) {
  width: 17px;
  height: 20px;
}

.software-editor {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.software-presets {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e2e8f0;
}

.software-presets-head {
  display: flex;
  flex-direction: column;
  gap: 1px;
  white-space: nowrap;
}

.software-presets-head span {
  color: #334155;
  font-size: 11px;
  font-weight: 750;
}

.software-presets-head small {
  color: #94a3b8;
  font-size: 9px;
}

.software-preset-list {
  min-width: 0;
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 6px;
}

.software-preset-btn {
  min-height: 28px;
  padding: 4px 9px;
  border: 1px solid #d7e0ea;
  border-radius: 9px;
  background: #ffffff;
  color: #526176;
  font-size: 10px;
  font-weight: 650;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  transition: border-color 0.16s ease, background-color 0.16s ease, color 0.16s ease;
}

.software-preset-btn:hover:not(.is-active) {
  border-color: #94a3b8;
  color: #1e293b;
}

.software-preset-btn.is-active {
  border-color: #60a5fa;
  background: #eaf2ff;
  color: #1d4ed8;
}

.software-selection-head {
  min-height: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: #64748b;
  font-size: 10px;
  font-weight: 650;
}

.software-clear-btn {
  padding: 2px 0;
  border: 0;
  background: transparent;
  color: #64748b;
  font: inherit;
  cursor: pointer;
  transition: color 0.16s ease;
}

.software-clear-btn:hover {
  color: #dc2626;
}

.software-options {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 7px;
}

.software-option {
  position: relative;
  min-width: 0;
  min-height: 36px;
  padding: 6px 8px;
  border: 1px solid #dbe3ec;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.82);
  color: #475569;
  display: flex;
  align-items: center;
  gap: 7px;
  cursor: pointer;
  user-select: none;
  transition: border-color 0.16s ease, background-color 0.16s ease, color 0.16s ease;
}

.software-option:hover:not(.is-selected) {
  border-color: #a8b6c7;
  background: #f8fafc;
}

.software-option.is-selected {
  border-color: #93c5fd;
  background: #eff6ff;
  color: #1e40af;
}

.software-option input {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  opacity: 0;
  pointer-events: none;
}

.software-option-check {
  width: 17px;
  height: 17px;
  flex: 0 0 17px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #b8c5d4;
  border-radius: 6px;
  background: #ffffff;
  color: transparent;
  transition: border-color 0.16s ease, background-color 0.16s ease, color 0.16s ease;
}

.software-option-check svg {
  width: 12px;
  height: 12px;
}

.software-option.is-selected .software-option-check {
  border-color: #2563eb;
  background: #2563eb;
  color: #ffffff;
}

.software-option-label {
  min-width: 0;
  overflow: hidden;
  font-size: 11px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.software-custom-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.software-custom-trigger {
  width: fit-content;
  min-height: 30px;
  padding: 4px 9px;
  border: 1px dashed #aebdce;
  border-radius: 9px;
  background: transparent;
  color: #526176;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  font-weight: 650;
  cursor: pointer;
  transition: border-color 0.16s ease, color 0.16s ease, background-color 0.16s ease;
}

.software-custom-trigger:hover {
  border-color: #60a5fa;
  background: #eff6ff;
  color: #1d4ed8;
}

.software-custom-trigger svg {
  width: 14px;
  height: 14px;
}

.software-custom-input {
  max-width: 420px;
}

.software-limit-hint {
  justify-content: flex-start;
}

.software-custom-enter-active,
.software-custom-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.software-custom-enter-from,
.software-custom-leave-to {
  opacity: 0;
  transform: translateY(-3px);
}

.spec-list-editor {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.spec-list-items {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  max-height: 126px;
  overflow-y: auto;
  padding: 10px;
  border: 1px solid #dbe4ee;
  border-radius: 13px;
  background: rgba(248, 250, 252, 0.86);
}

.spec-list-chip {
  max-width: 100%;
  min-height: 30px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 5px 4px 9px;
  border: 1px solid #bfdbfe;
  border-radius: 9px;
  background: #eff6ff;
  color: #1e3a5f;
  font-size: 12px;
  font-weight: 650;
}

.spec-list-chip-text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.spec-list-remove {
  width: 23px;
  height: 23px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  transition: background-color 0.16s ease, color 0.16s ease;
}

.spec-list-remove:hover {
  background: #fee2e2;
  color: #dc2626;
}

.spec-list-remove:focus-visible,
.spec-list-add-btn:focus-visible {
  outline: 3px solid rgba(59, 130, 246, 0.24);
  outline-offset: 2px;
}

.spec-list-remove svg,
.spec-list-add-btn svg {
  width: 16px;
  height: 16px;
}

.spec-list-empty {
  padding: 10px 12px;
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  color: #64748b;
  font-size: 12px;
  text-align: center;
}

.spec-list-add-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
}

.spec-list-input {
  min-width: 0;
}

.spec-list-add-btn {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 13px;
  border: 1px solid #2563eb;
  border-radius: 12px;
  background: #2563eb;
  color: #ffffff;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.16s ease, border-color 0.16s ease;
}

.spec-list-add-btn:hover:not(:disabled) {
  border-color: #1d4ed8;
  background: #1d4ed8;
}

.spec-list-add-btn:disabled {
  border-color: #cbd5e1;
  background: #e2e8f0;
  color: #94a3b8;
  cursor: not-allowed;
}

.spec-list-hint {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #64748b;
  font-size: 11px;
  line-height: 1.4;
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
  gap: 10px;
  min-width: 0;
}

.spec-form-group-double {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.spec-form-group-full {
  grid-column: 1 / -1;
}

.spec-form-group-os {
  grid-template-columns: minmax(0, 1.35fr) minmax(190px, 1fr);
  padding-bottom: 13px;
  border-bottom: 1px solid #e2e8f0;
}

.spec-form-group-software {
  padding-top: 1px;
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

:global(html[data-theme='dark']) .audience-specs-modal-overlay {
  background: rgba(2, 6, 23, 0.72);
}

:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-modal-content {
  color: #e2e8f0;
  background:
      radial-gradient(circle at top left, rgba(37, 99, 235, 0.18), transparent 34%),
      radial-gradient(circle at 88% 12%, rgba(14, 165, 233, 0.1), transparent 30%),
      linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(2, 6, 23, 0.98));
  border: 1px solid rgba(51, 65, 85, 0.95);
  box-shadow: 0 28px 72px rgba(2, 6, 23, 0.56);
}

:global(html[data-theme='dark']) .audience-specs-modal-overlay .modal-close-upper button {
  background: rgba(30, 41, 59, 0.82);
  border: 1px solid rgba(51, 65, 85, 0.95);
}

:global(html[data-theme='dark']) .audience-specs-modal-overlay .modal-close-upper button:hover {
  background: rgba(51, 65, 85, 0.9);
}

:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-modal-heading,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-modal-name,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-meta-value,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .spec-card-value,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-empty-title,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-form-banner-title,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-modal-progress-head {
  color: #e2e8f0;
}

:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-modal-description,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-meta-label,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .spec-card-label,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-empty-text,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-form-banner-text,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .spec-form-label,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .spec-suffix,
:global(html[data-theme='dark']) .spec-form-label {
  color: #cbd5e1 !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-form-label) {
  color: #dbe4ef !important;
}


:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-card,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-meta-pill,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-modal-progress,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .spec-card,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .spec-form-section {
  background:
      linear-gradient(180deg, rgba(15, 23, 42, 0.78), rgba(15, 23, 42, 0.56)),
      rgba(2, 6, 23, 0.32);
  border-color: rgba(51, 65, 85, 0.92);
  box-shadow: 0 14px 34px rgba(2, 6, 23, 0.28);
}

:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-modal-progress-track {
  background: rgba(30, 41, 59, 0.96);
}

:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-modal-progress-track span {
  background: linear-gradient(90deg, #2563eb, #38bdf8);
}

:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-meta-icon,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .spec-card-icon,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-empty-icon {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.28), rgba(14, 165, 233, 0.18));
  color: #93c5fd;
}

:global(html[data-theme='dark']) .audience-specs-modal-overlay .spec-card-pair-divider {
  background: linear-gradient(180deg, rgba(51, 65, 85, 0.18), rgba(148, 163, 184, 0.45), rgba(51, 65, 85, 0.18));
}

:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-empty {
  background: rgba(15, 23, 42, 0.58);
  border-color: rgba(59, 130, 246, 0.42);
}

:global(html[data-theme='dark']) .audience-specs-modal-overlay .specs-form-banner {
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.28), rgba(14, 165, 233, 0.1));
  border-color: rgba(59, 130, 246, 0.38);
}

:global(html[data-theme='dark']) .audience-specs-modal-overlay .spec-input,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .bool-segment-btn,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .bool-clear-btn,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .bool-btn {
  background: rgba(15, 23, 42, 0.78);
  border-color: rgba(71, 85, 105, 0.95);
  color: #e2e8f0;
}

:global(html[data-theme='dark']) .audience-specs-modal-overlay .spec-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.16);
}

:global(html[data-theme='dark']) .audience-specs-modal-overlay .spec-input::placeholder {
  color: #64748b;
}

:global(html[data-theme='dark']) .audience-specs-modal-overlay .spec-select {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20' fill='none'%3E%3Cpath d='m5 7.5l5 5l5-5' stroke='%2394a3b8' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
}

:global(html[data-theme='dark']) .audience-specs-modal-overlay .bool-segment-btn.active,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .bool-clear-btn.active,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .bool-btn.active,
:global(html[data-theme='dark']) .audience-specs-modal-overlay .bool-btn-muted.active {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.34), rgba(14, 165, 233, 0.18));
  border-color: rgba(96, 165, 250, 0.72);
  color: #bfdbfe;
  box-shadow: 0 10px 22px rgba(37, 99, 235, 0.14);
}

:global(html[data-theme='dark']) .audience-specs-modal-overlay .bool-btn-muted {
  color: #94a3b8;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-card.specs-card-modal),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-modal-content),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-card),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-meta-pill),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-modal-progress) {
  background:
      linear-gradient(180deg, rgba(15, 23, 42, 0.94), rgba(2, 6, 23, 0.9)),
      #020617 !important;
  border-color: rgba(51, 65, 85, 0.96) !important;
  box-shadow:
      0 18px 42px rgba(2, 6, 23, 0.36),
      inset 0 1px 0 rgba(148, 163, 184, 0.08) !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-modal-name),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-modal-heading),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-meta-value),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-card-value),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-modal-progress-head) {
  color: #f8fafc !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-modal-description),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-meta-label),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-card-label) {
  color: #94a3b8 !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-modal-progress-track) {
  background: rgba(30, 41, 59, 0.98) !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-view) {
  background: transparent !important;
  color: #cbd5e1 !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-modal-name) {
  color: #cbd5e1 !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-btn.specs-btn-secondary) {
  background: rgba(30, 41, 59, 0.92) !important;
  border: 1px solid rgba(71, 85, 105, 0.95) !important;
  color: #cbd5e1 !important;
  box-shadow: inset 0 1px 0 rgba(148, 163, 184, 0.08) !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-btn.specs-btn-secondary:hover:not(:disabled)) {
  background: rgba(51, 65, 85, 0.94) !important;
  color: #e2e8f0 !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-form-section) {
  background: rgba(15, 23, 42, 0.72) !important;
  border-color: rgba(51, 65, 85, 0.96) !important;
  box-shadow: inset 0 1px 0 rgba(148, 163, 184, 0.07) !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-form-section-toggle) {
  color: #cbd5e1;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-form-section-toggle:hover) {
  background: rgba(30, 41, 59, 0.72);
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-form-section-icon) {
  background: rgba(37, 99, 235, 0.2);
  color: #93c5fd;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-form-section-chevron) {
  color: #8291a7;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-form-section-copy strong) {
  color: #dbe4ef;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-form-section-copy small) {
  color: #8291a7;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-form-group-os),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .software-presets) {
  border-color: rgba(51, 65, 85, 0.9);
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-os-option) {
  border-color: rgba(71, 85, 105, 0.96);
  background: rgba(2, 6, 23, 0.42);
  color: #aebacd;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-os-option:hover:not(.is-active)) {
  border-color: #64748b;
  background: rgba(30, 41, 59, 0.8);
  color: #e2e8f0;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-os-option.is-active) {
  border-color: rgba(96, 165, 250, 0.72);
  background: rgba(37, 99, 235, 0.22);
  color: #bfdbfe;
  box-shadow: inset 0 0 0 1px rgba(147, 197, 253, 0.06);
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .software-presets-head span) {
  color: #cbd5e1;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .software-presets-head small),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .software-selection-head) {
  color: #8291a7;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .software-preset-btn) {
  border-color: rgba(71, 85, 105, 0.92);
  background: rgba(2, 6, 23, 0.38);
  color: #aebacd;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .software-preset-btn:hover:not(.is-active)) {
  border-color: #64748b;
  color: #e2e8f0;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .software-preset-btn.is-active) {
  border-color: rgba(96, 165, 250, 0.7);
  background: rgba(37, 99, 235, 0.22);
  color: #bfdbfe;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .software-clear-btn) {
  color: #8291a7;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .software-clear-btn:hover) {
  color: #fca5a5;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .software-option) {
  border-color: rgba(51, 65, 85, 0.96);
  background: rgba(2, 6, 23, 0.34);
  color: #aebacd;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .software-option:hover:not(.is-selected)) {
  border-color: #64748b;
  background: rgba(30, 41, 59, 0.7);
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .software-option.is-selected) {
  border-color: rgba(96, 165, 250, 0.62);
  background: rgba(37, 99, 235, 0.18);
  color: #dbeafe;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .software-option-check) {
  border-color: #526176;
  background: rgba(15, 23, 42, 0.96);
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .software-option.is-selected .software-option-check) {
  border-color: #3b82f6;
  background: #2563eb;
  color: #ffffff;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .software-custom-trigger) {
  border-color: #526176;
  color: #aebacd;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .software-custom-trigger:hover) {
  border-color: #60a5fa;
  background: rgba(37, 99, 235, 0.16);
  color: #bfdbfe;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .bool-segment-btn),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .bool-clear-btn) {
  background: rgba(15, 23, 42, 0.88) !important;
  border-color: rgba(71, 85, 105, 0.96) !important;
  color: #cbd5e1 !important;
  box-shadow: inset 0 1px 0 rgba(148, 163, 184, 0.06) !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .bool-segment-btn:hover:not(.active)),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .bool-clear-btn:hover:not(.active)) {
  background: rgba(30, 41, 59, 0.94) !important;
  color: #e2e8f0 !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .bool-segment-btn.active),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .bool-clear-btn.active) {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.36), rgba(14, 165, 233, 0.16)) !important;
  border-color: rgba(96, 165, 250, 0.7) !important;
  color: #bfdbfe !important;
  box-shadow:
      0 10px 22px rgba(37, 99, 235, 0.14),
      inset 0 1px 0 rgba(191, 219, 254, 0.1) !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-card),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-empty),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-form-banner),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-input),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .bool-btn),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .bool-btn-muted) {
  background:
      linear-gradient(180deg, rgba(15, 23, 42, 0.9), rgba(2, 6, 23, 0.72)),
      #020617 !important;
  border-color: rgba(51, 65, 85, 0.96) !important;
  color: #cbd5e1 !important;
  box-shadow: inset 0 1px 0 rgba(148, 163, 184, 0.07) !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-select) {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20' fill='none'%3E%3Cpath d='m5 7.5l5 5l5-5' stroke='%23dbe4ef' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") !important;
  background-repeat: no-repeat !important;
  background-position: right 14px center !important;
  background-size: 16px 16px !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-card-icon),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-meta-icon),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-empty-icon) {
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.42), rgba(14, 165, 233, 0.16)) !important;
  color: #bfdbfe !important;
  box-shadow: inset 0 1px 0 rgba(191, 219, 254, 0.08) !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-title),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-empty-title),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-form-banner-title) {
  color: #e2e8f0 !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-header-subtitle),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-empty-text),
:global(html[data-theme='dark'] .audience-specs-modal-overlay .specs-form-banner-text) {
  color: #94a3b8 !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-card-pair-divider) {
  background: linear-gradient(180deg, rgba(51, 65, 85, 0.12), rgba(148, 163, 184, 0.38), rgba(51, 65, 85, 0.12)) !important;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-card-list-count) {
  background: rgba(37, 99, 235, 0.24);
  color: #bfdbfe;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-card-tag) {
  border-color: rgba(71, 85, 105, 0.92);
  background: rgba(30, 41, 59, 0.78);
  color: #dbe4ef;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-list-items) {
  border-color: rgba(51, 65, 85, 0.96);
  background: rgba(2, 6, 23, 0.42);
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-list-chip) {
  border-color: rgba(59, 130, 246, 0.48);
  background: rgba(30, 64, 175, 0.2);
  color: #dbeafe;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-list-remove) {
  color: #94a3b8;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-list-remove:hover) {
  background: rgba(127, 29, 29, 0.5);
  color: #fca5a5;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-list-empty) {
  border-color: rgba(71, 85, 105, 0.9);
  color: #8291a7;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-list-hint) {
  color: #8291a7;
}

:global(html[data-theme='dark'] .audience-specs-modal-overlay .spec-list-add-btn:disabled) {
  border-color: #334155;
  background: #1e293b;
  color: #64748b;
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

.problem-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.problem-header .form-label {
  margin-bottom: 0;
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

/* ── Компактный список неисправностей ── */
.problem-list {
  --problem-row-height: 42px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.problem-list-scroll {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: calc(var(--problem-row-height) * 2 + 8px);
  padding-right: 4px;
  margin-right: -4px;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-width: thin;
  scrollbar-color: rgba(148, 163, 184, 0.72) transparent;
}

.problem-list-scroll.is-empty {
  max-height: none;
  padding-right: 0;
  margin-right: 0;
  overflow: visible;
}

.problem-list-scroll::-webkit-scrollbar {
  width: 6px;
}

.problem-list-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.problem-list-scroll::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.6);
  border-radius: 999px;
}

.problem-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: var(--problem-row-height);
}

.problem-index {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #dc2626;
  background: #fee2e2;
}

.problem-input {
  flex: 1;
  min-width: 0;
  min-height: 40px;
  padding: 9px 12px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 14px;
  font-family: inherit;
  box-sizing: border-box;
  transition: all 0.2s ease;
}

.problem-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.problem-input:disabled {
  background: #f8fafc;
  color: #475569;
}

.problem-remove {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 9px;
  cursor: pointer;
  color: #b91c1c;
  background: rgba(254, 226, 226, 0.7);
  transition: all 0.2s ease;
}

.problem-remove:hover {
  background: rgba(252, 165, 165, 0.9);
}

.problem-remove svg {
  width: 15px;
  height: 15px;
}

.problem-empty {
  padding: 10px 12px;
  border: 1px dashed #e2e8f0;
  border-radius: 10px;
  font-size: 13px;
  color: #94a3b8;
}

.problem-add {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  padding: 0;
  border: 1px solid rgba(59, 130, 246, 0.38);
  border-radius: 10px;
  color: #2563eb;
  background:
      linear-gradient(135deg, rgba(255, 255, 255, 0.8), transparent 58%),
      rgba(219, 234, 254, 0.55);
  box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.86),
      0 6px 16px rgba(37, 99, 235, 0.08);
  cursor: pointer;
  transition:
      background 0.2s ease,
      border-color 0.2s ease,
      color 0.2s ease,
      box-shadow 0.2s ease;
}

.problem-add:hover:not(:disabled) {
  border-color: rgba(37, 99, 235, 0.62);
  color: #1d4ed8;
  background:
      linear-gradient(135deg, rgba(255, 255, 255, 0.9), transparent 58%),
      rgba(191, 219, 254, 0.82);
  box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.92),
      0 8px 18px rgba(37, 99, 235, 0.12);
}

.problem-add:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.problem-add svg {
  width: 16px;
  height: 16px;
}

:global(html[data-theme='dark']) .problem-input {
  background:
      linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(2, 6, 23, 0.74)),
      #020617;
  border-color: rgba(51, 65, 85, 0.96);
  color: #dbe4ef;
  box-shadow: inset 0 1px 0 rgba(148, 163, 184, 0.08);
}

:global(html[data-theme='dark']) .problem-list-scroll {
  scrollbar-color: rgba(96, 165, 250, 0.52) transparent;
}

:global(html[data-theme='dark']) .problem-list-scroll::-webkit-scrollbar-thumb {
  background: rgba(96, 165, 250, 0.46);
}

:global(html[data-theme='dark']) .problem-input::placeholder {
  color: #64748b;
}

:global(html[data-theme='dark']) .problem-input:focus {
  border-color: rgba(96, 165, 250, 0.9);
  box-shadow:
      0 0 0 3px rgba(59, 130, 246, 0.16),
      inset 0 1px 0 rgba(148, 163, 184, 0.08);
}

:global(html[data-theme='dark']) .problem-input:disabled {
  background: rgba(15, 23, 42, 0.68);
  color: #94a3b8;
}

:global(html[data-theme='dark']) .problem-index {
  background: rgba(127, 29, 29, 0.4);
  color: #fca5a5;
}

:global(html[data-theme='dark']) .problem-empty {
  border-color: rgba(51, 65, 85, 0.96);
  color: #94a3b8;
  background: rgba(15, 23, 42, 0.46);
}

:global(html[data-theme='dark']) .problem-add {
  border-color: rgba(96, 165, 250, 0.4);
  color: #93c5fd;
  background:
      linear-gradient(135deg, rgba(30, 41, 59, 0.78), transparent 58%),
      rgba(37, 99, 235, 0.18);
  box-shadow:
      inset 0 1px 0 rgba(191, 219, 254, 0.08),
      0 8px 20px rgba(2, 6, 23, 0.18);
}

:global(html[data-theme='dark']) .problem-add:hover:not(:disabled) {
  background:
      linear-gradient(135deg, rgba(30, 41, 59, 0.92), transparent 58%),
      rgba(37, 99, 235, 0.3);
  border-color: rgba(147, 197, 253, 0.58);
  color: #bfdbfe;
  box-shadow:
      inset 0 1px 0 rgba(191, 219, 254, 0.12),
      0 10px 22px rgba(2, 6, 23, 0.24);
}

:global(html[data-theme='dark']) .problem-remove {
  background: rgba(127, 29, 29, 0.35);
  color: #fca5a5;
}

:global(html[data-theme='dark']) .problem-remove:hover {
  background: rgba(153, 27, 27, 0.54);
  color: #fecaca;
}

.unsaved-problems-overlay {
  position: fixed;
  inset: 0;
  top: var(--audience-modal-top, 0px);
  width: 100vw;
  height: 100vh;
  height: 100dvh;
  height: var(--audience-modal-vh, 100dvh);
  z-index: 2600;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 14px;
  overflow-y: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  background:
      radial-gradient(circle at 50% 20%, rgba(59, 130, 246, 0.18), transparent 36%),
      rgba(15, 23, 42, 0.52);
  backdrop-filter: blur(8px);
  animation: fadeIn 0.18s ease;
}

.unsaved-problems-dialog {
  width: min(100%, 440px);
  max-height: calc(100vh - 28px);
  max-height: calc(100dvh - 28px);
  max-height: calc(var(--audience-modal-vh, 100dvh) - 28px);
  margin: auto;
  overflow-y: auto;
  box-sizing: border-box;
  padding: 16px;
  border-radius: 20px;
  border: 1px solid rgba(191, 219, 254, 0.9);
  background:
      radial-gradient(circle at top left, rgba(219, 234, 254, 0.92), transparent 34%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.96));
  box-shadow:
      0 28px 70px rgba(15, 23, 42, 0.28),
      inset 0 1px 0 rgba(255, 255, 255, 0.92);
  animation: scaleIn 0.2s ease;
}

.unsaved-problems-icon {
  width: 40px;
  height: 40px;
  margin-bottom: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  color: #2563eb;
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.94), rgba(191, 219, 254, 0.72));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.92);
}

.unsaved-problems-icon svg {
  width: 22px;
  height: 22px;
}

.unsaved-problems-copy {
  min-width: 0;
}

.unsaved-problems-kicker {
  display: inline-flex;
  margin-bottom: 5px;
  color: #2563eb;
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.09em;
}

.unsaved-problems-copy h3 {
  margin: 0;
  color: #0f172a;
  font-size: 20px;
  line-height: 1.14;
  font-weight: 850;
}

.unsaved-problems-copy p {
  margin: 8px 0 0;
  color: #475569;
  font-size: 13px;
  line-height: 1.45;
}

.unsaved-problems-note {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 12px;
  padding: 9px 11px;
  border-radius: 13px;
  border: 1px solid rgba(252, 165, 165, 0.72);
  background: linear-gradient(135deg, rgba(254, 242, 242, 0.9), rgba(255, 247, 237, 0.78));
  color: #64748b;
  font-size: 12px;
  line-height: 1.35;
}

.unsaved-problems-note strong {
  flex-shrink: 0;
  color: #dc2626;
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.unsaved-problems-actions {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 7px;
  margin-top: 13px;
}

.unsaved-problems-btn {
  min-height: 34px;
  padding: 7px 10px;
  border-radius: 11px;
  border: 1px solid rgba(203, 213, 225, 0.9);
  background: rgba(255, 255, 255, 0.86);
  color: #334155;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}

.unsaved-problems-btn:hover:not(:disabled) {
  background: #f8fafc;
  border-color: #94a3b8;
}

.unsaved-problems-btn.is-muted {
  color: #64748b;
}

.unsaved-problems-btn.is-primary {
  border-color: rgba(239, 68, 68, 0.72);
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: #fff;
  box-shadow: 0 8px 18px rgba(220, 38, 38, 0.16);
}

.unsaved-problems-btn.is-primary:hover:not(:disabled) {
  border-color: rgba(220, 38, 38, 0.86);
  background: linear-gradient(135deg, #f05252, #b91c1c);
}

.unsaved-problems-btn:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

:global(html[data-theme='dark'] .audience-unsaved-problems-overlay) {
  background:
      radial-gradient(circle at 50% 18%, rgba(37, 99, 235, 0.18), transparent 38%),
      rgba(2, 6, 23, 0.74) !important;
}

:global(html[data-theme='dark'] .audience-unsaved-problems-overlay .unsaved-problems-dialog) {
  background:
      radial-gradient(circle at top left, rgba(37, 99, 235, 0.18), transparent 36%),
      linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(2, 6, 23, 0.96)) !important;
  border-color: rgba(71, 85, 105, 0.95) !important;
  box-shadow:
      0 30px 76px rgba(2, 6, 23, 0.62),
      inset 0 1px 0 rgba(148, 163, 184, 0.08) !important;
}

:global(html[data-theme='dark'] .audience-unsaved-problems-overlay .unsaved-problems-icon) {
  color: #bfdbfe !important;
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.42), rgba(14, 165, 233, 0.16)) !important;
  box-shadow: inset 0 1px 0 rgba(191, 219, 254, 0.08) !important;
}

:global(html[data-theme='dark'] .audience-unsaved-problems-overlay .unsaved-problems-kicker) {
  color: #93c5fd !important;
}

:global(html[data-theme='dark'] .audience-unsaved-problems-overlay .unsaved-problems-copy h3) {
  color: #f8fafc !important;
}

:global(html[data-theme='dark'] .audience-unsaved-problems-overlay .unsaved-problems-copy p) {
  color: #cbd5e1 !important;
}

:global(html[data-theme='dark'] .audience-unsaved-problems-overlay .unsaved-problems-note) {
  background: linear-gradient(135deg, rgba(127, 29, 29, 0.32), rgba(124, 45, 18, 0.18)) !important;
  border-color: rgba(248, 113, 113, 0.38) !important;
  color: #cbd5e1 !important;
}

:global(html[data-theme='dark'] .audience-unsaved-problems-overlay .unsaved-problems-note strong) {
  color: #fca5a5 !important;
}

:global(html[data-theme='dark'] .audience-unsaved-problems-overlay .unsaved-problems-btn) {
  background: rgba(30, 41, 59, 0.92) !important;
  border-color: rgba(71, 85, 105, 0.95) !important;
  color: #dbe4ef !important;
}

:global(html[data-theme='dark'] .audience-unsaved-problems-overlay .unsaved-problems-btn:hover:not(:disabled)) {
  background: rgba(51, 65, 85, 0.94) !important;
  border-color: rgba(100, 116, 139, 0.95) !important;
}

:global(html[data-theme='dark'] .audience-unsaved-problems-overlay .unsaved-problems-btn.is-muted) {
  color: #94a3b8 !important;
}

:global(html[data-theme='dark'] .audience-unsaved-problems-overlay .unsaved-problems-btn.is-primary) {
  background: linear-gradient(135deg, #ef4444, #b91c1c) !important;
  border-color: rgba(248, 113, 113, 0.68) !important;
  color: #fff !important;
  box-shadow: 0 14px 28px rgba(127, 29, 29, 0.32) !important;
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
  background:
      linear-gradient(135deg, rgba(255, 255, 255, 0.12), transparent 44%),
      linear-gradient(135deg, #10b981, #059669);
  color: white;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.18) inset;
}

.fix-btn:hover:not(:disabled) {
  transform: none;
  background:
      linear-gradient(135deg, rgba(255, 255, 255, 0.18), transparent 44%),
      linear-gradient(135deg, #12a874, #047857);
  box-shadow:
      0 0 0 1px rgba(16, 185, 129, 0.18) inset,
      0 8px 18px rgba(5, 150, 105, 0.16);
}

.break-btn {
  background:
      linear-gradient(135deg, rgba(255, 255, 255, 0.12), transparent 44%),
      linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.18) inset;
}

.break-btn:hover:not(:disabled) {
  transform: none;
  background:
      linear-gradient(135deg, rgba(255, 255, 255, 0.18), transparent 44%),
      linear-gradient(135deg, #e33d3d, #b91c1c);
  box-shadow:
      0 0 0 1px rgba(239, 68, 68, 0.18) inset,
      0 8px 18px rgba(220, 38, 38, 0.15);
}

.action-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
  opacity: 0.5;
}

.status-action-zone {
  min-height: 48px;
  align-items: stretch;
}

.status-action-zone > .status-inline-confirm {
  grid-column: 1 / -1;
}

.status-inline-confirm {
  --status-accent: #2563eb;
  --status-action: #1d4ed8;
  --status-action-hover: #1e40af;
  --status-fill-start: #60a5fa;
  --status-fill-end: #2563eb;
  --sc-bg: #f7f9fb;
  --sc-border: #d8e0e8;
  --sc-text: #1b2533;
  --sc-muted: #697789;
  --sc-mark-inner: #eef4fb;
  --sc-btn-bg: #ffffff;
  --sc-btn-hover: #f1f4f7;
  --sc-btn-text: #405064;
  --sc-btn-border: #d4dde6;
  --sc-track: #e1e7ed;
  --sc-countdown-bg: #edf2f6;
  --sc-countdown-border: #d2dce5;

  position: relative;
  isolation: isolate;
  flex: 1 1 100%;
  width: 100%;
  min-width: 0;
  max-width: 100%;
  min-height: 56px;
  box-sizing: border-box;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 8px;
  padding: 7px 7px 14px;
  border-radius: 16px;
  overflow: hidden;
  background: var(--sc-bg);
  border: 1px solid var(--sc-border);
  box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.82),
      0 8px 22px rgba(15, 23, 42, 0.07);
  transition: box-shadow 0.25s ease, border-color 0.25s ease, background 0.25s ease;
  animation: scConfirmEnter 0.24s cubic-bezier(0.2, 0.75, 0.25, 1) both;
}

.status-inline-confirm::before {
  content: "";
  position: absolute;
  left: 8px;
  right: 8px;
  bottom: 6px;
  height: 5px;
  z-index: 0;
  border-radius: 999px;
  background: var(--sc-track);
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.1);
  pointer-events: none;
}

.status-inline-confirm::after {
  display: none;
}

.status-inline-confirm.is-working {
  --status-accent: #0d9669;
  --status-action: #087b58;
  --status-action-hover: #066a4b;
  --status-fill-start: #40cc99;
  --status-fill-end: #0d9669;
  --sc-mark-inner: #eaf7f2;
  --sc-countdown-bg: #eaf6f1;
  --sc-countdown-border: #bcded1;
  --sc-track: #dbe9e4;
}

.status-inline-confirm.is-broken {
  --status-accent: #d94850;
  --status-action: #c43640;
  --status-action-hover: #aa2d36;
  --status-fill-start: #fb7b81;
  --status-fill-end: #d94850;
  --sc-mark-inner: #fff0f1;
  --sc-countdown-bg: #fceff0;
  --sc-countdown-border: #efc5c8;
  --sc-track: #eee0e1;
}

.status-inline-confirm.is-urgent {
  border-color: color-mix(in srgb, var(--status-accent), var(--sc-border) 66%);
  box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.82),
      0 0 0 3px color-mix(in srgb, var(--status-accent), transparent 90%),
      0 10px 24px color-mix(in srgb, var(--status-accent), transparent 91%);
}

@keyframes scConfirmEnter {
  from {
    opacity: 0;
    transform: translateY(3px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.status-inline-progress {
  position: absolute;
  left: 8px;
  right: 8px;
  bottom: 6px;
  height: 5px;
  border-radius: 999px;
  transform-origin: left center;
  transform: scaleX(1);
  animation: scCountdown var(--sc-duration, 5000ms) linear forwards;
  background: linear-gradient(90deg, var(--status-fill-start), var(--status-fill-end));
  box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.42),
      0 2px 8px color-mix(in srgb, var(--status-accent), transparent 76%);
  z-index: 1;
  overflow: visible;
  will-change: transform;
}

@keyframes scCountdown {
  from { transform: scaleX(1); }
  to   { transform: scaleX(0); }
}

.status-inline-progress::before {
  content: '';
  position: absolute;
  top: 1px;
  right: 1px;
  left: 1px;
  height: 1px;
  border-radius: inherit;
  background: rgba(255, 255, 255, 0.46);
  opacity: 0.7;
}

.status-inline-progress::after {
  content: '';
  position: absolute;
  top: -1px;
  right: -1px;
  bottom: -1px;
  width: 2px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--status-fill-start), white 24%);
  box-shadow:
      0 0 5px color-mix(in srgb, var(--status-accent), transparent 42%),
      -3px 0 8px color-mix(in srgb, var(--status-accent), transparent 72%);
}

.status-inline-mark,
.status-inline-copy,
.status-inline-btn {
  position: relative;
  z-index: 2;
}

.status-inline-mark {
  width: 36px;
  height: 36px;
  border: 1px solid color-mix(in srgb, var(--status-accent), transparent 70%);
  border-radius: 12px;
  display: inline-grid;
  place-items: center;
  color: var(--status-accent);
  background: var(--sc-mark-inner);
  box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.64),
      0 5px 12px color-mix(in srgb, var(--status-accent), transparent 90%);
}

.status-inline-mark svg {
  width: 17px;
  height: 17px;
}

.status-inline-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 1px;
}

.status-inline-kicker {
  color: var(--sc-muted);
  font-size: 9px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.11em;
  text-transform: uppercase;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-inline-label {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--sc-text);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.18;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-inline-label > span:first-child {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-inline-countdown {
  flex-shrink: 0;
  min-width: 47px;
  min-height: 25px;
  padding: 2px 7px;
  border: 1px solid var(--sc-countdown-border);
  border-radius: 999px;
  display: inline-flex;
  align-items: baseline;
  justify-content: center;
  gap: 2px;
  color: var(--status-accent);
  background: var(--sc-countdown-bg);
  box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.56),
      0 3px 9px color-mix(in srgb, var(--status-accent), transparent 92%);
  font-variant-numeric: tabular-nums;
}

.status-inline-countdown > span {
  color: color-mix(in srgb, var(--status-accent), var(--sc-muted) 48%);
  font-size: 8px;
  line-height: 1;
  letter-spacing: 0.02em;
}

.status-inline-confirm.is-urgent .status-inline-countdown {
  border-color: color-mix(in srgb, var(--status-accent), transparent 52%);
  background: color-mix(in srgb, var(--status-accent), var(--sc-bg) 86%);
  box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.48),
      0 0 0 2px color-mix(in srgb, var(--status-accent), transparent 90%);
}

/* Цифра обратного отсчёта */
.status-inline-label strong {
  font-size: 15px;
  font-weight: 800;
  color: var(--status-accent);
  font-variant-numeric: tabular-nums;
}

/* Кнопки */
.status-inline-btn {
  min-height: 34px;
  padding: 0 13px;
  border-radius: 12px;
  border: 1px solid var(--sc-btn-border);
  background: var(--sc-btn-bg);
  color: var(--sc-btn-text);
  font-size: 12.5px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
}

.status-inline-btn:hover:not(:disabled) {
  background: var(--sc-btn-hover);
  border-color: color-mix(in srgb, var(--status-accent), var(--sc-btn-border) 72%);
  box-shadow:
      inset 0 0 0 1px rgba(148, 163, 184, 0.1),
      0 5px 12px rgba(15, 23, 42, 0.07);
  transform: translateY(-1px);
}

.status-inline-btn:focus-visible {
  outline: none;
  border-color: color-mix(in srgb, var(--status-accent), var(--sc-btn-border) 48%);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--status-accent), transparent 82%);
}

.status-inline-btn:active:not(:disabled) {
  transform: translateY(0) scale(0.985);
}

.status-inline-btn.is-primary {
  color: white;
  border-color: color-mix(in srgb, var(--status-action), black 8%);
  background: var(--status-action);
  box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.2),
      0 6px 14px color-mix(in srgb, var(--status-action), transparent 78%);
}

.status-inline-btn.is-primary:hover:not(:disabled) {
  border-color: var(--status-action-hover);
  background: var(--status-action-hover);
  box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.18),
      0 7px 16px color-mix(in srgb, var(--status-action), transparent 72%);
}

.status-inline-btn.is-primary:focus-visible {
  box-shadow:
      0 0 0 3px color-mix(in srgb, var(--status-accent), transparent 76%),
      0 6px 14px color-mix(in srgb, var(--status-action), transparent 78%),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.status-inline-btn:disabled {
  cursor: wait;
  opacity: 0.68;
}

/* Тёмная тема */
:global(html[data-theme='dark'] .status-inline-confirm) {
  --sc-bg: #111921;
  --sc-border: #2b3945;
  --sc-text: #dde6eb;
  --sc-muted: #91a0aa;
  --sc-mark-inner: #17222b;
  --sc-btn-bg: #19242e;
  --sc-btn-hover: #202d38;
  --sc-btn-text: #c5d0d7;
  --sc-btn-border: #344550;
  --sc-track: #26343e;
  --sc-countdown-bg: #17232c;
  --sc-countdown-border: #344650;
  box-shadow:
      inset 0 1px 0 rgba(148, 163, 184, 0.08),
      0 10px 24px rgba(2, 6, 23, 0.3);
}

:global(html[data-theme='dark'] .status-inline-confirm.is-working) {
  --status-accent: #4fd5a5;
  --status-action: #147e5d;
  --status-action-hover: #106a4f;
  --status-fill-start: #63dfb2;
  --status-fill-end: #28b986;
  --sc-mark-inner: #132820;
  --sc-countdown-bg: #14261f;
  --sc-countdown-border: #295343;
  --sc-track: #213a31;
}

:global(html[data-theme='dark'] .status-inline-confirm.is-broken) {
  --status-accent: #ff858b;
  --status-action: #b83d47;
  --status-action-hover: #9d333c;
  --status-fill-start: #ff969b;
  --status-fill-end: #e85e67;
  --sc-mark-inner: #301a1e;
  --sc-countdown-bg: #2b191d;
  --sc-countdown-border: #633239;
  --sc-track: #43262b;
}

@media (max-width: 520px) {
  .status-action-zone {
    min-height: 36px;
  }

  .status-action-zone:has(.status-inline-confirm) {
    min-height: 108px;
  }

  .status-inline-confirm {
    grid-column: 1 / -1;
    grid-template-columns: minmax(78px, 0.82fr) minmax(0, 1.18fr);
    grid-template-areas:
        "copy copy"
        "cancel confirm";
    align-items: center;
    gap: 8px;
    padding: 8px 8px 14px;
    min-height: 104px;
    border-radius: 18px;
    background: var(--sc-bg);
  }

  .status-inline-confirm::before {
    bottom: 7px;
    height: 4px;
  }

  .status-inline-mark {
    position: absolute;
    left: 10px;
    top: 10px;
    width: 31px;
    height: 31px;
    border-radius: 12px;
  }

  .status-inline-copy {
    grid-area: copy;
    min-height: 32px;
    padding: 1px 4px 0 44px;
    align-self: center;
    align-items: flex-start;
    justify-content: center;
    gap: 3px;
  }

  .status-inline-kicker {
    font-size: 8px;
    letter-spacing: 0.12em;
  }

  .status-inline-label {
    font-size: 12.5px;
    line-height: 1.15;
    white-space: normal;
    overflow: visible;
    text-align: left;
    text-overflow: clip;
  }

  .status-inline-label strong {
    font-size: 14px;
  }

  .status-inline-countdown {
    min-width: 44px;
    min-height: 23px;
    padding: 1px 6px;
  }

  .status-inline-btn {
    min-height: 33px;
    padding: 0 10px;
    border-radius: 12px;
    font-size: 12px;
    width: 100%;
    box-shadow: none;
  }

  .status-inline-btn:not(.is-primary) {
    grid-area: cancel;
    justify-self: stretch;
  }

  .status-inline-btn.is-primary {
    grid-area: confirm;
    justify-self: stretch;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.16),
        0 5px 12px color-mix(in srgb, var(--status-action), transparent 76%);
  }

  .status-inline-progress {
    left: 8px;
    right: 8px;
    bottom: 7px;
    height: 4px;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--status-fill-start), var(--status-fill-end));
    box-shadow:
        0 0 0 1px color-mix(in srgb, var(--status-accent), transparent 78%),
        0 4px 12px color-mix(in srgb, var(--status-accent), transparent 72%);
  }

  .status-inline-progress::after {
    top: 0;
    right: 0;
    bottom: 0;
    width: 2px;
  }

}

@media (prefers-reduced-motion: reduce) {
  .status-inline-confirm {
    animation: none !important;
  }

  .status-inline-confirm,
  .status-inline-progress,
  .status-inline-btn {
    transition: none !important;
  }
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
  /* margin-top: 15px; */
  padding-top: 10px;
  min-height: 100px;
}

.hw-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 3px;
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
  inset: 0;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  height: 100dvh;
  height: var(--audience-modal-vh, 100dvh);
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(2px);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  overflow-y: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  animation: fadeIn 0.2s ease;
}

.audience-file-confirm-overlay {
  z-index: 2300;
}

/* Само окно */
.hw-confirm-box {
  background: white;
  padding: 24px;
  border-radius: 12px;
  width: 320px;
  max-width: 100%;
  max-height: calc(100vh - 32px);
  max-height: calc(100dvh - 32px);
  max-height: calc(var(--audience-modal-vh, 100dvh) - 32px);
  margin: auto;
  overflow-y: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
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
:global(html[data-theme='dark'] .audience-file-confirm-overlay) {
  background: rgba(2, 6, 23, 0.72) !important;
}

:global(html[data-theme='dark'] .audience-file-confirm-overlay .hw-confirm-box) {
  background:
      radial-gradient(circle at top right, rgba(239, 68, 68, 0.14), transparent 34%),
      linear-gradient(180deg, rgba(17, 24, 39, 0.98), rgba(15, 23, 42, 0.98)) !important;
  border: 1px solid rgba(71, 85, 105, 0.9) !important;
  color: #e2e8f0 !important;
  box-shadow: 0 28px 70px rgba(2, 6, 23, 0.56) !important;
}

:global(html[data-theme='dark'] .audience-file-confirm-overlay .hw-confirm-title) {
  color: #f8fafc !important;
}

:global(html[data-theme='dark'] .audience-file-confirm-overlay .hw-confirm-text),
:global(html[data-theme='dark'] .audience-file-confirm-overlay .hw-confirm-checkbox) {
  color: #cbd5e1 !important;
}

:global(html[data-theme='dark'] .audience-file-confirm-overlay .hw-btn-cancel) {
  background: rgba(30, 41, 59, 0.95) !important;
  border: 1px solid #475569 !important;
  color: #e2e8f0 !important;
}

:global(html[data-theme='dark'] .audience-file-confirm-overlay .hw-btn-cancel:hover) {
  background: rgba(51, 65, 85, 0.98) !important;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scaleIn {
  from { transform: scale(0.9); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

/* Конец стилей модалки подтверждения удаления файла */

/* Equipment modal: calm material, grouped hierarchy and direct feedback. */
.audience-equipment-modal {
  background: rgba(15, 23, 42, 0.34);
  backdrop-filter: blur(12px) saturate(1.08);
}

.equipment-modal-content {
  --eq-bg: rgba(250, 250, 252, 0.9);
  --eq-surface: #f2f2f7;
  --eq-surface-raised: #ffffff;
  --eq-input: #ffffff;
  --eq-border: rgba(60, 60, 67, 0.14);
  --eq-border-strong: rgba(60, 60, 67, 0.22);
  --eq-separator: rgba(60, 60, 67, 0.13);
  --eq-text: #1d1d1f;
  --eq-secondary: #6e6e73;
  --eq-tertiary: #8e8e93;
  --eq-blue: #007aff;
  --eq-blue-soft: rgba(0, 122, 255, 0.1);
  --eq-green: #248a3d;
  --eq-green-soft: rgba(36, 138, 61, 0.11);
  --eq-red: #d70015;
  --eq-red-soft: rgba(215, 0, 21, 0.1);

  width: min(100%, 600px);
  max-width: 600px;
  padding: 24px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--eq-border-strong) transparent;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 28px;
  color: var(--eq-text);
  background: var(--eq-bg);
  box-shadow:
      0 32px 90px rgba(15, 23, 42, 0.3),
      0 8px 28px rgba(15, 23, 42, 0.12),
      inset 0 1px 0 rgba(255, 255, 255, 0.84);
  backdrop-filter: blur(32px) saturate(1.35);
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
  font-optical-sizing: auto;
  animation: none;
  transform-origin: center 42%;
}

.equipment-modal-content::-webkit-scrollbar {
  width: 7px;
}

.equipment-modal-content::-webkit-scrollbar-thumb {
  border: 2px solid transparent;
  border-radius: 999px;
  background: var(--eq-border-strong);
  background-clip: padding-box;
}

:global(html[data-theme='dark'] .audience-equipment-modal) {
  background: rgba(0, 0, 0, 0.62);
}

:global(html[data-theme='dark'] .equipment-modal-content) {
  --eq-bg: rgba(17, 24, 39, 0.94);
  --eq-surface: #1e293b;
  --eq-surface-raised: #243247;
  --eq-input: #0f172a;
  --eq-border: rgba(148, 163, 184, 0.2);
  --eq-border-strong: rgba(148, 163, 184, 0.34);
  --eq-separator: rgba(148, 163, 184, 0.16);
  --eq-text: #e2e8f0;
  --eq-secondary: #a8b5c7;
  --eq-tertiary: #7f8da3;
  --eq-blue: #0a84ff;
  --eq-blue-soft: rgba(10, 132, 255, 0.16);
  --eq-green: #30d158;
  --eq-green-soft: rgba(48, 209, 88, 0.14);
  --eq-red: #ff453a;
  --eq-red-soft: rgba(255, 69, 58, 0.14);
  border-color: rgba(255, 255, 255, 0.12);
  box-shadow:
      0 36px 100px rgba(0, 0, 0, 0.62),
      0 10px 34px rgba(0, 0, 0, 0.34),
      inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.equipment-modal-heading {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  margin-bottom: 16px;
  padding-right: 48px;
}

.equipment-modal-heading-copy {
  min-width: 0;
}

.equipment-modal-kicker {
  display: block;
  margin-bottom: 3px;
  color: var(--eq-tertiary);
  font-size: 11px;
  font-weight: 600;
  line-height: 1.2;
  letter-spacing: 0.045em;
}

.equipment-modal-content .modal-title {
  margin: 0;
  padding-right: 0;
  gap: 3px;
  color: var(--eq-text);
  font-size: 25px;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.018em;
}

.equipment-modal-content .modal-subtitle {
  color: var(--eq-secondary);
  font-size: 13px;
  font-weight: 500;
  line-height: 1.3;
  letter-spacing: 0;
}

.equipment-modal-heading .status-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  width: auto;
  margin: 0;
  padding: 7px 10px;
  border: 1px solid transparent;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
}

.equipment-modal-heading .status-badge::before {
  content: '';
  width: 7px;
  height: 7px;
  flex: 0 0 7px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 0 3px color-mix(in srgb, currentColor, transparent 84%);
}

.equipment-modal-heading .status-badge.working {
  color: var(--eq-green);
  border-color: color-mix(in srgb, var(--eq-green), transparent 72%);
  background: var(--eq-green-soft);
}

.equipment-modal-heading .status-badge.broken {
  color: var(--eq-red);
  border-color: color-mix(in srgb, var(--eq-red), transparent 72%);
  background: var(--eq-red-soft);
}

.equipment-modal .modal-close-upper {
  top: 18px;
  right: 18px;
}

.equipment-modal-content .modal-close-upper button {
  width: 38px;
  height: 38px;
  margin: 0;
  color: var(--eq-secondary);
  border: 1px solid var(--eq-border);
  border-radius: 50%;
  background: var(--eq-surface);
  box-shadow: none;
  transition: color 160ms ease, background 160ms ease, transform 100ms ease;
}

.equipment-modal-content .modal-close-upper button svg {
  width: 17px;
  height: 17px;
  stroke: currentColor;
}

.equipment-modal-content .modal-close-upper button:hover {
  color: var(--eq-text);
  background: var(--eq-surface-raised);
  transform: none;
}

.equipment-modal-content .modal-close-upper button:active {
  transform: scale(0.92);
}

.equipment-modal-content .modal-close-upper button:focus-visible,
.equipment-modal-content button:focus-visible,
.equipment-modal-content [role='button']:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--eq-blue), transparent 64%);
  outline-offset: 2px;
}

.equipment-modal-content .modal-equipment-info {
  gap: 15px;
  margin-bottom: 0;
  padding: 16px;
  border: 1px solid var(--eq-border);
  border-radius: 20px;
  background: var(--eq-surface);
  box-shadow: none;
}

.equipment-modal-content .modal-equipment-icon {
  width: 56px;
  height: 56px;
  flex: 0 0 56px;
  border-radius: 17px;
  box-shadow:
      0 8px 18px color-mix(in srgb, var(--eq-blue), transparent 82%),
      inset 0 1px 0 rgba(255, 255, 255, 0.22);
}

.equipment-modal-content .modal-equipment-icon :deep(svg) {
  width: 29px;
  height: 29px;
}

.equipment-modal-content .modal-equipment-details {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
}

.equipment-modal-content .modal-equipment-details > div {
  min-height: 28px;
}

.equipment-modal-content .modal-equipment-details h3 {
  margin: 0;
  color: var(--eq-text);
  font-size: 17px;
  font-weight: 650;
  line-height: 1.28;
  letter-spacing: -0.01em;
}

.equipment-modal-content .modal-equipment-details p {
  margin: 0;
  color: var(--eq-secondary);
  font-size: 13px;
  line-height: 1.35;
}

.modal-inline-icon-button {
  appearance: none;
  width: 28px;
  height: 28px;
  flex: 0 0 28px;
  display: inline-grid;
  place-items: center;
  margin-left: 4px;
  padding: 0;
  color: var(--eq-tertiary);
  border: 0;
  border-radius: 9px;
  background: transparent;
  cursor: pointer;
  transition: color 160ms ease, background 160ms ease, transform 100ms ease;
}

.equipment-modal-content .modal-inline-icon-button svg {
  width: 16px;
  height: 16px;
  margin: 0;
  opacity: 1;
}

.modal-inline-icon-button:hover {
  color: var(--eq-blue);
  background: var(--eq-blue-soft);
}

.modal-inline-icon-button:active {
  transform: scale(0.9);
}

.modal-inline-icon-button.is-save {
  color: var(--eq-green);
  background: var(--eq-green-soft);
}

.equipment-modal-content .modal-equipment-inline-edit {
  gap: 5px;
}

.equipment-modal-content .modal-equipment-inline-input,
.equipment-modal-content .modal-equipment-details div input {
  min-height: 32px;
  padding: 5px 9px;
  color: var(--eq-text);
  border: 1px solid var(--eq-border-strong);
  border-radius: 10px;
  background: var(--eq-input);
  box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.04);
  transition: border-color 160ms ease, box-shadow 160ms ease, background 160ms ease;
}

.equipment-modal-content .modal-equipment-inline-input:focus {
  outline: none;
  border-color: var(--eq-blue);
  box-shadow: 0 0 0 3px var(--eq-blue-soft);
}

.equipment-modal-content .specs-entry-group {
  width: 170px;
  gap: 7px;
}

.equipment-modal-content .specs-entry-chip {
  padding: 5px 9px;
  border-color: var(--eq-border);
  background: var(--eq-surface-raised);
  box-shadow: none;
}

.equipment-modal-content .specs-entry-chip-text {
  color: var(--eq-secondary);
  font-size: 11px;
}

.equipment-modal-content .specs-entry-chip.is-partial {
  border-color: color-mix(in srgb, var(--eq-blue), transparent 72%);
  background: var(--eq-blue-soft);
}

.equipment-modal-content .specs-entry-chip.is-complete {
  border-color: color-mix(in srgb, var(--eq-green), transparent 70%);
  background: var(--eq-green-soft);
}

.equipment-modal-content .specs-entry-chip.is-empty {
  border-color: var(--eq-border);
  background: var(--eq-surface-raised);
}

.equipment-modal-content .specs-entry-btn {
  min-height: 38px;
  padding: 7px 11px;
  color: var(--eq-blue);
  border: 1px solid var(--eq-border);
  border-radius: 11px;
  background: var(--eq-surface-raised);
  box-shadow: none;
  transition: color 160ms ease, background 160ms ease, border-color 160ms ease, transform 100ms ease;
}

.equipment-modal-content .specs-entry-btn:hover {
  color: var(--eq-blue);
  border-color: color-mix(in srgb, var(--eq-blue), transparent 68%);
  background: color-mix(in srgb, var(--eq-blue-soft), var(--eq-surface-raised) 54%);
  box-shadow: none;
  transform: none;
}

.equipment-modal-content .specs-entry-btn:active {
  transform: scale(0.97);
}

.equipment-modal-content .equipment-modal-section {
  margin: 0;
  padding: 16px 0;
}

.equipment-modal-content .form-label,
.equipment-modal-content .hw-section-title {
  margin: 0;
  color: var(--eq-secondary);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.3;
  letter-spacing: 0;
  text-transform: none;
  text-shadow: none;
}

.equipment-modal-content .problem-header {
  margin-bottom: 9px;
}

.equipment-modal-content .problem-list {
  --problem-row-height: 40px;
}

.equipment-modal-content .problem-list-scroll {
  gap: 7px;
  scrollbar-color: var(--eq-border-strong) transparent;
}

.equipment-modal-content .problem-row {
  gap: 7px;
}

.equipment-modal-content .problem-index {
  width: 24px;
  height: 24px;
  color: var(--eq-red);
  border-radius: 8px;
  background: var(--eq-red-soft);
}

.equipment-modal-content .problem-input {
  min-height: 40px;
  padding: 8px 11px;
  color: var(--eq-text);
  border: 1px solid var(--eq-border-strong);
  border-radius: 11px;
  background: var(--eq-input);
  box-shadow: none;
  transition: border-color 160ms ease, box-shadow 160ms ease, background 160ms ease;
}

.equipment-modal-content .problem-input::placeholder {
  color: var(--eq-tertiary);
}

.equipment-modal-content .problem-input:focus {
  outline: none;
  border-color: var(--eq-blue);
  box-shadow: 0 0 0 3px var(--eq-blue-soft);
}

.equipment-modal-content .problem-input:disabled {
  color: var(--eq-secondary);
  background: var(--eq-surface);
}

.equipment-modal-content .problem-add,
.equipment-modal-content .problem-remove {
  border: 0;
  box-shadow: none;
  transition: color 160ms ease, background 160ms ease, transform 100ms ease;
}

.equipment-modal-content .problem-add {
  color: var(--eq-blue);
  background: var(--eq-blue-soft);
}

.equipment-modal-content .problem-add:hover:not(:disabled) {
  color: var(--eq-blue);
  border: 0;
  background: color-mix(in srgb, var(--eq-blue), transparent 82%);
  box-shadow: none;
}

.equipment-modal-content .problem-remove {
  color: var(--eq-tertiary);
  background: transparent;
}

.equipment-modal-content .problem-remove:hover {
  color: var(--eq-red);
  background: var(--eq-red-soft);
}

.equipment-modal-content .problem-add:active,
.equipment-modal-content .problem-remove:active {
  transform: scale(0.9);
}

.equipment-modal-content .problem-empty {
  padding: 11px 12px;
  color: var(--eq-tertiary);
  border: 0;
  border-radius: 11px;
  background: var(--eq-surface);
}

.equipment-modal-content .action-btns {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  justify-items: end;
  gap: 0;
  min-height: 48px;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.equipment-modal-content .action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  width: min(100%, 250px);
  min-height: 40px;
  padding: 8px 14px;
  border: 1px solid var(--eq-border);
  border-radius: 13px;
  color: var(--eq-secondary);
  background: var(--eq-surface);
  font-weight: 600;
  font-size: 14px;
  box-shadow: none;
  transition:
      color 160ms ease,
      background-color 160ms ease,
      border-color 160ms ease,
      opacity 160ms ease,
      transform 100ms ease;
}

.equipment-modal-content .action-btn-icon {
  width: 17px;
  height: 17px;
  flex: 0 0 17px;
}

.equipment-modal-content .fix-btn:not(:disabled) {
  color: var(--eq-green);
  border-color: color-mix(in srgb, var(--eq-green), transparent 58%);
  background: color-mix(in srgb, var(--eq-green-soft), var(--eq-surface) 68%);
}

.equipment-modal-content .break-btn:not(:disabled) {
  color: var(--eq-red);
  border-color: color-mix(in srgb, var(--eq-red), transparent 58%);
  background: color-mix(in srgb, var(--eq-red-soft), var(--eq-surface) 68%);
}

.equipment-modal-content .action-btn:disabled {
  color: var(--eq-tertiary);
  background: var(--eq-surface);
  box-shadow: none;
  opacity: 0.52;
}

@media (hover: hover) and (pointer: fine) {
  .equipment-modal-content .fix-btn:hover:not(:disabled) {
    border-color: color-mix(in srgb, var(--eq-green), transparent 46%);
    background-color: color-mix(in srgb, var(--eq-green-soft), var(--eq-surface) 56%);
    box-shadow: none;
    transform: none;
  }

  .equipment-modal-content .break-btn:hover:not(:disabled) {
    border-color: color-mix(in srgb, var(--eq-red), transparent 46%);
    background-color: color-mix(in srgb, var(--eq-red-soft), var(--eq-surface) 56%);
    box-shadow: none;
    transform: none;
  }
}

.equipment-modal-content .action-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.equipment-modal-content .action-btn:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--eq-blue), transparent 68%);
  outline-offset: 1px;
}

.equipment-modal-content .status-action-zone:has(.status-inline-confirm) {
  padding: 0;
  border: 0;
  background: transparent;
  box-shadow: none;
}

.equipment-modal-content .hw-files-section {
  min-height: 0;
  padding-bottom: 0;
}

.equipment-modal-content .hw-section-header {
  margin-bottom: 10px;
}

.equipment-modal-content .hw-add-btn-small {
  min-height: 32px;
  padding: 5px 9px;
  gap: 5px;
  color: var(--eq-blue);
  border: 1px solid var(--eq-border);
  border-radius: 10px;
  background: var(--eq-surface);
  transition: color 160ms ease, background 160ms ease, border-color 160ms ease, transform 100ms ease;
}

.equipment-modal-content .hw-add-btn-small:hover {
  color: var(--eq-blue);
  border-color: color-mix(in srgb, var(--eq-blue), transparent 70%);
  background: var(--eq-blue-soft);
}

.equipment-modal-content .hw-add-btn-small:active {
  transform: scale(0.96);
}

.equipment-modal-content .hw-files-grid {
  gap: 10px;
  max-height: none;
  padding: 2px 2px 8px;
  overflow-y: hidden;
  scrollbar-color: var(--eq-border-strong) transparent;
}

.equipment-modal-content .hw-file-card {
  width: 96px;
  height: 96px;
  border: 1px solid var(--eq-border);
  border-radius: 14px;
  background: var(--eq-surface);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.07);
  transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
}

.equipment-modal-content .hw-file-card:hover {
  border-color: var(--eq-border-strong);
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.11);
  transform: scale(1.015);
}

.equipment-modal-content .hw-file-card:active {
  transform: scale(0.985);
}

.equipment-modal-content .hw-file-preview {
  pointer-events: none;
}

.equipment-modal-content .hw-delete-btn {
  top: 5px;
  right: 5px;
  width: 26px;
  height: 26px;
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.24);
  background: rgba(28, 28, 30, 0.66);
  backdrop-filter: blur(10px);
  transition: background 160ms ease, transform 100ms ease;
}

.equipment-modal-content .hw-delete-btn:hover {
  background: rgba(215, 0, 21, 0.88);
}

.equipment-modal-content .hw-delete-btn:active {
  transform: scale(0.9);
}

.equipment-modal-content .hw-no-files {
  padding: 16px;
  color: var(--eq-tertiary);
  border: 0;
  border-radius: 13px;
  background: var(--eq-surface);
}

.equipment-modal-content .hw-drop-overlay {
  color: var(--eq-blue);
  border: 1px solid color-mix(in srgb, var(--eq-blue), transparent 48%);
  border-radius: 16px;
  background: color-mix(in srgb, var(--eq-blue-soft), var(--eq-bg) 28%);
  backdrop-filter: blur(18px);
}

.equipment-modal-content .hw-drop-content {
  color: var(--eq-blue);
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 220ms ease;
}

.modal-fade-enter-active .equipment-modal-content,
.modal-fade-leave-active .equipment-modal-content {
  animation: none;
  will-change: transform, opacity;
}

.modal-fade-enter-active .equipment-modal-content {
  transition:
      transform 340ms cubic-bezier(0.16, 1, 0.3, 1),
      opacity 220ms ease-out;
}

.modal-fade-leave-active .equipment-modal-content {
  transition:
      transform 210ms cubic-bezier(0.7, 0, 0.84, 0),
      opacity 170ms ease-in;
}

.modal-fade-enter-from .equipment-modal-content,
.modal-fade-leave-to .equipment-modal-content {
  opacity: 0;
  transform: translateY(10px) scale(0.975);
}

@media (max-width: 520px) {
  .equipment-modal-heading {
    grid-template-columns: minmax(0, 1fr);
    gap: 9px;
    padding-right: 44px;
  }

  .equipment-modal-heading .status-badge {
    justify-self: start;
  }
}

@media (prefers-reduced-motion: reduce) {
  .modal-fade-enter-active .equipment-modal-content,
  .modal-fade-leave-active .equipment-modal-content {
    transform: none;
    transition: opacity 160ms ease;
  }

  .modal-fade-enter-from .equipment-modal-content,
  .modal-fade-leave-to .equipment-modal-content {
    transform: none;
  }

  .equipment-modal-content button,
  .equipment-modal-content [role='button'] {
    transition: none;
  }
}

@media (prefers-reduced-transparency: reduce) {
  .audience-equipment-modal,
  .equipment-modal-content,
  .equipment-modal-content .hw-delete-btn,
  .equipment-modal-content .hw-drop-overlay {
    backdrop-filter: none;
  }

  .equipment-modal-content {
    --eq-bg: #fafafc;
  }

  :global(html[data-theme='dark'] .equipment-modal-content) {
    --eq-bg: #1c1c1e;
  }
}

@media (prefers-contrast: more) {
  .equipment-modal-content {
    --eq-border: rgba(60, 60, 67, 0.34);
    --eq-border-strong: rgba(60, 60, 67, 0.5);
  }

  :global(html[data-theme='dark'] .equipment-modal-content) {
    --eq-border: rgba(255, 255, 255, 0.32);
    --eq-border-strong: rgba(255, 255, 255, 0.52);
  }
}

/* Просмотр фото и видео */
:global(body > .audience-lightbox-overlay) {
  width: auto !important;
  max-width: 100%;
}

:global(html:has(body > .audience-lightbox-overlay)),
:global(body:has(> .audience-lightbox-overlay)) {
  scrollbar-width: none;
}

:global(html:has(body > .audience-lightbox-overlay)::-webkit-scrollbar),
:global(body:has(> .audience-lightbox-overlay)::-webkit-scrollbar) {
  width: 0;
  height: 0;
}

.hw-lightbox {
  --lb-backdrop: rgba(226, 235, 246, 0.9);
  --lb-backdrop-solid: #e6edf6;
  --lb-surface: rgba(255, 255, 255, 0.92);
  --lb-surface-solid: #f8fafc;
  --lb-stage: #dfe7f1;
  --lb-video-stage: #d6e0eb;
  --lb-stage-shade:
      linear-gradient(180deg, rgba(248, 250, 252, 0.06), rgba(51, 65, 85, 0.12)),
      radial-gradient(circle at 50% 48%, transparent 38%, rgba(51, 65, 85, 0.12) 100%);
  --lb-border: rgba(71, 85, 105, 0.2);
  --lb-border-strong: rgba(51, 65, 85, 0.4);
  --lb-text: #152033;
  --lb-muted: #5f6f84;
  --lb-accent: #2563eb;
  --lb-control: rgba(255, 255, 255, 0.9);
  --lb-control-hover: #ffffff;
  --lb-ambient-opacity: 0.19;
  --lb-ease-out: cubic-bezier(0.23, 1, 0.32, 1);

  position: fixed;
  inset: 0;
  z-index: 2000;
  height: 100vh;
  height: 100dvh;
  height: var(--audience-modal-vh, 100dvh);
  color: var(--lb-text);
  color-scheme: light;
  background: transparent;
  overflow: visible;
  overscroll-behavior: contain;
  isolation: isolate;
  animation: none;
  outline: none;
}

.hw-lightbox::before {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
      radial-gradient(circle at 18% 12%, rgba(96, 165, 250, 0.2), transparent 36%),
      radial-gradient(circle at 84% 86%, rgba(59, 130, 246, 0.1), transparent 32%),
      var(--lb-backdrop);
  backdrop-filter: blur(14px) saturate(0.9);
}

.hw-lb-shell {
  position: fixed;
  inset: 0;
  z-index: 1;
  width: 100%;
  height: 100vh;
  height: 100dvh;
  height: var(--audience-modal-vh, 100dvh);
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  gap: clamp(10px, 1.4vh, 16px);
  padding:
      max(16px, env(safe-area-inset-top))
      clamp(14px, 2.2vw, 32px)
      max(14px, env(safe-area-inset-bottom));
  overflow: hidden;
  overscroll-behavior: contain;
}

:global(html[data-theme='dark'] .hw-lightbox) {
  --lb-backdrop: rgba(1, 4, 9, 0.97);
  --lb-backdrop-solid: #05080d;
  --lb-surface: rgba(12, 18, 28, 0.96);
  --lb-surface-solid: #111827;
  --lb-stage: #03060a;
  --lb-video-stage: #020407;
  --lb-stage-shade:
      linear-gradient(180deg, rgba(3, 6, 10, 0.18), rgba(3, 6, 10, 0.48)),
      radial-gradient(circle at 50% 48%, transparent 32%, rgba(2, 5, 9, 0.34) 100%);
  --lb-border: rgba(148, 163, 184, 0.18);
  --lb-border-strong: rgba(148, 163, 184, 0.38);
  --lb-text: #edf2f8;
  --lb-muted: #9aa8ba;
  --lb-accent: #8ab4ff;
  --lb-control: rgba(9, 15, 24, 0.92);
  --lb-control-hover: rgba(24, 34, 48, 0.99);
  --lb-ambient-opacity: 0.26;
  color-scheme: dark;
}

.hw-lb-header,
.hw-lb-content,
.hw-lb-footer {
  position: relative;
  z-index: 1;
}

.hw-lb-header {
  width: min(100%, 1480px);
  min-height: 56px;
  margin-inline: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 6px 7px 6px 9px;
  border: 1px solid var(--lb-border);
  border-radius: 17px;
  background: var(--lb-surface);
  box-shadow: 0 10px 30px rgba(51, 65, 85, 0.1);
}

:global(html[data-theme='dark'] .hw-lb-header) {
  color: var(--lb-text) !important;
  border-color: var(--lb-border) !important;
  background: var(--lb-surface) !important;
  box-shadow: 0 12px 34px rgba(0, 0, 0, 0.24) !important;
}

.hw-lb-context,
.hw-lb-context-copy {
  min-width: 0;
  display: flex;
  align-items: center;
}

.hw-lb-context {
  max-width: calc(100% - 56px);
  min-height: 46px;
  gap: 11px;
  padding: 2px 0;
}

.hw-lb-kind-icon {
  width: 40px;
  height: 40px;
  flex: 0 0 40px;
  display: grid;
  place-items: center;
  color: var(--lb-accent);
  border: 1px solid color-mix(in srgb, var(--lb-accent) 24%, transparent);
  border-radius: 13px;
  background: color-mix(in srgb, var(--lb-accent) 10%, transparent);
}

.hw-lb-kind-icon svg {
  width: 18px;
  height: 18px;
}

.hw-lb-context-copy {
  flex-direction: column;
  align-items: flex-start;
  gap: 1px;
}

.hw-lb-meta {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--lb-muted);
  font-size: 11px;
  line-height: 1.3;
  font-variant-numeric: tabular-nums;
}

.hw-lb-meta-separator {
  width: 3px;
  height: 3px;
  flex: 0 0 3px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.62;
}

.hw-lb-context-copy strong {
  max-width: min(52vw, 620px);
  color: var(--lb-text);
  font-size: 15px;
  line-height: 1.3;
  letter-spacing: -0.012em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hw-lb-close,
.hw-lb-nav,
.hw-lb-thumb {
  appearance: none;
  border: 0;
  cursor: pointer;
}

.hw-lb-close {
  width: 44px;
  height: 44px;
  flex: 0 0 44px;
  display: grid;
  place-items: center;
  color: var(--lb-text);
  border: 1px solid var(--lb-border);
  border-radius: 50%;
  background: var(--lb-control);
  transition:
      color 140ms var(--lb-ease-out),
      background-color 140ms var(--lb-ease-out),
      border-color 140ms var(--lb-ease-out),
      transform 100ms var(--lb-ease-out);
}

.hw-lb-close svg {
  width: 19px;
  height: 19px;
}

.hw-lb-content {
  width: min(100%, 1480px);
  min-height: 0;
  margin-inline: auto;
  display: grid;
  place-items: stretch;
}

.hw-lb-stage {
  position: relative;
  min-width: 0;
  min-height: 220px;
  display: grid;
  place-items: center;
  overflow: hidden;
  isolation: isolate;
  padding: clamp(10px, 1.8vw, 24px);
  border-radius: 18px;
  background: var(--lb-stage);
  box-shadow: 0 28px 90px rgba(0, 0, 0, 0.46);
}

.hw-lb-stage::before {
  display: none;
}

.hw-lb-stage.is-video {
  background: var(--lb-video-stage);
}

.hw-lb-ambient,
.hw-lb-stage-shade {
  position: absolute;
  pointer-events: none;
}

.hw-lb-ambient {
  inset: -12%;
  z-index: 0;
  opacity: var(--lb-ambient-opacity);
  filter: blur(58px) saturate(0.9);
  transform: scale(1.08);
}

.hw-lb-ambient img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.hw-lb-stage-shade {
  inset: 0;
  z-index: 1;
  background: var(--lb-stage-shade);
}

.hw-lb-media-frame {
  position: relative;
  z-index: 2;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  display: grid;
  place-items: center;
  overflow: hidden;
}

.hw-lb-image,
.hw-lb-video {
  position: relative;
  z-index: 1;
  width: auto;
  height: auto;
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 10px;
  box-shadow: 0 18px 56px rgba(0, 0, 0, 0.38);
  user-select: none;
}

.hw-lb-image {
  display: block;
  cursor: zoom-in;
  touch-action: none;
  transform-origin: center;
  transition: transform 180ms var(--lb-ease-out);
}

.hw-lb-image.is-pannable {
  cursor: grab;
  will-change: transform;
}

.hw-lb-image.is-panning {
  cursor: grabbing;
  transition: none;
}

.hw-lb-video {
  width: min(100%, 1280px);
  background: #000;
}

.hw-lb-zoom {
  position: absolute;
  left: 50%;
  bottom: clamp(10px, 1.5vw, 18px);
  z-index: 4;
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 4px;
  border: 1px solid var(--lb-border);
  border-radius: 14px;
  background: var(--lb-surface);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.18);
  transform: translateX(-50%);
}

:global(html[data-theme='dark'] .hw-lb-zoom) {
  border-color: var(--lb-border) !important;
  background: var(--lb-surface) !important;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.28) !important;
}

.hw-lb-zoom-btn,
.hw-lb-zoom-value {
  appearance: none;
  min-height: 36px;
  display: grid;
  place-items: center;
  color: var(--lb-text);
  border: 0;
  border-radius: 10px;
  background: transparent;
  cursor: pointer;
  transition:
      color 140ms var(--lb-ease-out),
      background-color 140ms var(--lb-ease-out),
      transform 100ms var(--lb-ease-out),
      opacity 140ms var(--lb-ease-out);
}

.hw-lb-zoom-btn {
  width: 36px;
}

.hw-lb-zoom-btn svg {
  width: 18px;
  height: 18px;
}

.hw-lb-zoom-value {
  min-width: 58px;
  padding-inline: 8px;
  color: var(--lb-muted);
  font-size: 12px;
  font-weight: 650;
  font-variant-numeric: tabular-nums;
}

.hw-lb-zoom-value.is-fit {
  color: var(--lb-accent);
  background: color-mix(in srgb, var(--lb-accent) 10%, transparent);
}

.hw-lb-zoom-btn:disabled {
  opacity: 0.32;
  cursor: default;
}

.hw-lb-nav {
  position: absolute;
  top: 50%;
  z-index: 3;
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  color: var(--lb-text);
  border: 1px solid var(--lb-border);
  border-radius: 50%;
  background: var(--lb-control);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.28);
  transform: translateY(-50%);
  transition:
      color 140ms var(--lb-ease-out),
      background-color 140ms var(--lb-ease-out),
      border-color 140ms var(--lb-ease-out),
      transform 100ms var(--lb-ease-out);
}

.hw-lb-nav svg {
  width: 20px;
  height: 20px;
}

.hw-lb-prev {
  left: clamp(10px, 1.5vw, 20px);
}

.hw-lb-next {
  right: clamp(10px, 1.5vw, 20px);
}

.hw-lb-footer {
  width: fit-content;
  max-width: min(100%, 900px);
  margin-inline: auto;
}

.hw-lb-filmstrip {
  min-width: 0;
  max-width: min(calc(100vw - 32px), 888px);
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px;
  overflow-x: auto;
  border: 1px solid var(--lb-border);
  border-radius: 14px;
  background: var(--lb-surface);
  overscroll-behavior-inline: contain;
  scrollbar-width: none;
}

.hw-lb-filmstrip::-webkit-scrollbar {
  display: none;
}

.hw-lb-thumb {
  position: relative;
  width: 58px;
  height: 44px;
  flex: 0 0 58px;
  padding: 2px;
  overflow: hidden;
  color: var(--lb-muted);
  border: 1px solid transparent;
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.04);
  opacity: 0.52;
  transition:
      opacity 140ms var(--lb-ease-out),
      border-color 140ms var(--lb-ease-out),
      background-color 140ms var(--lb-ease-out),
      transform 100ms var(--lb-ease-out);
}

.hw-lb-thumb img,
.hw-lb-thumb-video {
  width: 100%;
  height: 100%;
  display: block;
  border-radius: 7px;
  object-fit: cover;
}

.hw-lb-thumb-video {
  opacity: 0;
  pointer-events: none;
  transition: opacity 180ms var(--lb-ease-out);
}

.hw-lb-thumb-video.is-ready {
  opacity: 1;
}

.hw-lb-video-thumb {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.24);
  border-radius: 50%;
  background: rgba(7, 12, 20, 0.68);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.24);
  pointer-events: none;
  transform: translate(-50%, -50%);
}

.hw-lb-video-thumb svg {
  width: 12px;
  height: 12px;
  margin-left: 1px;
}

.hw-lb-thumb.is-active {
  opacity: 1;
  border-color: var(--lb-accent);
  background: color-mix(in srgb, var(--lb-accent) 10%, transparent);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--lb-accent) 18%, transparent);
}

.hw-lightbox-fade-enter-active {
  transition: opacity 260ms var(--lb-ease-out);
}

.hw-lightbox-fade-leave-active {
  transition: opacity 180ms var(--lb-ease-out);
}

.hw-lightbox-fade-enter-active .hw-lb-header,
.hw-lightbox-fade-enter-active .hw-lb-content,
.hw-lightbox-fade-enter-active .hw-lb-footer {
  transition:
      opacity 280ms var(--lb-ease-out),
      transform 320ms var(--lb-ease-out),
      filter 260ms var(--lb-ease-out);
}

.hw-lightbox-fade-leave-active .hw-lb-header,
.hw-lightbox-fade-leave-active .hw-lb-content,
.hw-lightbox-fade-leave-active .hw-lb-footer {
  transition:
      opacity 160ms var(--lb-ease-out),
      transform 180ms var(--lb-ease-out),
      filter 160ms var(--lb-ease-out);
}

.hw-lightbox-fade-enter-from,
.hw-lightbox-fade-leave-to,
.hw-lightbox-fade-enter-from .hw-lb-header,
.hw-lightbox-fade-enter-from .hw-lb-content,
.hw-lightbox-fade-enter-from .hw-lb-footer,
.hw-lightbox-fade-leave-to .hw-lb-header,
.hw-lightbox-fade-leave-to .hw-lb-content,
.hw-lightbox-fade-leave-to .hw-lb-footer {
  opacity: 0;
}

.hw-lightbox-fade-enter-from .hw-lb-header {
  transform: translateY(-8px);
}

.hw-lightbox-fade-enter-from .hw-lb-content {
  filter: blur(8px);
  transform: scale(0.975);
}

.hw-lightbox-fade-enter-from .hw-lb-footer {
  transform: translateY(8px);
}

.hw-lightbox-fade-leave-to .hw-lb-header {
  transform: translateY(-3px);
}

.hw-lightbox-fade-leave-to .hw-lb-content {
  filter: blur(4px);
  transform: scale(0.988);
}

.hw-lightbox-fade-leave-to .hw-lb-footer {
  transform: translateY(3px);
}

.hw-media-swap-enter-active {
  transition:
      opacity 220ms var(--lb-ease-out),
      transform 240ms var(--lb-ease-out),
      filter 200ms var(--lb-ease-out);
}

.hw-media-swap-leave-active {
  transition:
      opacity 120ms var(--lb-ease-out),
      transform 140ms var(--lb-ease-out),
      filter 120ms var(--lb-ease-out);
}

.hw-media-swap-enter-from {
  opacity: 0;
  filter: blur(5px);
  transform: scale(0.988);
}

.hw-media-swap-leave-to {
  opacity: 0;
  filter: blur(3px);
  transform: scale(0.994);
}

.hw-ambient-swap-enter-active,
.hw-ambient-swap-leave-active {
  transition: opacity 260ms var(--lb-ease-out);
}

.hw-ambient-swap-enter-from,
.hw-ambient-swap-leave-to {
  opacity: 0;
}

@media (hover: hover) and (pointer: fine) {
  .hw-lb-close:hover,
  .hw-lb-nav:hover {
    color: var(--lb-text);
    border-color: var(--lb-border-strong);
    background: var(--lb-control-hover);
  }

  .hw-lb-thumb:hover {
    opacity: 0.9;
    border-color: var(--lb-border-strong);
    transform: translateY(-2px);
  }

  .hw-lb-thumb.is-active:hover {
    opacity: 1;
    border-color: var(--lb-accent);
  }

  .hw-lb-zoom-btn:hover:not(:disabled),
  .hw-lb-zoom-value:hover {
    color: var(--lb-text);
    background: var(--lb-control-hover);
  }
}

.hw-lb-close:active {
  transform: scale(0.94);
}

.hw-lb-nav:active {
  transform: translateY(-50%) scale(0.94);
}

.hw-lb-thumb:active {
  transform: scale(0.95);
}

.hw-lb-zoom-btn:active:not(:disabled),
.hw-lb-zoom-value:active {
  transform: scale(0.94);
}

.hw-lb-close:focus-visible,
.hw-lb-nav:focus-visible,
.hw-lb-thumb:focus-visible,
.hw-lb-zoom-btn:focus-visible,
.hw-lb-zoom-value:focus-visible {
  outline: 2px solid var(--lb-accent);
  outline-offset: 2px;
}

@media (max-width: 800px) {
  .hw-lb-shell {
    gap: 9px;
    padding:
        max(10px, env(safe-area-inset-top))
        8px
        max(10px, env(safe-area-inset-bottom));
  }

  .hw-lb-header {
    min-height: 42px;
  }

  .hw-lb-context {
    min-height: 42px;
  }

  .hw-lb-kind-icon {
    width: 36px;
    height: 36px;
    flex-basis: 36px;
    border-radius: 12px;
  }

  .hw-lb-context-copy strong {
    max-width: 48vw;
    font-size: 13px;
  }

  .hw-lb-stage {
    min-height: 180px;
    padding: 5px;
    border-radius: 14px;
  }

  .hw-lb-image,
  .hw-lb-video {
    border-radius: 8px;
  }

  .hw-lb-nav {
    width: 40px;
    height: 40px;
  }

  .hw-lb-nav svg {
    width: 19px;
    height: 19px;
  }

  .hw-lb-prev {
    left: 8px;
  }

  .hw-lb-next {
    right: 8px;
  }

  .hw-lb-footer {
    max-width: 100%;
  }

  .hw-lb-filmstrip {
    max-width: calc(100vw - 16px);
    padding: 5px;
    border-radius: 12px;
  }

  .hw-lb-zoom {
    bottom: 8px;
    padding: 3px;
    border-radius: 12px;
  }

  .hw-lb-zoom-btn,
  .hw-lb-zoom-value {
    min-height: 34px;
    border-radius: 9px;
  }

  .hw-lb-zoom-btn {
    width: 34px;
  }

  .hw-lb-zoom-value {
    min-width: 54px;
    font-size: 11px;
  }
}

@media (max-width: 520px) {
  .hw-lb-context-copy strong {
    max-width: 46vw;
  }

  .hw-lb-meta {
    font-size: 10px;
  }

  .hw-lb-thumb {
    width: 52px;
    height: 40px;
    flex-basis: 52px;
    border-radius: 8px;
  }

  .hw-lb-filmstrip {
    gap: 6px;
  }
}

@media (max-width: 400px) {
  .hw-lb-kind-icon {
    display: none;
  }

  .hw-lb-context-copy strong {
    max-width: 60vw;
  }
}

@media (max-height: 620px) {
  .hw-lb-shell {
    gap: 7px;
    padding-top: max(7px, env(safe-area-inset-top));
    padding-bottom: max(7px, env(safe-area-inset-bottom));
  }

  .hw-lb-kind-icon,
  .hw-lb-close {
    height: 34px;
  }

  .hw-lb-kind-icon,
  .hw-lb-close {
    width: 34px;
    flex-basis: 34px;
  }

  .hw-lb-footer {
    max-height: 44px;
  }

  .hw-lb-thumb {
    width: 48px;
    height: 32px;
    flex-basis: 48px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .hw-lightbox-fade-enter-active,
  .hw-lightbox-fade-leave-active {
    transition: opacity 140ms ease-out;
  }

  .hw-lightbox-fade-enter-active .hw-lb-header,
  .hw-lightbox-fade-enter-active .hw-lb-content,
  .hw-lightbox-fade-enter-active .hw-lb-footer,
  .hw-lightbox-fade-leave-active .hw-lb-header,
  .hw-lightbox-fade-leave-active .hw-lb-content,
  .hw-lightbox-fade-leave-active .hw-lb-footer,
  .hw-media-swap-enter-active,
  .hw-media-swap-leave-active,
  .hw-ambient-swap-enter-active,
  .hw-ambient-swap-leave-active,
  .hw-lb-image,
  .hw-lb-thumb-video {
    transition: opacity 120ms ease-out;
  }

  .hw-lightbox-fade-enter-from .hw-lb-header,
  .hw-lightbox-fade-enter-from .hw-lb-content,
  .hw-lightbox-fade-enter-from .hw-lb-footer,
  .hw-lightbox-fade-leave-to .hw-lb-header,
  .hw-lightbox-fade-leave-to .hw-lb-content,
  .hw-lightbox-fade-leave-to .hw-lb-footer,
  .hw-media-swap-enter-from,
  .hw-media-swap-leave-to,
  .hw-ambient-swap-enter-from,
  .hw-ambient-swap-leave-to {
    filter: none;
    transform: none;
  }
}

@media (prefers-reduced-transparency: reduce) {
  .hw-lightbox::before {
    background: var(--lb-backdrop-solid);
    backdrop-filter: none;
  }

  .hw-lb-header,
  .hw-lb-close,
  .hw-lb-nav,
  .hw-lb-filmstrip,
  .hw-lb-zoom {
    background: var(--lb-surface-solid);
    backdrop-filter: none;
  }
}

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
    max-width: min(100%, 12ch);
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
  }

  .scale-type-btn,
  .scale-controls {
    display: none;
  }

  .grid-info {
    display: none;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }

  .stats-section {
    margin-bottom: 16px;
  }

  .stat-card {
    min-width: 0;
    padding: 11px 12px;
    border-radius: 13px;
  }

  .stat-card:hover {
    transform: none;
  }

  .stat-label {
    min-height: 22px;
    margin-bottom: 4px;
    font-size: 10px;
    line-height: 1.1;
    letter-spacing: 0.2px;
  }

  .stat-value {
    font-size: 22px;
    line-height: 1;
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
    max-height: calc(var(--audience-modal-vh, 100dvh) - 24px);
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
    top: 12px;
    right: 14px;
    padding-top: 0;
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
    padding-right: 0;
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

  .equipment-modal .modal-equipment-details .modal-equipment-inline-edit .modal-equipment-inline-input {
    width: clamp(132px, 58vw, 204px);
    max-width: 100%;
    flex: 0 1 auto;
    min-height: 28px;
    height: 28px;
    padding: 1px 8px;
    font-size: 12px;
    line-height: 1.1;
    border-radius: 8px;
    border-width: 1px;
    box-sizing: border-box;
  }

  .equipment-modal .modal-equipment-details .modal-equipment-inline-edit.is-inv .modal-equipment-inline-input {
    width: clamp(104px, 44vw, 156px);
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
    min-height: 32px;
    padding: 4px 9px;
    border-radius: 9px;
    gap: 6px;
  }

  .equipment-modal .status-badge {
    display: inline-flex;
    align-items: center;
    justify-content: flex-start;
    width: auto;
    padding: 7px 10px;
    margin: 0;
    border-radius: 999px;
    font-size: 12px;
    text-align: left;
  }

  .equipment-modal .form-group {
    margin: 0;
  }

  .equipment-modal .form-label {
    margin-bottom: 6px;
    font-size: 12px;
  }

  .equipment-modal .problem-header {
    margin-bottom: 6px;
  }

  .equipment-modal .problem-header .form-label {
    margin-bottom: 0;
  }

  .equipment-modal .problem-add {
    width: 28px;
    height: 28px;
    border-radius: 9px;
  }

  .equipment-modal .form-textarea {
    min-height: 88px;
    padding: 12px 14px;
    border-radius: 14px;
    font-size: 14px;
  }

  .equipment-modal .action-btns {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 0;
    margin: 0;
  }

  .equipment-modal .status-action-zone:has(.status-inline-confirm) {
    grid-template-columns: minmax(0, 1fr);
  }

  .equipment-modal .status-action-zone > .status-inline-confirm {
    grid-column: 1 / -1;
  }

  .equipment-modal .action-btns > .action-btn:only-child {
    grid-column: 1 / -1;
  }

  .equipment-modal .action-btn {
    width: 100%;
    min-height: 36px;
    padding: 8px 10px;
    border-radius: 10px;
    font-size: 13px;
  }

  .unsaved-problems-overlay {
    padding: 10px;
    align-items: flex-end;
  }

  .unsaved-problems-dialog {
    width: min(100%, 400px);
    padding: 14px;
    border-radius: 18px;
  }

  .unsaved-problems-icon {
    width: 36px;
    height: 36px;
    margin-bottom: 8px;
    border-radius: 13px;
  }

  .unsaved-problems-copy h3 {
    font-size: 18px;
  }

  .unsaved-problems-copy p {
    font-size: 12px;
    line-height: 1.42;
  }

  .unsaved-problems-actions {
    grid-template-columns: 1fr 1fr;
  }

  .unsaved-problems-btn.is-primary {
    grid-column: 1 / -1;
    order: -1;
  }

  .unsaved-problems-btn {
    min-height: 32px;
    padding: 6px 9px;
    font-size: 11px;
  }

  .equipment-modal .hw-files-section {
    margin: 0;
    padding-top: 16px;
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
  .spec-form-section-grid {
    grid-template-columns: 1fr;
  }

  .spec-form-section {
    padding: 0;
    border-radius: 14px;
  }

  .spec-form-section-toggle {
    min-height: 52px;
    padding: 10px 12px;
  }

  .spec-form-section-grid {
    padding: 0 12px 12px;
  }

  .spec-form-group-double {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .spec-form-group-os {
    grid-template-columns: 1fr;
  }

  .software-presets {
    grid-template-columns: 1fr;
    gap: 7px;
  }

  .software-presets-head {
    flex-direction: row;
    align-items: baseline;
    gap: 7px;
  }

  .software-preset-list {
    justify-content: flex-start;
    flex-wrap: nowrap;
    overflow-x: auto;
    padding: 1px 1px 3px;
    scrollbar-width: none;
  }

  .software-preset-list::-webkit-scrollbar {
    display: none;
  }

  .software-options {
    grid-template-columns: repeat(2, minmax(0, 1fr));
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
    max-height: calc(var(--audience-modal-vh, 100dvh) - 20px);
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

  .equipment-modal .modal-equipment-details .modal-equipment-inline-edit .modal-equipment-inline-input {
    width: clamp(120px, 54vw, 176px);
    min-height: 26px;
    height: 26px;
    padding: 0 7px;
    font-size: 11px;
    line-height: 1.1;
    border-radius: 7px;
  }

  .equipment-modal .modal-equipment-details .modal-equipment-inline-edit.is-inv .modal-equipment-inline-input {
    width: clamp(96px, 40vw, 138px);
  }

  .equipment-modal .modal-equipment-inline-edit :deep(svg) {
    width: 15px;
    height: 15px;
  }

  .equipment-modal .status-badge {
    padding: 7px 10px;
    font-size: 11px;
  }

  .equipment-modal .problem-empty {
    font-size: 11px;
  }

  .equipment-modal .action-btn {
    min-height: 34px;
    padding: 7px 8px;
    font-size: 12px;
  }

  .unsaved-problems-dialog {
    padding: 12px;
    border-radius: 16px;
  }

  .unsaved-problems-kicker {
    font-size: 10px;
    letter-spacing: 0.09em;
  }

  .unsaved-problems-copy h3 {
    font-size: 17px;
  }

  .unsaved-problems-note {
    align-items: flex-start;
    flex-direction: column;
    gap: 5px;
    padding: 8px 10px;
    font-size: 11px;
  }

  .unsaved-problems-note strong {
    font-size: 11px;
  }

  .unsaved-problems-actions {
    grid-template-columns: 1fr;
    gap: 6px;
  }

  .unsaved-problems-btn.is-primary {
    order: -2;
  }

  .equipment-modal .hw-file-card {
    width: 80px;
    height: 80px;
  }

  .stats-grid {
    gap: 6px;
  }

  .stats-section {
    margin-bottom: 12px;
  }

  .stat-card {
    padding: 9px 10px;
    border-radius: 12px;
  }

  .stat-label {
    min-height: 20px;
    margin-bottom: 3px;
    font-size: 9px;
    letter-spacing: 0.1px;
  }

  .stat-value {
    font-size: 20px;
  }

  .equipment-grid {
    --cell-size: calc(55px * var(--ui-scale));
    --icon-div-size: calc(30px * var(--ui-scale));
    --icon-size: calc(18px * var(--ui-scale));
    --grid-gap: calc(4px * var(--ui-scale));
  }

  .equipment-label {
    max-width: min(100%, 10ch);
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

  .equipment-modal .specs-entry-btn {
    min-height: 30px;
    padding: 3px 8px;
    border-radius: 8px;
    font-size: 11px;
    gap: 5px;
  }

  .equipment-modal .specs-entry-btn svg {
    width: 14px;
    height: 14px;
  }

  .specs-template-toggle {
    min-height: 46px;
    padding: 7px 10px;
  }

  .specs-template-toggle-icon {
    width: 28px;
    height: 28px;
    flex-basis: 28px;
    border-radius: 9px;
  }

  .specs-template-toggle-copy small {
    display: none;
  }

  .spec-form-section-copy small {
    font-size: 10px;
  }

  .spec-form-label {
    font-size: 11px;
  }

  .spec-input,
  .spec-os-option {
    min-height: 40px;
  }

  .spec-os-option {
    gap: 4px;
    padding: 6px;
    font-size: 10px;
  }

  .spec-os-option-icon {
    width: 17px;
    height: 17px;
    flex-basis: 17px;
  }

  .spec-os-option-icon :deep(svg) {
    width: 16px;
    height: 16px;
  }

  .spec-os-option-icon.is-macos :deep(svg) {
    width: 31px;
    height: 19px;
  }

  .spec-os-option-icon.is-macos {
    width: 31px;
    flex-basis: 31px;
  }

  .spec-os-option-icon.is-linux :deep(svg) {
    width: 14px;
    height: 17px;
  }

  .software-option {
    min-height: 34px;
    padding: 5px 7px;
  }

  .software-option-label {
    font-size: 10px;
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

  .spec-card-list {
    gap: 10px;
  }

  .spec-card-tags,
  .spec-list-items {
    max-height: 108px;
  }

  .spec-list-add-btn {
    width: 44px;
    padding: 0;
  }

  .spec-list-add-btn span {
    display: none;
  }

  .spec-list-hint {
    font-size: 10px;
  }
}
</style>
