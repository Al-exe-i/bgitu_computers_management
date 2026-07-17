<script>
import router from "@/router/index.js";
import api from "@/services/api.js";
import {useNotificationsStore} from "@/stores/notifications.js";
import {useAudienceContext} from "@/stores/officeCtx.js";
import {useAuthStore} from "@/stores/auth.js";
import TrustedSvgIcon from "@/components/Common/TrustedSvgIcon.vue";

const EQUIPMENT_TYPES = Object.freeze([
  {
    id: 'computer',
    name: 'Компьютер',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">\n' +
        '                <rect x="2" y="3" width="20" height="14" rx="2"></rect>\n' +
        '                <path d="M8 21h8M12 17v4"></path>\n' +
        '              </svg>',
    color: 'linear-gradient(145deg, #60a5fa 0%, #3b82f6 48%, #1d4ed8 100%)'
  },
  {
    id: 'server',
    name: 'Сервер',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><title>Сервер</title><path fill="currentColor" d="M20 3H4a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2M4 9V5h16v4zm16 4H4a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-4a2 2 0 0 0-2-2M4 19v-4h16v4z"/><path fill="currentColor" d="M17 6h2v2h-2zm-3 0h2v2h-2zm3 10h2v2h-2zm-3 0h2v2h-2z"/></svg>',
    color: 'linear-gradient(135deg, #0f766e, #14b8a6)'
  },
  {
    id: 'tv',
    name: 'Телевизор',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 1920 1536"><title>Телевизор</title><path fill="currentColor" d="M1792 1120V160q0-13-9.5-22.5T1760 128H160q-13 0-22.5 9.5T128 160v960q0 13 9.5 22.5t22.5 9.5h1600q13 0 22.5-9.5t9.5-22.5m128-960v960q0 66-47 113t-113 47h-736v128h352q14 0 23 9t9 23v64q0 14-9 23t-23 9H544q-14 0-23-9t-9-23v-64q0-14 9-23t23-9h352v-128H160q-66 0-113-47T0 1120V160Q0 94 47 47T160 0h1600q66 0 113 47t47 113"/></svg>',
    color: 'linear-gradient(145deg, #fb923c 0%, #f97316 50%, #c2410c 100%)'
  },
  {
    id: 'projector',
    name: 'Проектор',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 16 16"><title>Projector SVG Icon</title><g fill="currentColor"><path d="M14 7.5a1.5 1.5 0 1 1-3 0a1.5 1.5 0 0 1 3 0M2.5 6a.5.5 0 0 0 0 1h4a.5.5 0 0 0 0-1zm0 2a.5.5 0 0 0 0 1h4a.5.5 0 0 0 0-1z"/><path d="M0 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2a1 1 0 0 1-1 1h-1a1 1 0 0 1-1-1H5a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1a2 2 0 0 1-2-2zm2-1a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V6a1 1 0 0 0-1-1z"/></g></svg>',
    color: 'linear-gradient(145deg, #a78bfa 0%, #8b5cf6 48%, #6d28d9 100%)'
  },
  {
    id: 'printer',
    name: 'Принтер',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 16 16"><title>Printer-fill SVG Icon</title><g fill="currentColor"><path d="M5 1a2 2 0 0 0-2 2v1h10V3a2 2 0 0 0-2-2zm6 8H5a1 1 0 0 0-1 1v3a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-3a1 1 0 0 0-1-1"/><path d="M0 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2h-1v-2a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v2H2a2 2 0 0 1-2-2zm2.5 1a.5.5 0 1 0 0-1a.5.5 0 0 0 0 1"/></g></svg>',
    color: 'linear-gradient(145deg, #34d399 0%, #10b981 48%, #047857 100%)'
  },
  {
    id: 'switch',
    name: 'Коммутатор',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 36 36"><title>Network-switch-solid-badged SVG Icon</title><path fill="currentColor" d="M32.26 13.15A7.49 7.49 0 0 1 22.57 7H7.13a2 2 0 0 0-1.91 1.41L2.09 18.48a2 2 0 0 0-.09.59V27a2 2 0 0 0 2 2h28a2 2 0 0 0 2-2v-7.94a2 2 0 0 0-.09-.59ZM8.92 25h-1.8v-3h1.8Zm5 0h-1.8v-3h1.8Zm5 0h-1.8v-3h1.8Zm5 0H22.1v-3h1.8Zm5 0H27.1v-3h1.8ZM31 19.4H5V18h26Z" class="clr-i-solid--badged clr-i-solid-path-1--badged"/><circle cx="30" cy="6" r="5" fill="currentColor" class="clr-i-solid--badged clr-i-solid-path-2--badged clr-i-badge"/><path fill="none" d="M0 0h36v36H0z"/></svg>',
    color: 'linear-gradient(145deg, #fbbf24 0%, #f59e0b 50%, #b45309 100%)'
  },
  {
    id: 'router',
    name: 'Роутер',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 16 16"><title>Router-fill SVG Icon</title><g fill="currentColor"><path d="M5.525 3.025a3.5 3.5 0 0 1 4.95 0a.5.5 0 1 0 .707-.707a4.5 4.5 0 0 0-6.364 0a.5.5 0 0 0 .707.707"/><path d="M6.94 4.44a1.5 1.5 0 0 1 2.12 0a.5.5 0 0 0 .708-.708a2.5 2.5 0 0 0-3.536 0a.5.5 0 0 0 .707.707Z"/><path d="M2.974 2.342a.5.5 0 1 0-.948.316L3.806 8H1.5A1.5 1.5 0 0 0 0 9.5v2A1.5 1.5 0 0 0 1.5 13H2a.5.5 0 0 0 .5.5h2A.5.5 0 0 0 5 13h6a.5.5 0 0 0 .5.5h2a.5.5 0 0 0 .5-.5h.5a1.5 1.5 0 0 0 1.5-1.5v-2A1.5 1.5 0 0 0 14.5 8h-2.306l1.78-5.342a.5.5 0 1 0-.948-.316L11.14 8H4.86zM2.5 11a.5.5 0 1 1 0-1a.5.5 0 0 1 0 1m4.5-.5a.5.5 0 1 1 1 0a.5.5 0 0 1-1 0m2.5.5a.5.5 0 1 1 0-1a.5.5 0 0 1 0 1m1.5-.5a.5.5 0 1 1 1 0a.5.5 0 0 1-1 0m2 0a.5.5 0 1 1 1 0a.5.5 0 0 1-1 0"/><path d="M8.5 5.5a.5.5 0 1 1-1 0a.5.5 0 0 1 1 0"/></g></svg>',
    color: 'linear-gradient(145deg, #22d3ee 0%, #06b6d4 48%, #0e7490 100%)'
  },
  {
    id: 'other',
    name: 'Другое',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><title>Processor-solid SVG Icon</title><path fill="currentColor" d="M10.358 9.938c1.082-.12 2.202-.12 3.284 0a.464.464 0 0 1 .409.4c.129 1.104.129 2.22 0 3.324a.464.464 0 0 1-.41.4a14.92 14.92 0 0 1-3.283 0a.464.464 0 0 1-.409-.4a14.324 14.324 0 0 1 0-3.324a.464.464 0 0 1 .41-.4"/><path fill="currentColor" fill-rule="evenodd" d="M15 2.25a.75.75 0 0 1 .75.75v2.927a2.929 2.929 0 0 1 2.308 2.323H21a.75.75 0 0 1 0 1.5h-2.788c.037.5.061 1 .073 1.5H20a.75.75 0 0 1 0 1.5h-1.715c-.012.5-.036 1-.073 1.5H21a.75.75 0 0 1 0 1.5h-2.942a2.929 2.929 0 0 1-2.308 2.323V21a.75.75 0 0 1-1.5 0v-2.774c-.498.035-.999.059-1.5.07V20a.75.75 0 0 1-1.5 0v-1.704a31.963 31.963 0 0 1-1.5-.07V21a.75.75 0 0 1-1.5 0v-2.927a2.929 2.929 0 0 1-2.308-2.323H3a.75.75 0 0 1 0-1.5h2.788c-.037-.5-.061-1-.074-1.5H4a.75.75 0 0 1 0-1.5h1.714c.013-.5.037-1 .074-1.5H3a.75.75 0 0 1 0-1.5h2.942A2.929 2.929 0 0 1 8.25 5.927V3a.75.75 0 0 1 1.5 0v2.774c.498-.035.999-.059 1.5-.07V4a.75.75 0 0 1 1.5 0v1.704c.501.011 1.002.035 1.5.07V3a.75.75 0 0 1 .75-.75m-1.192 6.197a16.407 16.407 0 0 0-3.616 0c-.898.1-1.626.808-1.732 1.717a15.808 15.808 0 0 0 0 3.672c.106.91.834 1.616 1.732 1.717c1.192.133 2.424.133 3.616 0a1.963 1.963 0 0 0 1.732-1.717c.143-1.22.143-2.452 0-3.672a1.963 1.963 0 0 0-1.732-1.717" clip-rule="evenodd"/></svg>',
    color: 'linear-gradient(145deg, #94a3b8 0%, #64748b 48%, #334155 100%)'
  }
])

const LANDMARK_LABELS = Object.freeze({
  north: 'Север',
  south: 'Юг',
  west: 'Запад',
  east: 'Восток',
})

const HISTORY_LIMIT = 40;
const EQUIPMENT_SNAP_DURATION_MS = 1450;
const EQUIPMENT_SNAP_MIN_PARTICLES = 145;
const EQUIPMENT_SNAP_MAX_PARTICLES = 230;

function extractSolidColors(value) {
  return [...new Set(String(value ?? '').match(/#[\da-f]{3,8}\b/gi) ?? [])];
}

function prefersReducedMotion() {
  return typeof window !== 'undefined'
      && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
}

function normalizeLandmarks(source = {}) {
  return {
    north: String(source?.north ?? source?.nord ?? '').trim(),
    south: String(source?.south ?? '').trim(),
    west: String(source?.west ?? '').trim(),
    east: String(source?.east ?? '').trim(),
  };
}

function buildLandmarksPayload(source = {}) {
  const normalized = normalizeLandmarks(source);
  const hasValue = Object.values(normalized).some(Boolean);

  return hasValue ? normalized : {};
}

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function normalizeNullableString(value) {
  if (value === null || value === undefined) return null;
  const text = String(value).trim();
  return text.length > 0 ? text : null;
}

function cloneJsonObject(value) {
  if (!isPlainObject(value)) return {};

  try {
    return JSON.parse(JSON.stringify(value));
  } catch {
    return {};
  }
}

function sanitizeFileNamePart(value, fallback) {
  const text = String(value ?? '').trim() || fallback;
  return text
      .replace(/[\\/:*?"<>|]+/g, '_')
      .replace(/\s+/g, '_')
      .replace(/_+/g, '_');
}

export default {
  name: 'CreateAudience',
  components: { TrustedSvgIcon },
  props: ['publicId'],
  data() {
    return {
      classroomNumber: null,
      offices_ids: [],
      floorNumber: 1,
      officeNumber: 1,
      gridWidth: 6,
      gridHeight: 4,

      selectedEquipmentId: null,
      selectedEquipmentSize: { width: 1, height: 1 },

      dragOverCell: null,
      draggedEquipmentId: null,
      suppressNextCellClick: false,

      equipmentItems: [],
      deletingEquipmentIds: [],
      equipmentRemovalTimers: {},
      snapParticlesByEquipmentId: {},
      landmarks: normalizeLandmarks(),
      editingLandmark: null,
      landmarkDraft: '',

      clearGridClicked: false,
      isGridActionsOpen: false,
      paramsCollapsed: false,
      loading: false,

      hasUnsavedChanges: false,
      showUnsavedLeaveModal: false,
      pendingLeaveTarget: '',
      pendingLeaveMode: 'push',
      bypassUnsavedLeaveGuard: false,
      isHydrating: false,
      initialSnapshot: '',
      historySnapshots: [],
      historyIndex: -1,
      isApplyingHistory: false,
    };
  },

  computed: {
    isEditMode()
    {
      return !!this.publicId;
    },

    equipmentTypes() {
      return EQUIPMENT_TYPES;
    },

    pageTitle() {
      const number = this.classroomNumber || this.publicId;
      return this.isEditMode ? `Редактирование аудитории №${number}` : 'Добавление новой аудитории';
    },

    visibleEquipmentItems() {
      return this.equipmentItems.filter(item =>
          item.x >= 0 &&
          item.y >= 0 &&
          item.x + item.width <= this.gridWidth &&
          item.y + item.height <= this.gridHeight
      );
    },

    outOfBoundsEquipmentItems() {
      return this.equipmentItems.filter(item =>
          item.x < 0 ||
          item.y < 0 ||
          item.x + item.width > this.gridWidth ||
          item.y + item.height > this.gridHeight
      );
    },

    // Плотность сетки
    gridDensityClass() {
      const cols = this.gridWidth;

      if (cols > 15) return 'density-tiny';    // 16+ колонок
      if (cols > 10) return 'density-compact'; // 11-15 колонок
      return 'density-normal';                 // <= 10 колонок
    },

    equipmentTypeMap() {
      return Object.fromEntries(this.equipmentTypes.map(t => [t.id, t]));
    },

    // Автоматический подсчет статистики
    stats() {
      const counts = {
        total: 0,
        computer: 0,
        server: 0,
        tv: 0,
        projector: 0,
        printer: 0,
        switch: 0,
        router: 0,
        other: 0,
        network: 0
      };

      for (const item of this.equipmentItems) {
        counts.total++;
        if (counts[item.type] !== undefined) {
          counts[item.type]++;
        }
      }

      counts.network = counts.switch + counts.router;
      return counts;
    },

    canClearGrid() {
      return this.equipmentItems.length > 0;
    },

    canUndo() {
      return this.historyIndex > 0;
    },

    canRedo() {
      return this.historyIndex >= 0 && this.historyIndex < this.historySnapshots.length - 1;
    },

    isSaveDisabled() {
      return this.isEditMode && !this.hasUnsavedChanges;
    },

    saveButtonTitle() {
      return this.isSaveDisabled ? 'Нет изменений для сохранения' : '';
    },

    clearGridConfirmText() {
      const count = this.equipmentItems.length;

      if (!count) {
        return 'Сетка уже пуста.';
      }

      return `Будут удалены все ${count} ед. оборудования из текущей схемы.`;
    },

    landmarkValues() {
      return normalizeLandmarks(this.landmarks);
    },

    notify()
    {
      return useNotificationsStore()
    },

    audienceContext()
    {
      return useAudienceContext()
    },

    authStore()
    {
      return useAuthStore()
    }
  },

  methods: {
    getEquipmentIdentity(item) {
      return item?.localId ?? item?.dbId ?? null;
    },

    isEquipmentDeleting(item) {
      const id = this.getEquipmentIdentity(item);
      return id !== null && this.deletingEquipmentIds.includes(id);
    },

    getEquipmentSnapParticles(item) {
      const id = this.getEquipmentIdentity(item);
      return id === null ? [] : this.snapParticlesByEquipmentId[String(id)] ?? [];
    },

    createEquipmentSnapParticles(item) {
      const id = this.getEquipmentIdentity(item);
      if (id === null || prefersReducedMotion()) return;

      const iconColors = extractSolidColors(this.equipmentTypeMap[item.type]?.color);
      const isDark = document.documentElement.dataset.theme === 'dark';
      const surfaceColors = item.state === false
          ? (isDark
              ? ['#3b1218', '#7f1d1d', '#fb7185', '#fecdd3']
              : ['#fef2f2', '#fee2e2', '#f87171', '#991b1b'])
          : (isDark
              ? ['#0b1220', '#111827', '#334155', '#cbd5e1']
              : ['#ffffff', '#f8fafc', '#cbd5e1', '#475569']);
      const palette = [
        ...surfaceColors,
        ...surfaceColors,
        ...(iconColors.length ? iconColors : ['#60a5fa']),
      ];
      const width = item.width ?? 1;
      const height = item.height ?? 1;
      const count = Math.min(
          EQUIPMENT_SNAP_MAX_PARTICLES,
          Math.max(EQUIPMENT_SNAP_MIN_PARTICLES, 120 + width * height * 22)
      );

      const particles = Array.from({ length: count }, (_, index) => {
        const x = 1 + Math.random() * 98;
        const y = 1 + Math.random() * 98;
        const waveDelay = (1 - x / 100) * 310 + Math.random() * 55;
        const tx = -32 + Math.random() * 104;
        const ty = -(58 + Math.random() * 112);
        const midTx = tx * 0.36 + (Math.random() - 0.5) * 22;
        const midTy = ty * 0.32 - 8 - Math.random() * 18;
        const lateTx = tx * 0.75 + (Math.random() - 0.5) * 16;
        const lateTy = ty * 0.72 - Math.random() * 12;
        const kindRoll = Math.random();
        const kind = kindRoll < 0.62 ? 'dust' : kindRoll < 0.93 ? 'shard' : 'spark';
        const sizeRoll = Math.random();
        const size = sizeRoll < 0.72
            ? 1 + Math.random() * 2
            : sizeRoll < 0.95
                ? 2.5 + Math.random() * 2
                : 4.5 + Math.random() * 1.5;
        const duration = 760 + Math.random() * 300;
        const rotate = -260 + Math.random() * 520;
        const particleWidth = kind === 'shard'
            ? size * (0.8 + Math.random() * 1.35)
            : size;
        const clip = kind === 'shard'
            ? (Math.random() > 0.5
                ? 'polygon(15% 0, 100% 22%, 72% 100%, 0 74%)'
                : 'polygon(34% 0, 100% 48%, 58% 100%, 0 63%)')
            : 'none';

        return {
          id: `${id}-${index}`,
          kind,
          style: {
            '--snap-x': `${x}%`,
            '--snap-y': `${y}%`,
            '--snap-tx': `${tx}px`,
            '--snap-ty': `${ty}px`,
            '--snap-mid-tx': `${midTx}px`,
            '--snap-mid-ty': `${midTy}px`,
            '--snap-late-tx': `${lateTx}px`,
            '--snap-late-ty': `${lateTy}px`,
            '--snap-size': `${size}px`,
            '--snap-width': `${particleWidth}px`,
            '--snap-delay': `${waveDelay}ms`,
            '--snap-duration': `${duration}ms`,
            '--snap-rotate': `${rotate}deg`,
            '--snap-mid-rotate': `${rotate * 0.42}deg`,
            '--snap-late-rotate': `${rotate * 0.78}deg`,
            '--snap-clip': clip,
            '--snap-color': palette[Math.floor(Math.random() * palette.length)],
          },
        };
      });

      this.snapParticlesByEquipmentId = {
        ...this.snapParticlesByEquipmentId,
        [String(id)]: particles,
      };
    },

    clearEquipmentSnapParticles(id) {
      const next = { ...this.snapParticlesByEquipmentId };
      delete next[String(id)];
      this.snapParticlesByEquipmentId = next;
    },

    clearEquipmentRemovalTimers() {
      Object.values(this.equipmentRemovalTimers).forEach(timerId => {
        clearTimeout(timerId);
      });

      this.equipmentRemovalTimers = {};
      this.deletingEquipmentIds = [];
      this.snapParticlesByEquipmentId = {};
    },

    selectEquipment(id)
    {
      if(this.selectedEquipmentId !== null && this.selectedEquipmentId === id)
        this.selectedEquipmentId = null
      else
        this.selectedEquipmentId = id;
    },

    // Обработка клика (если выбран инструмент)
    handleCellClick(row, col) {
      if (this.suppressNextCellClick) {
        this.suppressNextCellClick = false;
        return;
      }

      if (!this.selectedEquipmentId) return;

      const width = this.selectedEquipmentSize.width;
      const height = this.selectedEquipmentSize.height;

      const { row: targetRow, col: targetCol } = this.resolveDropAnchorPosition(
          row,
          col,
          width,
          height
      );

      this.placeEquipment(
          targetRow,
          targetCol,
          this.selectedEquipmentId,
          width,
          height
      );
    },

    canPlace(candidate, ignoreId = null) {
      if (candidate.x < 0 || candidate.y < 0) return false;
      if (candidate.x + candidate.width > this.gridWidth) return false;
      if (candidate.y + candidate.height > this.gridHeight) return false;

      return !this.equipmentItems.some(item => {
        const itemId = item.localId ?? item.dbId;
        if (itemId === ignoreId) return false;

        return !(
            candidate.x + candidate.width <= item.x ||
            item.x + item.width <= candidate.x ||
            candidate.y + candidate.height <= item.y ||
            item.y + item.height <= candidate.y
        );
      });
    },

    // Drag & Drop
    onDragStart(event, eq) {
      const payload = {
        mode: 'new',
        equipmentType: eq.id,
        width: this.selectedEquipmentSize.width,
        height: this.selectedEquipmentSize.height,
      };

      event.dataTransfer.effectAllowed = 'copy';
      event.dataTransfer.setData('application/json', JSON.stringify(payload));
      event.target.classList.add('dragging');
    },

    // Обработка начала перетаскивания из сетки
    onGridItemDragStart(event, item) {
      const payload = {
        mode: 'move',
        itemId: item.localId ?? item.dbId,
      };

      this.draggedEquipmentId = item.localId ?? item.dbId;

      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('application/json', JSON.stringify(payload));
    },

    onDragEnd(event) {
      event?.target?.classList?.remove('dragging');
      this.dragOverCell = null;
      this.draggedEquipmentId = null;
    },

    onDragOver(row, col) {
      this.dragOverCell = { row, col };
    },

    onDragLeave() {
      this.dragOverCell = null;
    },

    isDragOver(row, col) {
      return this.dragOverCell?.row === row && this.dragOverCell?.col === col;
    },

    onDrop(row, col, event) {
      event.preventDefault();
      event.stopPropagation();
      this.suppressNextCellClick = true;

      try {
        const raw = event.dataTransfer.getData('application/json');
        if (!raw) return;

        const payload = JSON.parse(raw);

        if (payload.mode === 'new') {
          const width = payload.width ?? 1;
          const height = payload.height ?? 1;

          const { row: targetRow, col: targetCol } = this.resolveDropAnchorPosition(
              row,
              col,
              width,
              height
          );

          this.placeEquipment(
              targetRow,
              targetCol,
              payload.equipmentType,
              width,
              height
          );
          return;
        }

        if (payload.mode === 'move') {
          const item = this.equipmentItems.find(
              eq => (eq.localId ?? eq.dbId) === payload.itemId
          );
          if (!item) return;

          const { row: targetRow, col: targetCol } = this.resolveDropAnchorPosition(
              row,
              col,
              item.width ?? 1,
              item.height ?? 1
          );

          this.moveEquipment(item, targetRow, targetCol);
        }
      } finally {
        this.dragOverCell = null;
        this.draggedEquipmentId = null;

        setTimeout(() => {
          this.suppressNextCellClick = false;
        }, 30);
      }
    },

    // Логика перемещения оборудования
    moveEquipment(item, toRow, toCol) {
      const id = item.localId ?? item.dbId;

      const updated = {
        ...item,
        x: toCol,
        y: toRow,
      };

      if (!this.canPlace(updated, id)) {
        this.notify.warning('Нельзя переместить оборудование в эту позицию');
        return;
      }

      this.equipmentItems = this.equipmentItems.map(eq =>
          (eq.localId ?? eq.dbId) === id ? updated : eq
      );
    },

    placeEquipment(row, col, equipmentType, width = 1, height = 1) {
      const item = {
        localId: crypto.randomUUID(),
        dbId: null,
        type: equipmentType,
        x: col,
        y: row,
        width,
        height,
        state: true,
        description: null,
        inv_number: null,
        title: null,
        specs: {},
        files: []
      };

      if (!this.canPlace(item, item.localId)) {
        this.notify.warning('Оборудование не помещается или пересекается');
        return;
      }

      this.equipmentItems = [...this.equipmentItems, item];
    },

    removeEquipment(item) {
      const id = this.getEquipmentIdentity(item);
      if (id === null || this.deletingEquipmentIds.includes(id)) return;

      this.createEquipmentSnapParticles(item);
      this.deletingEquipmentIds = [...this.deletingEquipmentIds, id];

      const removalDelay = prefersReducedMotion() ? 180 : EQUIPMENT_SNAP_DURATION_MS;
      this.equipmentRemovalTimers[id] = setTimeout(() => {
        this.equipmentItems = this.equipmentItems.filter(
            eq => this.getEquipmentIdentity(eq) !== id
        );
        this.deletingEquipmentIds = this.deletingEquipmentIds.filter(itemId => itemId !== id);
        this.clearEquipmentSnapParticles(id);
        delete this.equipmentRemovalTimers[id];
      }, removalDelay);
    },

    resolveDropAnchorPosition(row, col, width = 1, height = 1) {
      return {
        row: row - (height - 1),
        col: col - (width - 1),
      };
    },

    clearGrid() {
      if (!this.canClearGrid) {
        return;
      }

      this.clearGridClicked = !this.clearGridClicked;
    },

    cancelClearGrid() {
      this.clearGridClicked = false;
    },

    confirmClearGrid() {
      if (!this.canClearGrid) {
        this.clearGridClicked = false;
        return;
      }

      this.clearEquipmentRemovalTimers();
      this.equipmentItems = [];
      this.clearGridClicked = false;
    },

    getLandmarkLabel(direction) {
      return LANDMARK_LABELS[direction] ?? direction;
    },

    getLandmarkDisplayValue(direction) {
      return this.landmarkValues[direction] || this.getLandmarkLabel(direction);
    },

    isLandmarkPlaceholder(direction) {
      return !this.landmarkValues[direction];
    },

    openLandmarkEditor(direction) {
      this.editingLandmark = direction;
      this.landmarkDraft = this.landmarkValues[direction];
    },

    closeLandmarkEditor() {
      this.editingLandmark = null;
      this.landmarkDraft = '';
    },

    saveLandmarkDraft() {
      if (!this.editingLandmark) {
        return;
      }

      this.landmarks = {
        ...this.landmarks,
        [this.editingLandmark]: String(this.landmarkDraft ?? '').trim(),
      };

      this.closeLandmarkEditor();
    },

    buildGridExportFileName() {
      const audience = sanitizeFileNamePart(this.classroomNumber, 'new');
      const floor = sanitizeFileNamePart(this.floorNumber, '1');
      const office = sanitizeFileNamePart(this.officeNumber, '1');

      return `Audience_${audience}_floor_${floor}_office_${office}.json`;
    },

    buildGridExportPayload() {
      return {
        schema: 'bgitu-audience-grid',
        version: 1,
        grid: {
          width: Number(this.gridWidth),
          height: Number(this.gridHeight),
          landmarks: normalizeLandmarks(this.landmarks),
        },
        hardware: this.equipmentItems
            .filter(item => !this.isEquipmentDeleting(item))
            .map(item => ({
              type: item.type,
              x: Number(item.x),
              y: Number(item.y),
              width: Number(item.width ?? 1),
              height: Number(item.height ?? 1),
              state: item.state ?? true,
              description: normalizeNullableString(item.description),
              inv_number: normalizeNullableString(item.inv_number),
              title: normalizeNullableString(item.title),
              specs: cloneJsonObject(item.specs),
            })),
      };
    },

    async exportGridToJson() {
      const payload = this.buildGridExportPayload();
      const fileName = this.buildGridExportFileName();
      const blob = new Blob([JSON.stringify(payload, null, 2)], {
        type: 'application/json;charset=utf-8',
      });

      if (window.isSecureContext && 'showSaveFilePicker' in window) {
        try {
          const handle = await window.showSaveFilePicker({
            suggestedName: fileName,
            types: [
              {
                description: 'JSON файл сетки аудитории',
                accept: { 'application/json': ['.json'] },
              },
            ],
          });
          const writable = await handle.createWritable();

          await writable.write(blob);
          await writable.close();
          return;
        } catch (error) {
          if (error?.name === 'AbortError') {
            return;
          }
        }
      }

      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');

      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 0);
    },

    triggerGridJsonImport() {
      this.$refs.gridJsonInput?.click();
    },

    normalizeImportedPositiveInteger(value) {
      const number = Number(value);

      if (!Number.isInteger(number) || number < 1) {
        throw new Error('Invalid grid value');
      }

      return number;
    },

    normalizeImportedCoordinate(value) {
      const number = Number(value);

      if (!Number.isInteger(number) || number < 0) {
        throw new Error('Invalid hardware coordinate');
      }

      return number;
    },

    parseImportedGridJson(data) {
      if (!isPlainObject(data)) {
        throw new Error('Invalid file');
      }

      if (data.schema !== undefined && data.schema !== 'bgitu-audience-grid') {
        throw new Error('Invalid schema');
      }

      const gridSource = isPlainObject(data.grid) ? data.grid : data;
      const gridWidth = this.normalizeImportedPositiveInteger(gridSource.width ?? data.gridWidth);
      const gridHeight = this.normalizeImportedPositiveInteger(gridSource.height ?? data.gridHeight);
      const rawHardware = Array.isArray(data.hardware)
          ? data.hardware
          : Array.isArray(data.equipment)
              ? data.equipment
              : null;

      if (!rawHardware) {
        throw new Error('Invalid hardware');
      }

      const occupied = new Set();
      const hardware = rawHardware.map((item, index) => {
        if (!isPlainObject(item)) {
          throw new Error('Invalid hardware item');
        }

        const type = String(item.type ?? '').trim();
        if (!this.equipmentTypeMap[type]) {
          throw new Error('Invalid hardware type');
        }

        const x = this.normalizeImportedCoordinate(item.x);
        const y = this.normalizeImportedCoordinate(item.y);
        const width = this.normalizeImportedPositiveInteger(item.width ?? 1);
        const height = this.normalizeImportedPositiveInteger(item.height ?? 1);

        if (x + width > gridWidth || y + height > gridHeight) {
          throw new Error('Hardware out of grid');
        }

        for (let row = y; row < y + height; row += 1) {
          for (let col = x; col < x + width; col += 1) {
            const key = `${row}:${col}`;
            if (occupied.has(key)) {
              throw new Error('Hardware overlaps');
            }
            occupied.add(key);
          }
        }

        if (item.state !== undefined && item.state !== null && typeof item.state !== 'boolean') {
          throw new Error('Invalid hardware state');
        }

        if (item.specs !== undefined && item.specs !== null && !isPlainObject(item.specs)) {
          throw new Error('Invalid hardware specs');
        }

        return {
          localId: `import-${index}-${crypto.randomUUID()}`,
          dbId: null,
          type,
          x,
          y,
          width,
          height,
          state: item.state ?? true,
          description: normalizeNullableString(item.description),
          inv_number: normalizeNullableString(item.inv_number ?? item.invNumber),
          title: normalizeNullableString(item.title),
          specs: cloneJsonObject(item.specs),
          files: [],
        };
      });

      return {
        gridWidth,
        gridHeight,
        landmarks: normalizeLandmarks(gridSource.landmarks ?? data.landmarks),
        hardware,
      };
    },

    async importGridFromJson(event) {
      const input = event.target;
      const file = input.files?.[0];

      if (!file) return;

      try {
        const data = JSON.parse(await file.text());
        const imported = this.parseImportedGridJson(data);

        this.clearEquipmentRemovalTimers();
        this.isApplyingHistory = true;
        this.gridWidth = imported.gridWidth;
        this.gridHeight = imported.gridHeight;
        this.landmarks = imported.landmarks;
        this.equipmentItems = imported.hardware;
        this.clearGridClicked = false;
        this.closeLandmarkEditor();

        this.$nextTick(() => {
          this.isApplyingHistory = false;
          this.recomputeUnsavedChanges();
        });

        this.notify.success('Сетка загружена из JSON');
      } catch {
        this.notify.error('Вы выбрали не тот файл');
      } finally {
        input.value = '';
      }
    },

    toggleGridActionsMenu() {
      this.isGridActionsOpen = !this.isGridActionsOpen;
    },

    closeGridActionsMenu() {
      this.isGridActionsOpen = false;
    },

    handleGridActionsOutsideClick(event) {
      if (!this.isGridActionsOpen) return;

      const menu = this.$refs.gridActionsMenu;
      if (menu && !menu.contains(event.target)) {
        this.closeGridActionsMenu();
      }
    },

    async handleGridMenuExport() {
      await this.exportGridToJson();
      this.closeGridActionsMenu();
    },

    handleGridMenuImport() {
      this.closeGridActionsMenu();
      this.triggerGridJsonImport();
    },

    handleGridMenuUndo() {
      this.undoAudienceChange();
      this.closeGridActionsMenu();
    },

    handleGridMenuRedo() {
      this.redoAudienceChange();
      this.closeGridActionsMenu();
    },

    handleGridMenuClear() {
      this.clearGrid();
      this.closeGridActionsMenu();
    },

    isEditableShortcutTarget(target) {
      if (!(target instanceof HTMLElement)) return false;

      const tagName = target.tagName.toLowerCase();
      return target.isContentEditable || ['input', 'textarea', 'select'].includes(tagName);
    },

    handleAudienceKeyboardShortcuts(event) {
      if (event.key === 'Escape' && this.isGridActionsOpen) {
        this.closeGridActionsMenu();
        return;
      }

      if (!(event.ctrlKey || event.metaKey) || event.altKey || this.isEditableShortcutTarget(event.target)) {
        return;
      }

      const isZKey = event.code === 'KeyZ';
      const isUndo = isZKey && !event.shiftKey;
      const isRedo = isZKey && event.shiftKey;

      if (isUndo && this.canUndo) {
        event.preventDefault();
        this.undoAudienceChange();
        return;
      }

      if (isRedo && this.canRedo) {
        event.preventDefault();
        this.redoAudienceChange();
      }
    },

    buildAudienceSnapshot() {
      const normalizedItems = [...this.equipmentItems]
          .map(item => ({
            id: item.dbId || null,
            type: item.type,
            x: item.x,
            y: item.y,
            width: item.width,
            height: item.height,
            state: item.state ?? true,
            description: item.description ?? null,
            inv_number: item.inv_number ?? null,
            title: item.title ?? null,
            specs: item.specs ?? {},
          }))
          .sort((a, b) => {
            const aKey = `${a.id ?? 'new'}-${a.x}-${a.y}-${a.type}`;
            const bKey = `${b.id ?? 'new'}-${b.x}-${b.y}-${b.type}`;
            return aKey.localeCompare(bKey);
          });

      return JSON.stringify({
        classroomNumber: this.classroomNumber ?? null,
        floorNumber: this.floorNumber,
        officeNumber: this.officeNumber,
        gridWidth: this.gridWidth,
        gridHeight: this.gridHeight,
        landmarks: normalizeLandmarks(this.landmarks),
        hardware: normalizedItems,
      });
    },

    captureInitialSnapshot() {
      this.initialSnapshot = this.buildAudienceSnapshot();
      this.hasUnsavedChanges = false;
      this.resetHistory(this.initialSnapshot);
    },

    resetHistory(snapshot = this.buildAudienceSnapshot()) {
      this.historySnapshots = [snapshot];
      this.historyIndex = 0;
    },

    rememberHistoryStep() {
      if (this.isHydrating || this.isApplyingHistory) return;

      const snapshot = this.buildAudienceSnapshot();
      const currentSnapshot = this.historySnapshots[this.historyIndex];

      if (snapshot === currentSnapshot) {
        return;
      }

      let nextSnapshots = this.historySnapshots.slice(0, this.historyIndex + 1);
      nextSnapshots.push(snapshot);

      if (nextSnapshots.length > HISTORY_LIMIT) {
        nextSnapshots = nextSnapshots.slice(nextSnapshots.length - HISTORY_LIMIT);
      }

      this.historySnapshots = nextSnapshots;
      this.historyIndex = nextSnapshots.length - 1;
    },

    applyAudienceSnapshot(snapshot) {
      if (!snapshot) return;

      let data;
      try {
        data = JSON.parse(snapshot);
      } catch {
        this.notify.error('Не удалось восстановить шаг истории');
        return;
      }

      this.clearEquipmentRemovalTimers();
      this.isApplyingHistory = true;
      this.classroomNumber = data.classroomNumber ?? null;
      this.floorNumber = Number(data.floorNumber ?? 1);
      this.officeNumber = Number(data.officeNumber ?? 1);
      this.gridWidth = Number(data.gridWidth ?? 1);
      this.gridHeight = Number(data.gridHeight ?? 1);
      this.landmarks = normalizeLandmarks(data.landmarks);
      this.equipmentItems = (data.hardware ?? []).map((item, index) => ({
        localId: item.id ? `db-${item.id}` : `history-${index}-${crypto.randomUUID()}`,
        dbId: item.id || null,
        type: item.type,
        x: item.x,
        y: item.y,
        width: item.width ?? 1,
        height: item.height ?? 1,
        state: item.state ?? true,
        description: item.description ?? null,
        inv_number: item.inv_number ?? null,
        title: item.title ?? null,
        specs: item.specs ?? {},
        files: []
      }));

      this.clearGridClicked = false;
      this.closeLandmarkEditor();

      this.$nextTick(() => {
        this.isApplyingHistory = false;
        this.recomputeUnsavedChanges();
        this.updatePageTitle();
      });
    },

    undoAudienceChange() {
      if (!this.canUndo) return;

      this.historyIndex -= 1;
      this.applyAudienceSnapshot(this.historySnapshots[this.historyIndex]);
    },

    redoAudienceChange() {
      if (!this.canRedo) return;

      this.historyIndex += 1;
      this.applyAudienceSnapshot(this.historySnapshots[this.historyIndex]);
    },

    hasAudienceChanges() {
      return this.buildAudienceSnapshot() !== this.initialSnapshot;
    },

    recomputeUnsavedChanges() {
      if (this.isHydrating) return;
      this.hasUnsavedChanges = this.hasAudienceChanges();
      this.rememberHistoryStep();
    },

    async getOffices()
    {
      await api.get(`/offices/all_short`).then(response => {
        this.offices_ids = Object.values(response.data).map(item => item.id);
      })
    },

    async loadAudienceData() {
      this.loading = true;
      this.isHydrating = true;
      try {
        const res = await api.get(`/audiences/${this.publicId}`);
        const data = res.data;

        this.classroomNumber = String(data.number ?? data.id);
        this.updatePageTitle();
        this.floorNumber = data.floor;
        this.officeNumber = data.office_id;
        this.gridWidth = data.width;
        this.gridHeight = data.height;
        this.landmarks = normalizeLandmarks(data.landmarks);

        this.equipmentItems = (data.hardware ?? []).map(hw => ({
          localId: `db-${hw.id}`,
          dbId: hw.id,
          type: hw.type,
          x: hw.x,
          y: hw.y,
          width: hw.width ?? 1,
          height: hw.height ?? 1,
          state: hw.state,
          description: hw.description ?? null,
          inv_number: hw.inv_number ?? null,
          title: hw.title ?? null,
          specs: hw.specs ?? {},
          files: hw.files ?? []
        }));
        this.closeLandmarkEditor();

        await this.$nextTick(() => {
          this.captureInitialSnapshot();
          this.isHydrating = false;
        });
      } catch (e) {
        this.isHydrating = false;
        this.notify.error("Не удалось загрузить данные аудитории");
        await router.push('/');
      } finally {
        this.loading = false;
      }
    },

    getEquipmentStyle(item) {
      return {
        gridColumn: `${item.x + 1} / span ${item.width}`,
        gridRow: `${item.y + 1} / span ${item.height}`,
      };
    },

    mapFrontendToBackend(items) {
      return items.map(item => ({
        id: item.dbId || null,
        type: item.type,
        x: item.x,
        y: item.y,
        width: item.width,
        height: item.height,
        state: item.state ?? true,
        description: item.description ?? null,
        inv_number: item.inv_number ?? null,
        title: item.title ?? null,
        specs: item.specs ?? {}
      }));
    },

    saveClassroom() {
      if (!this.classroomNumber) {
        this.notify.warning('Введите номер аудитории!');
        return;
      }

      if (this.isEditMode && !this.hasAudienceChanges()) {
        this.hasUnsavedChanges = false;
        this.notify.info('Изменений нет, аудитория не отправлялась на сервер');
        return;
      }

      const outOfBoundsItems = this.outOfBoundsEquipmentItems

      if (outOfBoundsItems.length > 0) {
        const confirmMsg =
            `Внимание! Вы уменьшили размеры сетки.\n` +
            `${outOfBoundsItems.length} ед. оборудования окажутся за пределами и будут удалены.\n\n` +
            `Продолжить?`;

        if (!confirm(confirmMsg)) {
          return;
        }
      }

      const validItems = this.equipmentItems.filter(item =>
          item.x >= 0 &&
          item.y >= 0 &&
          item.x + item.width <= this.gridWidth &&
          item.y + item.height <= this.gridHeight
      );

      if (validItems.length === 0) {
        this.notify.warning('Добавьте хотя бы одно оборудование!');
        return;
      }

      const classroomData = {
        number: Number(this.classroomNumber),
        floor: this.floorNumber,
        width: this.gridWidth,
        height: this.gridHeight,
        hardware: this.mapFrontendToBackend(validItems),
        office_id: this.officeNumber,
        landmarks: buildLandmarksPayload(this.landmarks)
      };

      if (this.isEditMode) {
        api.put(`/audiences/${this.publicId}`, classroomData)
            .then(() => {
              this.notify.success(`Аудитория обновлена!`);
              this.audienceContext.setOffice(classroomData.office_id);
              this.hasUnsavedChanges = false;
              router.push({ name: "Audience", params: { audiencePublicId: this.publicId } });
            })
            .catch(err => {
              this.notify.error(`Ошибка обновления: ${err.response?.data?.detail || ''}`);
            });
      } else {
        api.post(`/audiences`, classroomData)
            .then((response) => {
              const createdPublicId = response.data?.public_id;
              if (!createdPublicId) {
                this.notify.error(`Аудитория создана, но сервер не вернул UUID для перехода.`);
                return;
              }
              this.notify.success(`Аудитория создана!`);
              this.hasUnsavedChanges = false;
              router.push({ name: "Audience", params: { audiencePublicId: createdPublicId } });
            })
            .catch(err => {
              if (err.response?.status === 409) {
                this.notify.error(`В выбранном корпусе уже есть аудитория с таким номером!`);
              } else {
                this.notify.error(`Не удалось создать аудиторию!`);
              }
            });
      }
    },

    goBack() {
      router.go(-1)
    },

    openUnsavedLeaveModal(target, mode = 'push') {
      this.pendingLeaveTarget = target || '';
      this.pendingLeaveMode = mode;
      this.showUnsavedLeaveModal = true;
    },

    closeUnsavedLeaveModal() {
      this.showUnsavedLeaveModal = false;
      this.pendingLeaveTarget = '';
      this.pendingLeaveMode = 'push';
    },

    async confirmUnsavedLeave() {
      const target = this.pendingLeaveTarget;
      const mode = this.pendingLeaveMode;

      this.showUnsavedLeaveModal = false;
      this.pendingLeaveTarget = '';
      this.pendingLeaveMode = 'push';

      if (!target) {
        return;
      }

      this.bypassUnsavedLeaveGuard = true;

      try {
        if (mode === 'back') {
          this.$router.go(-1);
          return;
        }

        if (mode === 'forward') {
          this.$router.go(1);
          return;
        }

        await this.$router.push(target);
      } catch {
        this.bypassUnsavedLeaveGuard = false;
      }
    },

    classroomNumberFilter() {

      if (!/^\d*[1-9]\d*$/.test(this.classroomNumber) || this.classroomNumber.length > 3)
        this.classroomNumber = this.classroomNumber.slice(0, -1);
    },

    updatePageTitle() {
      if (this.isEditMode && this.classroomNumber) {
        document.title = `Редактирование аудитории №${this.classroomNumber}`;
        return;
      }

      document.title = this.isEditMode ? 'Редактирование аудитории' : 'Создание аудитории';
    },
  },

  watch: {
    equipmentItems: {
      handler() {
        this.clearGridClicked = false;
        this.recomputeUnsavedChanges();
      },
      deep: true
    },

    gridWidth() {
      this.recomputeUnsavedChanges();
    },

    gridHeight() {
      this.recomputeUnsavedChanges();
    },

    floorNumber() {
      this.recomputeUnsavedChanges();
    },

    officeNumber() {
      this.recomputeUnsavedChanges();
    },

    landmarks: {
      handler() {
        this.recomputeUnsavedChanges();
      },
      deep: true
    },

    classroomNumber() {
      this.recomputeUnsavedChanges();
      this.updatePageTitle();
    }
  },

  mounted()
  {
    this.isHydrating = true;
    this.updatePageTitle();
    document.addEventListener('pointerdown', this.handleGridActionsOutsideClick);
    window.addEventListener('keydown', this.handleAudienceKeyboardShortcuts);
    const officeIdFromQuery = Number(this.$route.query.office_id);
    if (!this.isEditMode && Number.isInteger(officeIdFromQuery) && officeIdFromQuery > 0) {
      this.officeNumber = officeIdFromQuery;
    }

    this.getOffices();
    if (this.publicId)
    {
      this.loadAudienceData();
    } else {
      this.$nextTick(() => {
        this.captureInitialSnapshot();
        this.isHydrating = false;
      });
    }
  },

  beforeUnmount()
  {
    document.removeEventListener('pointerdown', this.handleGridActionsOutsideClick);
    window.removeEventListener('keydown', this.handleAudienceKeyboardShortcuts);
    this.clearEquipmentRemovalTimers();
  },

  beforeRouteLeave(to, from, next)
  {
    if (this.bypassUnsavedLeaveGuard)
    {
      next();
      return;
    }

    if (this.hasUnsavedChanges && !this.authStore.isLoggingOut)
    {
      const historyState = window.history.state ?? {};
      const leaveMode = historyState.back === to.fullPath
          ? 'back'
          : historyState.forward === to.fullPath
              ? 'forward'
              : 'push';

      this.openUnsavedLeaveModal(to.fullPath, leaveMode);
      next(false);
    }
    else
    {
      next();
    }
  }

};
</script>

<template>
  <div class="page-wrapper create-audience-page" :class="{ 'is-edit-mode': isEditMode }">
    <div class="container">
      <div class="header">
        <button class="back-btn" @click="goBack">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          Назад
        </button>
        <h1 class="page-title">{{ pageTitle }}</h1>
        <div class="header-spacer"></div>
      </div>

      <div class="main-layout">
        <div class="left-panel">

          <div class="panel" :class="{collapsed: paramsCollapsed}">

            <div class="panel-header">
              <h3 class="panel-title panel-title-tight">Параметры аудитории</h3>
              <div @click="paramsCollapsed = !paramsCollapsed" class="collapse-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M6 9l6 6 6-6"/>
                </svg>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">Номер аудитории</label>
              <input
                  type="text"
                  class="form-input"
                  v-model="classroomNumber"
                  placeholder="Например: 105"
                  @input="classroomNumberFilter"
                  :disabled="isEditMode"
              >
            </div>

            <div class="form-group">
              <label class="form-label">Корпус</label>
              <div class="select-field">
                <select class="form-select" v-model.number="officeNumber">
                  <option v-for="office in offices_ids" :value="office">Корпус {{ office }}</option>
                </select>
                <svg class="select-field-arrow" viewBox="0 0 12 8" aria-hidden="true">
                  <path d="M1 1l5 5 5-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">Этаж</label>
              <input
                  type="number"
                  class="form-input"
                  v-model.number="floorNumber"
                  min="1" max="9"
              >
            </div>

            <div class="form-group">
              <label class="form-label">Размер сетки</label>
              <div class="grid-size-inputs">
                <div>
                  <input
                      type="number"
                      class="form-input"
                      v-model.number="gridWidth"
                      min="1" max="20"
                      placeholder="Ширина"
                  >
                </div>
                <div>
                  <input
                      type="number"
                      class="form-input"
                      v-model.number="gridHeight"
                      min="1" max="20"
                      placeholder="Высота"
                  >
                </div>
              </div>
            </div>
          </div>

          <div class="panel">
            <h3 class="panel-title">Оборудование</h3>
            <p class="panel-hint">
              Выберите и перетащите в сетку или кликните на клетку
            </p>

            <div class="size-picker">
              <button
                  type="button"
                  class="size-btn"
                  :class="{ active: selectedEquipmentSize.width === 1 && selectedEquipmentSize.height === 1 }"
                  @click="selectedEquipmentSize = { width: 1, height: 1 }"
              >
                1×1
              </button>

              <button
                  type="button"
                  class="size-btn"
                  :class="{ active: selectedEquipmentSize.width === 2 && selectedEquipmentSize.height === 1 }"
                  @click="selectedEquipmentSize = { width: 2, height: 1 }"
              >
                2×1
              </button>

              <button
                  type="button"
                  class="size-btn"
                  :class="{ active: selectedEquipmentSize.width === 1 && selectedEquipmentSize.height === 2 }"
                  @click="selectedEquipmentSize = { width: 1, height: 2 }"
              >
                1×2
              </button>
            </div>

            <div class="equipment-palette">
              <div
                  v-for="eq in equipmentTypes"
                  :key="eq.id"
                  class="equipment-item"
                  :class="{ selected: selectedEquipmentId === eq.id }"
                  draggable="true"
                  @click="selectEquipment(eq.id)"
                  @dragstart="onDragStart($event, eq)"
                  @dragend="onDragEnd"
              >
                <div class="equipment-icon" :style="{ background: eq.color }">
                  <TrustedSvgIcon :svg="eq.icon" />
                </div>
                <div class="equipment-name">{{ eq.name }}</div>
              </div>
            </div>
          </div>

          <div class="panel">
            <h3 class="panel-title">Статистика</h3>
            <div class="stats-panel">
              <div class="stat-item">
                <span class="stat-label">Всего оборудования:</span>
                <span class="stat-value">{{ stats.total }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Компьютеров:</span>
                <span class="stat-value">{{ stats.computer }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Серверов:</span>
                <span class="stat-value">{{ stats.server }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Телевизоров:</span>
                <span class="stat-value">{{ stats.tv }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Проекторов:</span>
                <span class="stat-value">{{ stats.projector }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Принтеров:</span>
                <span class="stat-value">{{ stats.printer }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Сетевого оборудования:</span>
                <span class="stat-value">{{ stats.network }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="grid-panel">
          <div class="grid-header">
            <div>
              <h3 class="panel-title panel-title-no-margin">Расстановка оборудования</h3>
              <p class="grid-info">Сетка {{ gridWidth }}×{{ gridHeight }}</p>
            </div>
            <div class="grid-header-actions">
              <div class="grid-action-cluster">
                <div ref="gridActionsMenu" class="grid-actions-menu">
                  <button
                      type="button"
                      class="grid-actions-trigger"
                      :class="{ active: isGridActionsOpen }"
                      :aria-expanded="String(isGridActionsOpen)"
                      aria-haspopup="menu"
                      title="Действия с сеткой"
                      @click.stop="toggleGridActionsMenu"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="3"/>
                      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06A1.65 1.65 0 0 0 15 19.4a1.65 1.65 0 0 0-1 .6 1.65 1.65 0 0 0-.33 1.02V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-.6-1 1.65 1.65 0 0 0-1.02-.33H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-.6 1.65 1.65 0 0 0 .33-1.02V3a2 2 0 0 1 4 0v.09A1.65 1.65 0 0 0 15 4.6a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.14.34.34.65.6 1 .28.26.64.4 1.02.4H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51.6Z"/>
                    </svg>
                    Действия
                  </button>

                  <transition name="grid-actions-dropdown">
                    <div
                        v-if="isGridActionsOpen"
                        class="grid-actions-dropdown"
                        role="menu"
                        @click.stop
                    >
                      <button
                          type="button"
                          class="grid-action-menu-item"
                          :disabled="!canUndo"
                          role="menuitem"
                          @click="handleGridMenuUndo"
                      >
                        <span class="grid-action-menu-icon">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M9 14 4 9l5-5"/>
                            <path d="M4 9h10a6 6 0 0 1 0 12h-3"/>
                          </svg>
                        </span>
                        <span class="grid-action-menu-copy">
                          <span class="grid-action-menu-title">Отменить</span>
                          <span class="grid-action-menu-hint">Ctrl+Z</span>
                        </span>
                      </button>
                      <button
                          type="button"
                          class="grid-action-menu-item"
                          :disabled="!canRedo"
                          role="menuitem"
                          @click="handleGridMenuRedo"
                      >
                        <span class="grid-action-menu-icon">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="m15 14 5-5-5-5"/>
                            <path d="M20 9H10a6 6 0 0 0 0 12h3"/>
                          </svg>
                        </span>
                        <span class="grid-action-menu-copy">
                          <span class="grid-action-menu-title">Повторить</span>
                          <span class="grid-action-menu-hint">Ctrl+Shift+Z</span>
                        </span>
                      </button>

                      <div class="grid-action-divider"></div>

                      <button
                          type="button"
                          class="grid-action-menu-item"
                          role="menuitem"
                          @click="handleGridMenuExport"
                      >
                        <span class="grid-action-menu-icon is-blue">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 3v12"/>
                            <path d="m7 10 5 5 5-5"/>
                            <path d="M5 21h14"/>
                          </svg>
                        </span>
                        <span class="grid-action-menu-copy">
                          <span class="grid-action-menu-title">Выгрузить JSON</span>
                          <span class="grid-action-menu-hint">Сетка и оборудование</span>
                        </span>
                      </button>
                      <button
                          type="button"
                          class="grid-action-menu-item"
                          role="menuitem"
                          @click="handleGridMenuImport"
                      >
                        <span class="grid-action-menu-icon is-blue">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 21V9"/>
                            <path d="m7 14 5-5 5 5"/>
                            <path d="M5 3h14"/>
                          </svg>
                        </span>
                        <span class="grid-action-menu-copy">
                          <span class="grid-action-menu-title">Загрузить JSON</span>
                          <span class="grid-action-menu-hint">Заменит текущую сетку</span>
                        </span>
                      </button>

                      <div class="grid-action-divider"></div>

                      <button
                          type="button"
                          class="grid-action-menu-item is-danger"
                          :disabled="!canClearGrid"
                          role="menuitem"
                          @click="handleGridMenuClear"
                      >
                        <span class="grid-action-menu-icon is-danger">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 6h18"/>
                            <path d="M8 6V4.8c0-.66.54-1.2 1.2-1.2h5.6c.66 0 1.2.54 1.2 1.2V6"/>
                            <path d="M19 6l-1 13.2A2 2 0 0 1 16.01 21H7.99A2 2 0 0 1 6 19.2L5 6"/>
                            <path d="M10 10.5v6"/>
                            <path d="M14 10.5v6"/>
                          </svg>
                        </span>
                        <span class="grid-action-menu-copy">
                          <span class="grid-action-menu-title">Очистить всё</span>
                          <span class="grid-action-menu-hint">Потребуется подтверждение</span>
                        </span>
                      </button>
                    </div>
                  </transition>
                </div>
                <input
                    ref="gridJsonInput"
                    class="grid-json-input"
                    type="file"
                    accept=".json,application/json"
                    @change="importGridFromJson"
                >
                <button
                    type="button"
                    class="btn btn-primary grid-save-btn"
                    :disabled="isSaveDisabled"
                    :title="saveButtonTitle"
                    @click="saveClassroom"
                >
                  {{ isEditMode ? 'Сохранить' : 'Создать' }}
                </button>
              </div>

              <transition name="clear-confirm">
                <div
                    v-if="clearGridClicked"
                    class="clear-grid-confirm"
                    role="alertdialog"
                    aria-live="polite"
                >
                  <div class="clear-grid-confirm-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M3 6h18"/>
                      <path d="M8 6V4.8c0-.66.54-1.2 1.2-1.2h5.6c.66 0 1.2.54 1.2 1.2V6"/>
                      <path d="M19 6l-1 13.2A2 2 0 0 1 16.01 21H7.99A2 2 0 0 1 6 19.2L5 6"/>
                      <path d="M10 10.5v6"/>
                      <path d="M14 10.5v6"/>
                    </svg>
                  </div>

                  <div class="clear-grid-confirm-copy">
                    <div class="clear-grid-confirm-title">Очистить схему аудитории?</div>
                    <div class="clear-grid-confirm-text">{{ clearGridConfirmText }}</div>
                  </div>

                  <div class="clear-grid-confirm-actions">
                    <button
                        type="button"
                        class="btn btn-secondary clear-grid-cancel"
                        @click="cancelClearGrid"
                    >
                      Отмена
                    </button>
                    <button
                        type="button"
                        class="clear-grid-btn is-danger"
                        @click="confirmClearGrid"
                    >
                      Очистить
                    </button>
                  </div>
                </div>
              </transition>
            </div>
          </div>

          <div class="grid-wrapper">
            <div v-if="gridWidth < 1 || gridHeight < 1" class="empty-grid">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
              <div>Задайте размеры сетки</div>
            </div>

            <div v-else class="grid-landmarks-shell">
              <div
                  class="grid-landmark-line is-north"
                  :class="{ placeholder: isLandmarkPlaceholder('north') }"
              >
                <span class="grid-landmark-text">{{ getLandmarkDisplayValue('north') }}</span>
                <button
                    type="button"
                    class="landmark-edit-btn"
                    @click="openLandmarkEditor('north')"
                    aria-label="Редактировать север"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 20h9"/>
                    <path d="M16.5 3.5a2.12 2.12 0 1 1 3 3L7 19l-4 1 1-4z"/>
                  </svg>
                </button>

                <div
                    v-if="editingLandmark === 'north'"
                    class="landmark-editor-popup is-horizontal is-north"
                >
                  <div class="landmark-editor-title">{{ getLandmarkLabel('north') }}</div>
                  <div class="landmark-editor-row">
                    <input
                        v-model.trim="landmarkDraft"
                        type="text"
                        class="landmark-editor-input"
                        :placeholder="getLandmarkLabel('north')"
                        @keydown.enter.prevent="saveLandmarkDraft"
                        @keydown.esc.prevent="closeLandmarkEditor"
                    >
                    <button
                        type="button"
                        class="landmark-editor-action is-confirm"
                        @click="saveLandmarkDraft"
                        aria-label="Сохранить ориентир"
                    >
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 6 9 17l-5-5"/>
                      </svg>
                    </button>
                    <button
                        type="button"
                        class="landmark-editor-action"
                        @click="closeLandmarkEditor"
                        aria-label="Отменить редактирование ориентира"
                    >
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 6 6 18M6 6l12 12"/>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>

              <div class="grid-landmark-main">
                <div class="grid-landmark-side is-west">
                  <div
                      class="grid-landmark-side-stack"
                      :class="{ placeholder: isLandmarkPlaceholder('west') }"
                  >
                    <span class="grid-landmark-side-text">{{ getLandmarkDisplayValue('west') }}</span>
                    <button
                        type="button"
                        class="landmark-edit-btn is-side"
                        @click="openLandmarkEditor('west')"
                        aria-label="Редактировать запад"
                    >
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 20h9"/>
                        <path d="M16.5 3.5a2.12 2.12 0 1 1 3 3L7 19l-4 1 1-4z"/>
                      </svg>
                    </button>
                  </div>

                  <div
                      v-if="editingLandmark === 'west'"
                      class="landmark-editor-popup is-side-popup is-west-popup"
                  >
                    <div class="landmark-editor-title">{{ getLandmarkLabel('west') }}</div>
                    <div class="landmark-editor-row">
                      <input
                          v-model.trim="landmarkDraft"
                          type="text"
                          class="landmark-editor-input"
                          :placeholder="getLandmarkLabel('west')"
                          @keydown.enter.prevent="saveLandmarkDraft"
                          @keydown.esc.prevent="closeLandmarkEditor"
                      >
                      <button
                          type="button"
                          class="landmark-editor-action is-confirm"
                          @click="saveLandmarkDraft"
                          aria-label="Сохранить ориентир"
                      >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M20 6 9 17l-5-5"/>
                        </svg>
                      </button>
                      <button
                          type="button"
                          class="landmark-editor-action"
                          @click="closeLandmarkEditor"
                          aria-label="Отменить редактирование ориентира"
                      >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M18 6 6 18M6 6l12 12"/>
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>

                <div
                    class="grid-container"
                    :class="gridDensityClass"
                    :style="{ '--grid-cols': gridWidth, '--grid-rows': gridHeight }"
                >
                  <div class="grid-base">
                    <template v-for="row in gridHeight" :key="`row-${row}`">
                      <div
                          v-for="col in gridWidth"
                          :key="`cell-${row}-${col}`"
                          class="grid-cell"
                          :class="{ 'drag-over': isDragOver(row - 1, col - 1) }"
                          @click="handleCellClick(row - 1, col - 1)"
                          @dragover.prevent="onDragOver(row - 1, col - 1)"
                          @dragleave="onDragLeave"
                          @drop="onDrop(row - 1, col - 1, $event)"
                      />
                    </template>
                  </div>

                  <div class="grid-overlay">
                    <div
                        v-for="item in visibleEquipmentItems"
                        :key="item.localId || item.dbId"
                        class="grid-equipment"
                        :class="{
                          broken: item.state === false,
                          'is-wide': item.width > item.height,
                          'is-tall': item.height >= item.width,
                          'is-removing': isEquipmentDeleting(item)
                        }"
                        :style="getEquipmentStyle(item)"
                        :draggable="!isEquipmentDeleting(item)"
                        @dragstart.stop="!isEquipmentDeleting(item) && onGridItemDragStart($event, item)"
                        @dragend="onDragEnd"
                    >
                      <div class="equipment-card-content">
                        <div
                            class="cell-icon"
                            :style="{ background: equipmentTypeMap[item.type].color }"
                        >
                          <TrustedSvgIcon :svg="equipmentTypeMap[item.type].icon" />
                        </div>

                        <div class="cell-label">
                          {{ equipmentTypeMap[item.type].name }}
                        </div>

                        <button
                            class="remove-btn"
                            :disabled="isEquipmentDeleting(item)"
                            @click.stop="removeEquipment(item)"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 1024 1024">
                            <path fill="currentColor" fill-rule="evenodd" d="M799.855 166.312c.023.007.043.018.084.059l57.69 57.69c.041.041.052.06.059.084a.118.118 0 0 1 0 .069c-.007.023-.018.042-.059.083L569.926 512l287.703 287.703c.041.04.052.06.059.083a.118.118 0 0 1 0 .07c-.007.022-.018.042-.059.083l-57.69 57.69c-.041.041-.06.052-.084.059a.118.118 0 0 1-.069 0c-.023-.007-.042-.018-.083-.059L512 569.926L224.297 857.629c-.04.041-.06.052-.083.059a.118.118 0 0 1-.07 0c-.022-.007-.042-.018-.083-.059l-57.69-57.69c-.041-.041-.052-.06-.059-.084a.118.118 0 0 1 0-.069c.007-.023.018-.042.059-.083L454.073 512L166.371 224.297c-.041-.04-.052-.06-.059-.083a.118.118 0 0 1 0-.07c.007-.022.018-.042.059-.083l57.69-57.69c.041-.041.06-.052.084-.059a.118.118 0 0 1 .069 0c.023.007.042.018.083.059L512 454.073l287.703-287.702c.04-.041.06-.052.083-.059a.118.118 0 0 1 .07 0Z"/>
                          </svg>
                        </button>
                      </div>

                      <div
                          v-if="isEquipmentDeleting(item)"
                          class="snap-particles"
                          aria-hidden="true"
                      >
                        <span
                            v-for="particle in getEquipmentSnapParticles(item)"
                            :key="particle.id"
                            class="snap-particle"
                            :class="`is-${particle.kind}`"
                            :style="particle.style"
                        ></span>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="grid-landmark-side is-east">
                  <div
                      class="grid-landmark-side-stack"
                      :class="{ placeholder: isLandmarkPlaceholder('east') }"
                  >
                    <span class="grid-landmark-side-text">{{ getLandmarkDisplayValue('east') }}</span>
                    <button
                        type="button"
                        class="landmark-edit-btn is-side"
                        @click="openLandmarkEditor('east')"
                        aria-label="Редактировать восток"
                    >
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 20h9"/>
                        <path d="M16.5 3.5a2.12 2.12 0 1 1 3 3L7 19l-4 1 1-4z"/>
                      </svg>
                    </button>
                  </div>

                  <div
                      v-if="editingLandmark === 'east'"
                      class="landmark-editor-popup is-side-popup is-east-popup"
                  >
                    <div class="landmark-editor-title">{{ getLandmarkLabel('east') }}</div>
                    <div class="landmark-editor-row">
                      <input
                          v-model.trim="landmarkDraft"
                          type="text"
                          class="landmark-editor-input"
                          :placeholder="getLandmarkLabel('east')"
                          @keydown.enter.prevent="saveLandmarkDraft"
                          @keydown.esc.prevent="closeLandmarkEditor"
                      >
                      <button
                          type="button"
                          class="landmark-editor-action is-confirm"
                          @click="saveLandmarkDraft"
                          aria-label="Сохранить ориентир"
                      >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M20 6 9 17l-5-5"/>
                        </svg>
                      </button>
                      <button
                          type="button"
                          class="landmark-editor-action"
                          @click="closeLandmarkEditor"
                          aria-label="Отменить редактирование ориентира"
                      >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M18 6 6 18M6 6l12 12"/>
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div
                  class="grid-landmark-line is-south"
                  :class="{ placeholder: isLandmarkPlaceholder('south') }"
              >
                <span class="grid-landmark-text">{{ getLandmarkDisplayValue('south') }}</span>
                <button
                    type="button"
                    class="landmark-edit-btn"
                    @click="openLandmarkEditor('south')"
                    aria-label="Редактировать юг"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 20h9"/>
                    <path d="M16.5 3.5a2.12 2.12 0 1 1 3 3L7 19l-4 1 1-4z"/>
                  </svg>
                </button>

                <div
                    v-if="editingLandmark === 'south'"
                    class="landmark-editor-popup is-horizontal is-south"
                >
                  <div class="landmark-editor-title">{{ getLandmarkLabel('south') }}</div>
                  <div class="landmark-editor-row">
                    <input
                        v-model.trim="landmarkDraft"
                        type="text"
                        class="landmark-editor-input"
                        :placeholder="getLandmarkLabel('south')"
                        @keydown.enter.prevent="saveLandmarkDraft"
                        @keydown.esc.prevent="closeLandmarkEditor"
                    >
                    <button
                        type="button"
                        class="landmark-editor-action is-confirm"
                        @click="saveLandmarkDraft"
                        aria-label="Сохранить ориентир"
                    >
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 6 9 17l-5-5"/>
                      </svg>
                    </button>
                    <button
                        type="button"
                        class="landmark-editor-action"
                        @click="closeLandmarkEditor"
                        aria-label="Отменить редактирование ориентира"
                    >
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 6 6 18M6 6l12 12"/>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <Teleport to="body">
    <transition name="leave-guard-modal">
      <div
          v-if="showUnsavedLeaveModal"
          class="leave-guard-overlay create-audience-leave-modal"
          @click.self="closeUnsavedLeaveModal"
      >
        <div
            class="leave-guard-card"
            role="dialog"
            aria-modal="true"
            aria-labelledby="create-audience-leave-title"
        >
          <button
              type="button"
              class="leave-guard-close"
              @click="closeUnsavedLeaveModal"
              aria-label="Закрыть окно подтверждения"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6 6 18M6 6l12 12"/>
            </svg>
          </button>

          <div class="leave-guard-hero">
            <div class="leave-guard-icon" aria-hidden="true">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 10.5v3.75m-9.303 3.376C1.83 19.126 2.914 21 4.645 21h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 4.88c-.866-1.501-3.032-1.501-3.898 0L2.697 17.626ZM12 17.25h.007v.008H12v-.008Z"/></svg>
            </div>

            <div class="leave-guard-copy">
              <span class="leave-guard-kicker">Несохранённые изменения</span>
              <h3 id="create-audience-leave-title" class="leave-guard-title">Уйти без сохранения?</h3>
              <p class="leave-guard-text">
                Изменения в параметрах аудитории, сетке и оборудовании будут потеряны.
              </p>
            </div>
          </div>

          <div class="leave-guard-actions">
            <button
                type="button"
                class="btn btn-secondary leave-guard-btn"
                @click="closeUnsavedLeaveModal"
            >
              Остаться
            </button>
            <button
                type="button"
                class="leave-guard-danger"
                @click="confirmUnsavedLeave"
            >
              Уйти без сохранения
            </button>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>


<style scoped>
/* Scoped стили применяются только к этому компоненту */

.page-wrapper {
  background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
  min-height: 100vh;
  padding: 20px;
}

.container {
  max-width: 1600px;
  margin: 0 auto;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30px;
  animation: createAudienceHeaderReveal 0.58s cubic-bezier(0.16, 1, 0.3, 1) backwards;
}

.header-spacer {
  width: 180px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  background: white;
  border: 2px solid #3b82f6;
  border-radius: 12px;
  color: #3b82f6;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: #3b82f6;
  color: white;
  transform: translateX(-5px);
}

.back-btn svg {
  width: 20px;
  height: 20px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #1e40af;
}

.main-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 20px;
}

.left-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  animation: createAudiencePanelReveal 0.62s cubic-bezier(0.16, 1, 0.3, 1) backwards;
}

.left-panel .panel:nth-child(1) {
  animation-delay: 0.08s;
}

.left-panel .panel:nth-child(2) {
  animation-delay: 0.16s;
}

.left-panel .panel:nth-child(3) {
  animation-delay: 0.24s;
}


.panel.collapsed .collapse-icon svg {
  transform: rotate(-90deg);
}

.panel.collapsed .form-group
{
  display: none;
}

.panel-header{
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.collapse-icon {
  width: 25px;
  height: 25px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f1f5f9;
  transition: all 0.3s ease;
}

.collapse-icon:hover {
  cursor: pointer;
}

.collapse-icon svg {
  width: 24px;
  height: 24px;
  transition: transform 0.3s ease;
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e3a8a;
  margin-bottom: 16px;
}

.panel-title-tight {
  margin-bottom: 0;
}

.panel-title-no-margin {
  margin: 0;
}

.panel-hint {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 12px;
  line-height: 1.45;
}

.size-picker {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.size-btn {
  padding: 8px 12px;
  border: 2px solid #cbd5e1;
  border-radius: 10px;
  background: #f8fafc;
  color: #334155;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.size-btn:hover {
  border-color: #93c5fd;
  background: #eff6ff;
}

.size-btn.active {
  border-color: #3b82f6;
  background: #dbeafe;
  color: #1d4ed8;
}

.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  padding: 10px 14px;
  border: 2px solid #d1d5db;
  border-radius: 8px;
  font-size: 15px;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.form-select {
  width: 100%;
  border: 2px solid #d1d5db;
  border-radius: 8px;
  font-size: 15px;
  background-color: #fff;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  transition: border-color 0.2s;
  background-image: url("data:image/svg+xml,%3Csvg width='12' height='8' viewBox='0 0 12 8' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%236b7280' stroke-width='2' fill='none'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
  padding: 10px 40px 10px 14px;
}

.form-select:focus {
  outline: none;
  border-color: #3b82f6;
}

.select-field {
  position: relative;
}

.select-field .form-select {
  background-image: none !important;
  padding-right: 42px !important;
}

.select-field-arrow {
  position: absolute;
  top: 50%;
  right: 14px;
  width: 12px;
  height: 8px;
  color: #6b7280;
  pointer-events: none;
  transform: translateY(-50%);
}

:global(html[data-theme='dark']) .create-audience-page .select-field-arrow {
  color: #cbd5e1;
}

.grid-wrapper {
  overflow-x: auto;
  overflow-y: visible;
  animation: createAudienceGridReveal 0.78s cubic-bezier(0.16, 1, 0.3, 1) 0.42s backwards;
}

.grid-landmarks-shell {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  min-width: max-content;
  padding: 2px 0;
}

.grid-landmark-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.grid-landmark-main > .grid-container {
  flex-shrink: 0;
}

.grid-landmark-line {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 24px;
  color: #475569;
}

.grid-landmark-text,
.grid-landmark-side-text {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: inherit;
}

.grid-landmark-line.placeholder,
.grid-landmark-side-stack.placeholder {
  color: #94a3b8;
}

.grid-landmark-side {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  color: #475569;
}

.grid-landmark-side-stack {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.grid-landmark-side-text {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  line-height: 1;
}

.grid-landmark-side.is-west .grid-landmark-side-text {
  transform: rotate(180deg);
}

.landmark-edit-btn {
  width: 22px;
  height: 22px;
  border: 1px solid rgba(148, 163, 184, 0.34);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.94);
  color: #64748b;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
  transition: transform 0.18s ease, border-color 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
}

.landmark-edit-btn:hover {
  color: #2563eb;
  border-color: rgba(59, 130, 246, 0.34);
  transform: translateY(-1px);
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.14);
}

.landmark-edit-btn svg {
  width: 12px;
  height: 12px;
}

.landmark-edit-btn.is-side {
  width: 20px;
  height: 20px;
}

.landmark-editor-popup {
  position: absolute;
  z-index: 7;
  min-width: 210px;
  padding: 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(148, 163, 184, 0.28);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.18);
}

.landmark-editor-popup.is-north {
  top: calc(100% + 10px);
  left: 50%;
  transform: translateX(-50%);
}

.landmark-editor-popup.is-south {
  bottom: calc(100% + 10px);
  left: 50%;
  transform: translateX(-50%);
}

.landmark-editor-popup.is-west-popup {
  top: 50%;
  left: calc(100% + 10px);
  transform: translateY(-50%);
}

.landmark-editor-popup.is-east-popup {
  top: 50%;
  right: calc(100% + 10px);
  transform: translateY(-50%);
}

.landmark-editor-title {
  margin-bottom: 8px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #64748b;
}

.landmark-editor-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.landmark-editor-input {
  flex: 1;
  min-width: 0;
  height: 34px;
  padding: 0 12px;
  border: 1px solid rgba(148, 163, 184, 0.34);
  border-radius: 10px;
  background: #f8fafc;
  color: #0f172a;
  font-size: 13px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.landmark-editor-input:focus {
  outline: none;
  border-color: rgba(59, 130, 246, 0.58);
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.14);
}

.landmark-editor-action {
  width: 34px;
  height: 34px;
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 10px;
  background: #f8fafc;
  color: #475569;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, color 0.18s ease, background 0.18s ease;
}

.landmark-editor-action:hover {
  transform: translateY(-1px);
  border-color: rgba(100, 116, 139, 0.32);
  color: #1e293b;
}

.landmark-editor-action.is-confirm {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  border-color: transparent;
  color: #ffffff;
}

.landmark-editor-action.is-confirm:hover {
  color: #ffffff;
}

.landmark-editor-action svg {
  width: 16px;
  height: 16px;
}

.grid-size-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.equipment-palette {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.equipment-item {
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  border: 2px solid #cbd5e1;
  border-radius: 12px;
  padding: 16px;
  cursor: grab;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  user-select: none;
  animation: createAudienceItemReveal 0.46s cubic-bezier(0.16, 1, 0.3, 1) backwards;
}

.equipment-item:nth-child(1) {
  animation-delay: 0.24s;
}

.equipment-item:nth-child(2) {
  animation-delay: 0.28s;
}

.equipment-item:nth-child(3) {
  animation-delay: 0.32s;
}

.equipment-item:nth-child(4) {
  animation-delay: 0.36s;
}

.equipment-item:nth-child(5) {
  animation-delay: 0.4s;
}

.equipment-item:nth-child(6) {
  animation-delay: 0.44s;
}

.equipment-item:nth-child(7) {
  animation-delay: 0.48s;
}

.equipment-item:hover {
  transform: scale(1.02);
  box-shadow: 0 6px 16px rgba(0,0,0,0.15);
  border-color: #3b82f6;
}

/* Класс dragging добавляется нативно при dragstart, но можно стилизовать */
.equipment-item.dragging {
  opacity: 0.5;
  cursor: grabbing;
}

.equipment-item.selected {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
}

.equipment-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  color: white;
  will-change: transform;
}

/* Глубокий селектор для SVG внутри безопасной обертки, если scoped мешает */
.equipment-icon:deep(svg) {
  width: 28px;
  height: 28px;
}

.equipment-name {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  text-align: center;
}

.stats-panel {
  background: linear-gradient(135deg, #f0f9ff, #dbeafe);
  border: 2px solid #93c5fd;
  border-radius: 12px;
  padding: 16px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 14px;
  animation: createAudienceStatsReveal 0.46s cubic-bezier(0.16, 1, 0.3, 1) backwards;
}

.stat-item:nth-child(1) {
  animation-delay: 0.28s;
}

.stat-item:nth-child(2) {
  animation-delay: 0.32s;
}

.stat-item:nth-child(3) {
  animation-delay: 0.36s;
}

.stat-item:nth-child(4) {
  animation-delay: 0.4s;
}

.stat-item:nth-child(5) {
  animation-delay: 0.44s;
}

.stat-item:nth-child(6) {
  animation-delay: 0.48s;
}

.stat-item:nth-child(7) {
  animation-delay: 0.52s;
}

.stat-label {
  color: #64748b;
}

.stat-value {
  font-weight: 700;
  color: #1e40af;
}

.btn {
  padding: 12px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.3);
}

.btn-primary:disabled {
  cursor: not-allowed;
  opacity: 0.58;
  transform: none;
  box-shadow: none;
}

.btn-primary:hover:disabled {
  transform: none;
  box-shadow: none;
}

.btn-secondary {
  background: #f1f5f9;
  color: #64748b;
}

.btn-secondary:hover {
  background: #e2e8f0;
}

.grid-panel {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  min-height: 600px;
  animation: createAudienceGridPanelReveal 0.72s cubic-bezier(0.16, 1, 0.3, 1) 0.2s backwards;
}

.grid-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  gap: 18px;
  animation: createAudiencePanelReveal 0.58s cubic-bezier(0.16, 1, 0.3, 1) 0.34s backwards;
}

.grid-info {
  font-size: 14px;
  color: #64748b;
}

.grid-header-actions {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
  flex-shrink: 0;
}

.grid-action-cluster {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 10px;
}

.grid-actions-menu {
  position: relative;
}

.grid-actions-trigger {
  height: 42px;
  padding: 0 14px;
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 14px;
  background:
      linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(248, 250, 252, 0.95)),
      #f8fafc;
  color: #334155;
  font-family: inherit;
  font-size: 13px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  white-space: nowrap;
  cursor: pointer;
  box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.86),
      0 10px 22px rgba(15, 23, 42, 0.08);
  transition: transform 0.2s ease, border-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}

.grid-actions-trigger svg {
  width: 17px;
  height: 17px;
}

.grid-actions-trigger:hover,
.grid-actions-trigger.active {
  color: #1d4ed8;
  border-color: rgba(59, 130, 246, 0.42);
  transform: translateY(-1px);
  box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.9),
      0 14px 28px rgba(37, 99, 235, 0.14);
}

.grid-actions-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  z-index: 12;
  width: min(328px, calc(100vw - 48px));
  padding: 8px;
  border: 1px solid rgba(203, 213, 225, 0.86);
  border-radius: 18px;
  background:
      radial-gradient(circle at top right, rgba(59, 130, 246, 0.12), transparent 34%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.98));
  box-shadow: 0 24px 54px rgba(15, 23, 42, 0.16);
}

.grid-action-menu-item {
  width: 100%;
  min-height: 48px;
  padding: 8px 10px;
  border: 0;
  border-radius: 13px;
  background: transparent;
  color: #1e293b;
  font-family: inherit;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 10px;
  cursor: pointer;
  text-align: left;
  transition: background 0.18s ease, color 0.18s ease, transform 0.18s ease, opacity 0.18s ease;
}

.grid-action-menu-item:hover:not(:disabled) {
  background: rgba(219, 234, 254, 0.72);
  color: #1d4ed8;
  transform: translateX(2px);
}

.grid-action-menu-item:disabled {
  cursor: not-allowed;
  opacity: 0.46;
}

.grid-action-menu-item.is-danger:hover:not(:disabled) {
  background: rgba(254, 226, 226, 0.86);
  color: #b91c1c;
}

.grid-action-menu-icon {
  width: 32px;
  height: 32px;
  border-radius: 11px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  color: #475569;
  flex-shrink: 0;
}

.grid-action-menu-icon.is-blue {
  background: #dbeafe;
  color: #1d4ed8;
}

.grid-action-menu-icon.is-danger {
  background: #fee2e2;
  color: #be123c;
}

.grid-action-menu-icon svg {
  width: 16px;
  height: 16px;
}

.grid-action-menu-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.grid-action-menu-title {
  font-size: 13px;
  font-weight: 800;
  line-height: 1.15;
}

.grid-action-menu-hint {
  color: #64748b;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.2;
}

.grid-action-divider {
  height: 1px;
  margin: 6px 8px;
  background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.38), transparent);
}

.grid-actions-dropdown-enter-active,
.grid-actions-dropdown-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.grid-actions-dropdown-enter-from,
.grid-actions-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.98);
}

.grid-json-input {
  display: none;
}

.grid-save-btn {
  min-width: 148px;
  box-shadow: 0 10px 24px rgba(16, 185, 129, 0.18);
}

.clear-grid-btn {
  padding: 10px 16px;
  background: linear-gradient(135deg, #fff7ed, #fff1f2);
  color: #be123c;
  border: 1px solid #fecdd3;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  white-space: nowrap;
  box-shadow: 0 8px 20px rgba(244, 63, 94, 0.1);
  transition: all 0.24s ease;
}

.clear-grid-btn:hover {
  transform: translateY(-1px);
  background: linear-gradient(135deg, #ffe4e6, #ffe4e6);
  border-color: #fda4af;
  box-shadow: 0 12px 26px rgba(244, 63, 94, 0.14);
}

.clear-grid-btn:disabled {
  cursor: not-allowed;
  background: #f8fafc;
  color: #94a3b8;
  border-color: #e2e8f0;
  box-shadow: none;
  transform: none;
}

.clear-grid-btn.is-armed {
  background: linear-gradient(135deg, #fff1f2, #ffe4e6);
  border-color: #fb7185;
  color: #9f1239;
}

.clear-grid-btn.is-danger {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  border-color: transparent;
  color: #ffffff;
  box-shadow: 0 12px 26px rgba(220, 38, 38, 0.2);
}

.clear-grid-btn.is-danger:hover {
  background: linear-gradient(135deg, #dc2626, #b91c1c);
  border-color: transparent;
}

:global(html[data-theme='dark'] .create-audience-page .grid-actions-trigger) {
  background:
      linear-gradient(135deg, rgba(30, 41, 59, 0.94), rgba(15, 23, 42, 0.96)),
      #0f172a;
  border-color: #334155;
  color: #cbd5e1;
  box-shadow: none;
}

:global(html[data-theme='dark'] .create-audience-page .grid-actions-trigger:hover),
:global(html[data-theme='dark'] .create-audience-page .grid-actions-trigger.active) {
  border-color: #2563eb;
  color: #bfdbfe;
  box-shadow: 0 14px 28px rgba(37, 99, 235, 0.14);
}

:global(html[data-theme='dark'] .create-audience-page .grid-actions-dropdown) {
  background:
      radial-gradient(circle at top right, rgba(37, 99, 235, 0.18), transparent 34%),
      linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(2, 6, 23, 0.98));
  border-color: #334155;
  box-shadow: 0 24px 54px rgba(2, 6, 23, 0.48);
}

:global(html[data-theme='dark'] .create-audience-page .grid-action-menu-item) {
  color: #e2e8f0;
}

:global(html[data-theme='dark'] .create-audience-page .grid-action-menu-item:hover:not(:disabled)) {
  background: rgba(37, 99, 235, 0.18);
  color: #bfdbfe;
}

:global(html[data-theme='dark'] .create-audience-page .grid-action-menu-item.is-danger:hover:not(:disabled)) {
  background: rgba(127, 29, 29, 0.26);
  color: #fecaca;
}

:global(html[data-theme='dark'] .create-audience-page .grid-action-menu-icon) {
  background: #111827;
  color: #cbd5e1;
}

:global(html[data-theme='dark'] .create-audience-page .grid-action-menu-icon.is-blue) {
  background: rgba(30, 64, 175, 0.36);
  color: #bfdbfe;
}

:global(html[data-theme='dark'] .create-audience-page .grid-action-menu-icon.is-danger) {
  background: rgba(127, 29, 29, 0.32);
  color: #fecaca;
}

:global(html[data-theme='dark'] .create-audience-page .grid-action-menu-hint) {
  color: #94a3b8;
}

:global(html[data-theme='dark'] .create-audience-page .grid-action-divider) {
  background: linear-gradient(90deg, transparent, rgba(71, 85, 105, 0.72), transparent);
}

:global(html[data-theme='dark'] .create-audience-page) {
  background: #020617 !important;
  color-scheme: dark;
  filter: none !important;
}

:global(html[data-theme='dark'] .create-audience-page.is-edit-mode),
:global(html[data-theme='dark'] .create-audience-page.is-edit-mode .panel),
:global(html[data-theme='dark'] .create-audience-page.is-edit-mode .grid-panel),
:global(html[data-theme='dark'] .create-audience-page.is-edit-mode .grid-container),
:global(html[data-theme='dark'] .create-audience-page.is-edit-mode .grid-actions-trigger),
:global(html[data-theme='dark'] .create-audience-page.is-edit-mode .grid-actions-dropdown),
:global(html[data-theme='dark'] .create-audience-page.is-edit-mode .form-input),
:global(html[data-theme='dark'] .create-audience-page.is-edit-mode .form-select),
:global(html[data-theme='dark'] .create-audience-page.is-edit-mode .stats-panel) {
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  filter: none !important;
}

:global(html[data-theme='dark'] .create-audience-page.is-edit-mode .form-input:disabled) {
  opacity: 1 !important;
  background: #020617 !important;
  border-color: #1e3a8a !important;
  color: #cbd5e1 !important;
  -webkit-text-fill-color: #cbd5e1 !important;
  box-shadow: none !important;
}

:global(html[data-theme='dark'] .create-audience-page.is-edit-mode .grid-save-btn:disabled) {
  opacity: 1 !important;
  background: #052e2b !important;
  border: 1px solid #047857 !important;
  color: #86efac !important;
  box-shadow: none !important;
}

:global(html[data-theme='dark'] .create-audience-page.is-edit-mode .grid-action-menu-item:disabled),
:global(html[data-theme='dark'] .create-audience-page.is-edit-mode .clear-grid-btn:disabled) {
  opacity: 1 !important;
  background: #07111f !important;
  border-color: #1e293b !important;
  color: #64748b !important;
  box-shadow: none !important;
}

:global(html[data-theme='dark'] .create-audience-page.is-edit-mode .grid-actions-trigger) {
  background: #020617 !important;
  border-color: #1e3a8a !important;
  box-shadow: none !important;
}

.clear-grid-confirm {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  width: min(420px, calc(100vw - 64px));
  padding: 14px;
  border-radius: 18px;
  border: 1px solid #fecdd3;
  background:
      radial-gradient(circle at top left, rgba(251, 113, 133, 0.16), transparent 34%),
      linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(255, 241, 242, 0.96));
  box-shadow: 0 22px 44px rgba(15, 23, 42, 0.14);
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 14px;
  z-index: 8;
}

.clear-grid-confirm-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #e11d48;
  background: linear-gradient(135deg, rgba(255, 228, 230, 0.98), rgba(254, 205, 211, 0.9));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.clear-grid-confirm-icon svg {
  width: 20px;
  height: 20px;
}

.clear-grid-confirm-copy {
  min-width: 0;
}

.clear-grid-confirm-title {
  font-size: 14px;
  font-weight: 700;
  color: #881337;
}

.clear-grid-confirm-text {
  margin-top: 4px;
  font-size: 13px;
  line-height: 1.45;
  color: #9f1239;
}

.clear-grid-confirm-actions {
  grid-column: 1 / -1;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.clear-grid-cancel {
  flex: 0 0 auto;
  min-width: 104px;
}

.clear-confirm-enter-active,
.clear-confirm-leave-active {
  transition: opacity 0.2s ease, transform 0.24s ease;
}

.clear-confirm-enter-from,
.clear-confirm-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.98);
}

.leave-guard-overlay {
  position: fixed;
  inset: 0;
  z-index: 1100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.58);
}

.leave-guard-card {
  position: relative;
  width: min(100%, 520px);
  padding: 24px;
  border-radius: 28px;
  border: 1px solid rgba(251, 191, 36, 0.24);
  background:
      radial-gradient(circle at top right, rgba(59, 130, 246, 0.12), transparent 32%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.98));
  box-shadow:
      0 28px 54px rgba(15, 23, 42, 0.2),
      inset 0 1px 0 rgba(255, 255, 255, 0.72);
  overflow: hidden;
}

.leave-guard-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 38px;
  height: 38px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(255, 255, 255, 0.74);
  color: #64748b;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;
}

.leave-guard-close:hover {
  background: rgba(255, 255, 255, 0.96);
  color: #0f172a;
  transform: translateY(-1px);
}

.leave-guard-close svg {
  width: 18px;
  height: 18px;
}

.leave-guard-hero {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding-right: 42px;
}

.leave-guard-icon {
  width: 54px;
  height: 54px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(254, 240, 138, 0.42), rgba(251, 146, 60, 0.2));
  color: #b45309;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.leave-guard-icon svg {
  width: 24px;
  height: 24px;
}

.leave-guard-copy {
  min-width: 0;
}

.leave-guard-kicker {
  display: inline-block;
  margin-bottom: 6px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #92400e;
}

.leave-guard-title {
  margin: 0;
  font-size: 26px;
  line-height: 1.08;
  font-weight: 800;
  color: #0f172a;
}

.leave-guard-text {
  margin: 10px 0 0;
  font-size: 14px;
  line-height: 1.6;
  color: #64748b;
}

.leave-guard-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 24px;
  padding-top: 18px;
  border-top: 1px solid rgba(203, 213, 225, 0.72);
}

.leave-guard-btn,
.leave-guard-danger {
  min-height: 44px;
  border-radius: 14px;
}

.leave-guard-btn {
  min-width: 128px;
}

.leave-guard-danger {
  padding: 0 18px;
  border: 1px solid rgba(244, 63, 94, 0.18);
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 14px 28px rgba(220, 38, 38, 0.2);
  transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
}

.leave-guard-danger:hover {
  transform: translateY(-1px);
  box-shadow: 0 18px 34px rgba(220, 38, 38, 0.24);
  filter: saturate(1.05);
}

.leave-guard-modal-enter-active,
.leave-guard-modal-leave-active {
  transition: opacity 0.22s ease;
}

.leave-guard-modal-enter-active .leave-guard-card,
.leave-guard-modal-leave-active .leave-guard-card {
  transition: transform 0.24s ease, opacity 0.24s ease;
}

.leave-guard-modal-enter-from,
.leave-guard-modal-leave-to {
  opacity: 0;
}

.leave-guard-modal-enter-from .leave-guard-card,
.leave-guard-modal-leave-to .leave-guard-card {
  opacity: 0;
  transform: translateY(12px) scale(0.98);
}

.grid-container {
  --cell-size: 80px;
  --icon-size: 38px;
  --font-size: 10px;
  --btn-size: 20px;
  --cell-fw: 600;
  --grid-gap: 8px;

  position: relative;
  display: inline-block;
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
  border: 2px dashed #cbd5e1;
  user-select: none;
}

.grid-container.density-compact {
  --cell-size: 60px;
  --icon-size: 30px;
  --font-size: 9px;
  --btn-size: 18px;
  --cell-fw: 500;
  --grid-gap: 6px;
}

.grid-container.density-tiny {
  --cell-size: 45px;
  --icon-size: 28px;
  --font-size: 0px;
  --btn-size: 16px;
  --grid-gap: 4px;
}

.grid-container.density-tiny .cell-label {
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
  top: 20px;
  left: 20px;
  pointer-events: none;
}

.grid-overlay .grid-equipment {
  pointer-events: auto;
}

.grid-container.density-compact .grid-equipment {
  padding: 4px;
  gap: 4px;
  border-radius: 10px;
}

.grid-container.density-tiny .grid-equipment {
  padding: 4px;
  gap: 2px;
  border-radius: 8px;
}

.grid-container.density-tiny .remove-btn {
  top: 2px;
  right: 2px;
}

.grid-cell {
  width: var(--cell-size);
  height: var(--cell-size);
  border-radius: 12px;
  border: 1.5px dashed #cbd5e1;
  background: #ffffff;
  box-sizing: border-box;
  transition: background 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
}

.grid-cell:hover {
  border-color: #94a3b8;
  background: #f8fafc;
}

.grid-cell.drag-over {
  border-color: #3b82f6;
  background: #dbeafe;
}

.grid-equipment {
  --snap-surface: #ffffff;
  --snap-border: #cbd5e1;
  --snap-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);

  position: relative;
  z-index: 2;

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;

  min-width: 0;
  min-height: 0;
  box-sizing: border-box;

  padding: 8px;
  border-radius: 12px;
  background: var(--snap-surface);
  border: 1px solid var(--snap-border);
  box-shadow: var(--snap-shadow);

  cursor: grab;
  overflow: hidden;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}

.grid-equipment:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.12);
  border-color: #94a3b8;
}

.grid-equipment:active {
  cursor: grabbing;
}

.grid-equipment.broken {
  --snap-surface: #fef2f2;
  --snap-border: #f87171;

  background: #fef2f2;
  border-color: #f87171;
}

.grid-equipment.is-wide {
  flex-direction: row;
  justify-content: center;
}

.grid-equipment.is-tall {
  flex-direction: column;
}

.equipment-card-content {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  flex-direction: inherit;
  align-items: center;
  justify-content: center;
  gap: inherit;
  min-width: 0;
  min-height: 0;
  padding: inherit;
  box-sizing: border-box;
}

:global(html[data-theme='dark'] .create-audience-page .grid-equipment) {
  --snap-surface: #0b1220;
  --snap-border: #1e3a8a;
  --snap-shadow: none;
}

:global(html[data-theme='dark'] .create-audience-page .grid-equipment.broken) {
  --snap-surface: #3b1218;
  --snap-border: #fb7185;
}

.grid-equipment.is-removing {
  z-index: 8;
  pointer-events: none;
  overflow: visible;
  background: transparent;
  border-color: transparent;
  box-shadow: none;
  animation: equipmentSnapImpact 180ms cubic-bezier(0.22, 1, 0.36, 1) both;
}

:global(html[data-theme='dark'] .create-audience-page .grid-equipment.is-removing) {
  background: transparent !important;
  border-color: transparent !important;
  box-shadow: none !important;
}

.grid-equipment.is-removing::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 1;
  box-sizing: border-box;
  border: 1px solid var(--snap-border);
  border-radius: inherit;
  background: var(--snap-surface);
  box-shadow: var(--snap-shadow);
  pointer-events: none;
  animation: equipmentSnapSurface 920ms 90ms cubic-bezier(0.58, 0, 0.42, 1) forwards;
}

.grid-equipment.is-removing::after {
  content: "";
  position: absolute;
  top: -10%;
  bottom: -10%;
  left: 100%;
  width: 24%;
  pointer-events: none;
  z-index: 6;
  opacity: 0;
  background:
      radial-gradient(ellipse at 50% 34%, rgba(255, 255, 255, 0.82), transparent 54%),
      linear-gradient(90deg, transparent, rgba(125, 211, 252, 0.48), transparent);
  filter: blur(2px);
  mix-blend-mode: screen;
  transform: translateX(-50%);
  animation: equipmentSnapEdge 920ms 90ms cubic-bezier(0.58, 0, 0.42, 1) forwards;
}

.grid-equipment.is-removing .equipment-card-content {
  animation: equipmentSnapSurface 920ms 90ms cubic-bezier(0.58, 0, 0.42, 1) forwards;
}

.snap-particles {
  position: absolute;
  inset: 0;
  z-index: 7;
  pointer-events: none;
  overflow: visible;
}

.snap-particle {
  position: absolute;
  left: var(--snap-x);
  top: var(--snap-y);
  width: var(--snap-width);
  height: var(--snap-size);
  background: var(--snap-color);
  clip-path: var(--snap-clip);
  opacity: 0;
  transform: translate(-50%, -50%) scale(0.28) rotate(0deg);
  animation: equipmentSnapParticle var(--snap-duration) cubic-bezier(0.16, 0.72, 0.24, 1) forwards;
  animation-delay: var(--snap-delay);
  will-change: transform, opacity, filter;
}

.snap-particle.is-dust {
  border-radius: 999px;
}

.snap-particle.is-shard {
  border-radius: 1px;
}

.snap-particle.is-spark {
  border-radius: 999px;
  box-shadow: 0 0 5px 1px var(--snap-color);
}

.cell-icon {
  width: var(--icon-size);
  height: var(--icon-size);
  border-radius: 10px;

  display: flex;
  align-items: center;
  justify-content: center;

  color: white;
  flex-shrink: 0;
}


.cell-icon :deep(svg),
.cell-icon svg {
  width: calc(var(--icon-size) * 0.7);
  height: calc(var(--icon-size) * 0.7);
}


.cell-label {
  font-size: var(--font-size);
  font-weight: var(--cell-fw);
  line-height: 1.15;
  text-align: center;
  color: #334155;

  word-break: break-word;
  overflow-wrap: anywhere;
  max-width: 100%;
}

.remove-btn {
  position: absolute;
  top: 4px;
  right: 4px;

  width: var(--btn-size);
  height: var(--btn-size);
  border: none;
  border-radius: 999px;

  display: flex;
  align-items: center;
  justify-content: center;

  background: rgba(15, 23, 42, 0.72);
  color: white;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s ease, background 0.15s ease, transform 0.15s ease;
}

.grid-equipment:hover .remove-btn {
  opacity: 1;
}

.remove-btn:hover {
  background: #dc2626;
  transform: scale(1.05);
}

.remove-btn svg {
  width: 12px;
  height: 12px;
}

.remove-btn:hover {
  background: #dc2626;
}

.empty-grid {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #94a3b8;
}

.empty-grid svg {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

/* Media Queries (адаптивность) */
@media (max-width: 1400px) {
  .main-layout {
    grid-template-columns: 280px 1fr;
  }
}

@media (max-width: 1024px) {
  .main-layout {
    grid-template-columns: 1fr;
  }

  .header {
    flex-wrap: wrap;
    gap: 15px;
  }

  .page-title {
    font-size: 24px;
    text-align: center;
    width: 100%;
    order: -1;
  }

  .header > div:last-child {
    display: none;
  }

  .left-panel {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
  }

  .cell-icon {
    width: 36px;
    height: 36px; }
}

@media (max-width: 768px)
{
  .cell-label {
    font-size: 8px;
  }

  .container {
    max-width: 100%;
  }

  .back-btn {
    width: 100%;
    justify-content: center;
  }

  .left-panel {
    grid-template-columns: 1fr;
  }

  .grid-container {
    --cell-size: 60px;
    --icon-size: 32px;
  }

  .grid-container.density-tiny {
    gap: 8px;
  }

  .grid-panel {
    overflow-x: auto;
  }

  .grid-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .grid-header-actions {
    width: 100%;
    align-items: stretch;
  }

  .grid-action-cluster {
    width: 100%;
  }

  .grid-actions-menu {
    flex: 0 0 auto;
  }

  .grid-actions-trigger {
    width: 100%;
  }

  .grid-actions-dropdown {
    left: 0;
    right: auto;
    width: min(328px, calc(100vw - 48px));
  }

  .grid-action-cluster > .grid-save-btn {
    flex: 1 1 0;
    min-width: 0;
  }

  .clear-grid-confirm {
    position: static;
    width: 100%;
  }

  .clear-grid-confirm-actions {
    justify-content: stretch;
  }

  .clear-grid-confirm-actions > * {
    flex: 1 1 0;
  }

  .leave-guard-overlay {
    padding: 18px;
  }

  .leave-guard-card {
    width: min(100%, 100%);
    padding: 20px;
    border-radius: 24px;
  }

  .leave-guard-actions {
    flex-direction: column;
  }

  .leave-guard-actions > * {
    width: 100%;
  }

  .grid-landmarks-shell {
    gap: 8px;
  }

  .grid-landmark-main {
    gap: 10px;
  }

  .grid-landmark-line {
    min-height: 22px;
  }

  .grid-landmark-text,
  .grid-landmark-side-text {
    font-size: 10px;
    letter-spacing: 0.1em;
  }

  .grid-landmark-side {
    min-width: 34px;
  }

  .landmark-editor-popup {
    min-width: 190px;
    padding: 10px;
  }

  .landmark-editor-popup.is-west-popup,
  .landmark-editor-popup.is-east-popup {
    top: calc(100% + 10px);
    left: 50%;
    right: auto;
    transform: translateX(-50%);
  }

  .landmark-editor-input,
  .landmark-editor-action {
    height: 32px;
  }

}

@media (max-width: 480px)
{
  .equipment-palette {
    grid-template-columns: repeat(2, 1fr);
  }

  .leave-guard-card {
    padding: 18px;
  }

  .leave-guard-hero {
    gap: 12px;
    padding-right: 32px;
  }

  .leave-guard-icon {
    width: 46px;
    height: 46px;
    border-radius: 15px;
  }

  .leave-guard-title {
    font-size: 22px;
  }

  .leave-guard-text {
    font-size: 13px;
  }

  .grid-cell {
    width: 50px; height: 50px;
  }

  .cell-equipment {
    gap: 0;
  }

  .cell-icon {
    width: 32px;
    height: 32px;
  }

  .grid-landmark-main {
    gap: 8px;
  }

  .grid-landmark-text,
  .grid-landmark-side-text {
    font-size: 9px;
    letter-spacing: 0.08em;
  }

  .grid-landmark-side {
    min-width: 28px;
  }

  .landmark-edit-btn {
    width: 20px;
    height: 20px;
  }

  .landmark-edit-btn.is-side {
    width: 18px;
    height: 18px;
  }

  .landmark-editor-popup {
    min-width: 170px;
    padding: 9px;
  }

  .landmark-editor-title {
    margin-bottom: 6px;
    font-size: 10px;
  }

  .landmark-editor-row {
    gap: 6px;
  }

  .landmark-editor-input {
    height: 30px;
    padding: 0 10px;
    font-size: 12px;
  }

  .landmark-editor-action {
    width: 30px;
    height: 30px;
  }
}

@keyframes createAudienceHeaderReveal {
  from {
    opacity: 0;
    transform: translateY(-14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes createAudiencePanelReveal {
  from {
    opacity: 0;
    transform: translateY(22px) scale(0.985);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes createAudienceGridPanelReveal {
  from {
    opacity: 0;
    transform: translateX(24px) scale(0.988);
  }
  to {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

@keyframes createAudienceGridReveal {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes createAudienceItemReveal {
  from {
    opacity: 0;
    transform: translateY(14px) scale(0.94);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes createAudienceStatsReveal {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes equipmentSnapImpact {
  0% {
    transform: translateY(0) scale(1);
  }
  48% {
    transform: translateY(-1px) scale(1.025);
  }
  100% {
    transform: translateY(0) scale(1);
  }
}

@keyframes equipmentSnapSurface {
  0%, 8% {
    clip-path: polygon(
        0 0, 100% 0, 100% 12%, 100% 25%, 100% 39%,
        100% 53%, 100% 67%, 100% 82%, 100% 100%, 0 100%
    );
  }
  38% {
    clip-path: polygon(
        0 0, 72% 0, 78% 12%, 69% 25%, 75% 39%,
        68% 53%, 74% 67%, 66% 82%, 71% 100%, 0 100%
    );
  }
  72% {
    clip-path: polygon(
        0 0, 31% 0, 37% 12%, 27% 25%, 34% 39%,
        26% 53%, 33% 67%, 24% 82%, 29% 100%, 0 100%
    );
  }
  100% {
    clip-path: polygon(
        0 0, 0 0, 0 12%, 0 25%, 0 39%,
        0 53%, 0 67%, 0 82%, 0 100%, 0 100%
    );
  }
}

@keyframes equipmentSnapParticle {
  0% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.28) rotate(0deg);
    filter: blur(0);
  }
  13% {
    opacity: 0.98;
    transform: translate(-50%, -50%) scale(1) rotate(0deg);
    filter: blur(0);
  }
  48% {
    opacity: 0.9;
    transform:
        translate(
            calc(-50% + var(--snap-mid-tx)),
            calc(-50% + var(--snap-mid-ty))
        )
        scale(0.86)
        rotate(var(--snap-mid-rotate));
    filter: blur(0.15px);
  }
  78% {
    opacity: 0.48;
    transform:
        translate(
            calc(-50% + var(--snap-late-tx)),
            calc(-50% + var(--snap-late-ty))
        )
        scale(0.52)
        rotate(var(--snap-late-rotate));
    filter: blur(0.55px);
  }
  100% {
    opacity: 0;
    transform:
        translate(
            calc(-50% + var(--snap-tx)),
            calc(-50% + var(--snap-ty))
        )
        scale(0.08)
        rotate(var(--snap-rotate));
    filter: blur(1.8px);
  }
}

@keyframes equipmentSnapEdge {
  0% {
    opacity: 0;
    left: 100%;
  }
  12% {
    opacity: 0.78;
  }
  38% {
    left: 72%;
    opacity: 0.66;
  }
  72% {
    left: 31%;
    opacity: 0.42;
  }
  100% {
    opacity: 0;
    left: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .header,
  .panel,
  .equipment-item,
  .stat-item,
  .grid-panel,
  .grid-header,
  .grid-wrapper {
    animation: none !important;
  }

  .grid-equipment.is-removing {
    opacity: 0 !important;
    animation: none !important;
    transition: opacity 160ms ease !important;
  }

  .grid-equipment.is-removing::before,
  .grid-equipment.is-removing::after,
  .grid-equipment.is-removing .equipment-card-content,
  .snap-particle {
    animation: none !important;
  }

  .grid-equipment.is-removing::before,
  .grid-equipment.is-removing::after,
  .snap-particles {
    display: none !important;
  }
}
</style>
