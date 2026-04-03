<script>
import router from "@/router/index.js";
import api from "@/services/api.js";
import {useNotificationsStore} from "@/stores/notifications.js";
import {useAudienceContext} from "@/stores/officeCtx.js";
import {useAuthStore} from "@/stores/auth.js";

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

export default {
  name: 'CreateAudience',
  props: ['id'],
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

      clearGridClicked: false,
      paramsCollapsed: false,
      loading: false,

      hasUnsavedChanges: false,
      isHydrating: false,
      initialSnapshot: '',
    };
  },

  computed: {
    isEditMode()
    {
      return !!this.id;
    },

    equipmentTypes() {
      return EQUIPMENT_TYPES;
    },

    pageTitle() {
      return this.isEditMode ? `Редактирование аудитории №${this.id}` : 'Добавление новой аудитории';
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
      const id = item.localId ?? item.dbId;
      this.equipmentItems = this.equipmentItems.filter(
          eq => (eq.localId ?? eq.dbId) !== id
      );
    },

    resolveDropAnchorPosition(row, col, width = 1, height = 1) {
      return {
        row: row - (height - 1),
        col: col - (width - 1),
      };
    },

    clearGrid() {
      if (this.clearGridClicked) {
        this.equipmentItems = [];
      }
    },

    resetForm() {
      this.isHydrating = true;

      if (this.isEditMode) {
        this.loadAudienceData();
        return;
      }

      this.classroomNumber = null;
      this.floorNumber = 1;
      this.gridWidth = 6;
      this.gridHeight = 4;
      this.officeNumber = 1;
      this.equipmentItems = [];
      this.selectedEquipmentId = null;
      this.selectedEquipmentSize = { width: 1, height: 1 };
      this.clearGridClicked = false;

      this.$nextTick(() => {
        this.captureInitialSnapshot();
        this.isHydrating = false;
      });
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
        hardware: normalizedItems,
      });
    },

    captureInitialSnapshot() {
      this.initialSnapshot = this.buildAudienceSnapshot();
      this.hasUnsavedChanges = false;
    },

    recomputeUnsavedChanges() {
      if (this.isHydrating) return;
      this.hasUnsavedChanges = this.buildAudienceSnapshot() !== this.initialSnapshot;
    },

    async getOffices()
    {
      await api.get(`/offices/all_short`).then(response => {
        this.offices_ids = Object.values(response.data).map(item => item.id);
      })
    },

    async loadAudienceData() {
      this.loading = true;
      try {
        const res = await api.get(`/audiences/${this.id}`);
        const data = res.data;

        this.classroomNumber = String(data.id);
        this.floorNumber = data.floor;
        this.officeNumber = data.office_id;
        this.gridWidth = data.width;
        this.gridHeight = data.height;

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

        await this.$nextTick(() => {
          this.captureInitialSnapshot();
          this.isHydrating = false;
        });
      } catch (e) {
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
        floor: this.floorNumber,
        width: this.gridWidth,
        height: this.gridHeight,
        hardware: this.mapFrontendToBackend(validItems),
        office_id: this.officeNumber
      };

      if (this.isEditMode) {
        api.put(`/audiences/${this.id}`, classroomData)
            .then(() => {
              this.notify.success(`Аудитория обновлена!`);
              this.audienceContext.setOffice(classroomData.office_id);
              this.hasUnsavedChanges = false;
              router.push({ name: "Audience", params: { audienceId: this.id } });
            })
            .catch(err => {
              this.notify.error(`Ошибка обновления: ${err.response?.data?.detail || ''}`);
            });
      } else {
        const createPayload = {
          ...classroomData,
          id: Number(this.classroomNumber)
        };

        api.post(`/audiences`, createPayload)
            .then(() => {
              this.notify.success(`Аудитория создана!`);
              this.hasUnsavedChanges = false;
              router.push({ name: "Audience", params: { audienceId: Number(this.classroomNumber) } });
            })
            .catch(err => {
              if (err.response?.status === 409) {
                this.notify.error(`Такая аудитория уже существует!`);
              } else {
                this.notify.error(`Не удалось создать аудиторию!`);
              }
            });
      }
    },

    goBack() {
      router.go(-1)
    },

    classroomNumberFilter() {

      if (!/^\d*[1-9]\d*$/.test(this.classroomNumber) || this.classroomNumber.length > 3)
        this.classroomNumber = this.classroomNumber.slice(0, -1);
    }
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

    classroomNumber() {
      this.recomputeUnsavedChanges();
    }
  },

  mounted()
  {
    this.getOffices();
    if (this.id)
    {
      this.loadAudienceData();
    }
  },

  beforeRouteLeave(to, from, next)
  {
    if (this.hasUnsavedChanges && !this.authStore.isLoggingOut)
    {
      const answer = window.confirm('У вас есть несохраненные изменения. Вы уверены, что хотите уйти?');
      if (answer)
      {
        next();
      }
      else
      {
        next(false);
      }
    }
    else
    {
      next();
    }
  }

};
</script>

<template>
  <div class="page-wrapper create-audience-page">
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
              <select class="form-select" v-model.number="officeNumber">
                <option v-for="office in offices_ids" :value="office">Корпус {{ office }}</option>
              </select>
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
                <div class="equipment-icon" :style="{ background: eq.color }" v-html="eq.icon"></div>
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

            <div class="action-buttons action-buttons-spaced">
              <button class="btn btn-secondary" @click="resetForm">Сброс</button>
              <button class="btn btn-primary" @click="saveClassroom">
                {{ isEditMode ? 'Сохранить' : 'Создать' }}
              </button>
            </div>
          </div>
        </div>

        <div class="grid-panel">
          <div class="grid-header">
            <div>
              <h3 class="panel-title panel-title-no-margin">Расстановка оборудования</h3>
              <p class="grid-info">Сетка {{ gridWidth }}×{{ gridHeight }}</p>
            </div>
            <button class="clear-grid-btn" @click="clearGrid">{{ clearGridClicked ? 'Подтвердить' : 'Очистить всё' }}</button>
          </div>

          <div class="grid-wrapper">
            <div v-if="gridWidth < 1 || gridHeight < 1" class="empty-grid">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
              <div>Задайте размеры сетки</div>
            </div>

            <div
                v-else
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
                      'is-tall': item.height >= item.width
                    }"
                    :style="getEquipmentStyle(item)"
                    draggable="true"
                    @dragstart.stop="onGridItemDragStart($event, item)"
                    @dragend="onDragEnd"
                >
                  <div
                      class="cell-icon"
                      :style="{ background: equipmentTypeMap[item.type].color }"
                      v-html="equipmentTypeMap[item.type].icon"
                  ></div>

                  <div class="cell-label">
                    {{ equipmentTypeMap[item.type].name }}
                  </div>

                  <button
                      class="remove-btn"
                      @click.stop="removeEquipment(item)"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 1024 1024">
                      <path fill="currentColor" fill-rule="evenodd" d="M799.855 166.312c.023.007.043.018.084.059l57.69 57.69c.041.041.052.06.059.084a.118.118 0 0 1 0 .069c-.007.023-.018.042-.059.083L569.926 512l287.703 287.703c.041.04.052.06.059.083a.118.118 0 0 1 0 .07c-.007.022-.018.042-.059.083l-57.69 57.69c-.041.041-.06.052-.084.059a.118.118 0 0 1-.069 0c-.023-.007-.042-.018-.083-.059L512 569.926L224.297 857.629c-.04.041-.06.052-.083.059a.118.118 0 0 1-.07 0c-.022-.007-.042-.018-.083-.059l-57.69-57.69c-.041-.041-.052-.06-.059-.084a.118.118 0 0 1 0-.069c.007-.023.018-.042.059-.083L454.073 512L166.371 224.297c-.041-.04-.052-.06-.059-.083a.118.118 0 0 1 0-.07c.007-.022.018-.042.059-.083l57.69-57.69c.041-.041.06-.052.084-.059a.118.118 0 0 1 .069 0c.023.007.042.018.083.059L512 454.073l287.703-287.702c.04-.041.06-.052.083-.059a.118.118 0 0 1 .07 0Z"/>
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

.grid-wrapper {
  overflow-x: auto;
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

/* Глубокий селектор для SVG внутри v-html, если scoped мешает */
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
}

.stat-label {
  color: #64748b;
}

.stat-value {
  font-weight: 700;
  color: #1e40af;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.action-buttons-spaced {
  margin-top: 16px;
}

.btn {
  flex: 1;
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
}

.grid-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.grid-info {
  font-size: 14px;
  color: #64748b;
}

.clear-grid-btn {
  padding: 8px 16px;
  background: #fef2f2;
  color: #dc2626;
  border: 2px solid #fecaca;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-grid-btn:hover {
  background: #fee2e2;
  border-color: #fca5a5;
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
  background: #ffffff;
  border: 1px solid #cbd5e1;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);

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

  .clear-grid-btn {
    width: 100%;
  }

}

@media (max-width: 480px)
{
  .equipment-palette {
    grid-template-columns: repeat(2, 1fr);
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
}
</style>
