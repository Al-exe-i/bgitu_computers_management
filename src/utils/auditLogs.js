import { getInviteRoleLabel } from "@/utils/invites.js";

const ENTITY_LABELS = Object.freeze({
  audience: "Аудитория",
  office: "Корпус",
  hardware: "Оборудование",
  user: "Пользователь",
  invite: "Приглашение",
  session: "Сеанс",
});

const FIELD_LABELS = Object.freeze({
  action: "действие",
  address: "адрес",
  audience_id: "аудитория",
  changed_fields: "изменённые поля",
  classroom_number: "номер аудитории",
  created_by_user_id: "создатель",
  description: "описание",
  email: "email",
  entity_id: "ID сущности",
  entity_type: "тип сущности",
  expires_at: "срок действия",
  file_count: "количество файлов",
  file_ids: "файлы",
  file_name: "файл",
  file_names: "файлы",
  files: "файлы",
  floor: "этаж",
  hardware: "оборудование",
  hardware_id: "оборудование",
  height: "высота",
  id: "ID",
  inv_number: "инвентарный номер",
  ip: "IP-адрес",
  landmarks: "ориентиры",
  method: "метод",
  name: "имя",
  note: "примечание",
  office_id: "корпус",
  path: "путь",
  payload: "данные",
  photo: "фото",
  photo_url: "фото",
  role: "роль",
  session_id: "сеанс",
  state: "состояние",
  specs: "характеристики",
  surname: "фамилия",
  target_email: "email",
  target_role: "роль",
  title: "название",
  updated_fields: "изменённые поля",
  user_agent: "User-Agent",
  user_id: "пользователь",
  width: "ширина",
  x: "ряд",
  y: "место",
});

const ACTION_LABELS = Object.freeze({
  "auth.login": "Вход в систему",
  "auth.refresh": "Обновление сессии",
  "auth.refresh_reuse": "Повторное использование refresh token",
  "auth.logout": "Выход из системы",
  "auth.logout_all": "Выход со всех устройств",
  "auth.session_revoke": "Отзыв сеанса",
  "auth.register_by_invite": "Регистрация по приглашению",
  "audience.create": "Создание аудитории",
  "audience.update": "Обновление аудитории",
  "audience.delete": "Удаление аудитории",
  "office.create": "Создание корпуса",
  "office.update": "Обновление корпуса",
  "office.delete": "Удаление корпуса",
  "hardware.file_add": "Добавление файлов к оборудованию",
  "hardware.update": "Обновление оборудования",
  "hardware.file_delete": "Удаление файлов оборудования",
  "user.create": "Создание пользователя",
  "user.update": "Изменение пользователя",
  "user.delete": "Удаление пользователя",
  "user.password_change": "Смена пароля",
  "user.photo_upload": "Загрузка фото",
  "user.photo_delete": "Удаление фото",
  "invite.create": "Создание приглашения",
  "invite.create_batch": "Массовое создание приглашений",
  "invite.revoke": "Отзыв приглашения",
  "invite.delete": "Удаление приглашения",
});

const AUDIT_ACTION_OPTIONS = Object.freeze(
  Object.entries(ACTION_LABELS)
    .map(([value, label]) => ({ value, label }))
    .sort((left, right) => left.label.localeCompare(right.label, "ru"))
);

const AUDIT_ENTITY_TYPE_OPTIONS = Object.freeze(
  Object.entries(ENTITY_LABELS)
    .map(([value, label]) => ({ value, label }))
    .sort((left, right) => left.label.localeCompare(right.label, "ru"))
);

function normalizeString(value) {
  return String(value ?? "").trim();
}

function normalizeLower(value) {
  return normalizeString(value).toLowerCase();
}

function toArray(value) {
  if (Array.isArray(value)) return value;
  if (value == null) return [];
  return [value];
}

function uniqueStrings(values) {
  const seen = new Set();
  const result = [];

  values.forEach((value) => {
    const normalized = normalizeString(value);
    if (!normalized) return;

    const key = normalized.toLowerCase();
    if (seen.has(key)) return;

    seen.add(key);
    result.push(normalized);
  });

  return result;
}

function truncateText(value, maxLength = 120) {
  const normalized = normalizeString(value);
  if (!normalized) return "";
  if (normalized.length <= maxLength) return normalized;
  return `${normalized.slice(0, maxLength - 1)}…`;
}

function humanizeToken(value) {
  const normalized = normalizeString(value);
  if (!normalized) return "";

  return normalized
    .replace(/[._-]+/g, " ")
    .replace(/\s+/g, " ")
    .replace(/^\w/, (char) => char.toUpperCase());
}

function formatCount(value, one, few, many) {
  const count = Number(value);
  if (!Number.isFinite(count)) return "";

  const mod10 = count % 10;
  const mod100 = count % 100;

  if (mod10 === 1 && mod100 !== 11) return `${count} ${one}`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return `${count} ${few}`;
  return `${count} ${many}`;
}

function formatAuditDateTime(value) {
  if (!value) return "—";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

function getAuditCreatedAtTimestamp(log) {
  const rawValue = log?.created_at ?? log?.createdAt;
  const date = new Date(rawValue);
  const timestamp = date.getTime();

  return Number.isNaN(timestamp) ? 0 : timestamp;
}

function getAuditLogNumericId(log) {
  const numericId = Number(log?.id);
  return Number.isFinite(numericId) ? numericId : 0;
}

function formatMaybeDate(value) {
  const normalized = normalizeString(value);
  if (!normalized) return "";

  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return normalized;

  return formatAuditDateTime(date);
}

function formatStateLabel(value) {
  if (value === true) return "исправно";
  if (value === false) return "неисправно";
  return "";
}

function getActorTitleLabel(item) {
  if (item?.user?.email) return item.user.email;
  if (item?.user_id != null) return `Пользователь #${item.user_id}`;
  return "";
}

function getActorMetaLabel(item) {
  return getActorTitleLabel(item) || "Система";
}

function getEntityTypeLabel(entityType) {
  const normalized = normalizeLower(entityType);
  if (!normalized) return "";
  return ENTITY_LABELS[normalized] || humanizeToken(normalized);
}

function getEntityLabel(entityType, entityId) {
  const typeLabel = getEntityTypeLabel(entityType);

  if (!typeLabel && entityId == null) return "";
  if (entityId == null) return typeLabel || "";

  return `${typeLabel || "Сущность"} #${entityId}`;
}

function buildActionLabel(action) {
  return ACTION_LABELS[action] || humanizeToken(action) || "Неизвестное действие";
}

function getAuditToneClass(action) {
  const normalized = normalizeLower(action);

  if (
    normalized.endsWith(".delete") ||
    normalized.endsWith(".revoke") ||
    normalized === "auth.refresh_reuse"
  ) {
    return "tone-danger";
  }

  if (
    normalized.endsWith(".create") ||
    normalized === "invite.create_batch" ||
    normalized === "auth.login" ||
    normalized === "auth.register_by_invite"
  ) {
    return "tone-success";
  }

  if (
    normalized.endsWith(".update") ||
    normalized.endsWith(".file_add") ||
    normalized.endsWith(".file_delete") ||
    normalized === "user.password_change" ||
    normalized === "auth.logout_all" ||
    normalized === "auth.session_revoke" ||
    normalized === "auth.refresh"
  ) {
    return "tone-warning";
  }

  return "tone-neutral";
}

function getAuditMethodBadgeClass(method) {
  const normalized = normalizeLower(method).toUpperCase();
  const map = {
    GET: "badge-get",
    POST: "badge-post",
    PUT: "badge-put",
    PATCH: "badge-put",
    DELETE: "badge-delete",
  };

  return map[normalized] || "badge-default";
}

function getFieldLabel(field) {
  const normalized = normalizeLower(field);
  return FIELD_LABELS[normalized] || humanizeToken(normalized).toLowerCase();
}

function getChangedFields(payload) {
  const fields = payload?.changed_fields ?? payload?.changedFields ?? payload?.updated_fields ?? payload?.updatedFields;
  if (!fields) return [];

  return uniqueStrings(
    toArray(fields).map((field) => getFieldLabel(field))
  );
}

function formatChangedFieldsSummary(payload) {
  const changedFields = getChangedFields(payload);
  if (!changedFields.length) return "";

  return `Изменены поля: ${changedFields.join(", ")}`;
}

function getPayloadEmails(payload) {
  const emails = toArray(payload?.emails ?? payload?.target_emails ?? payload?.targetEmails)
    .map((value) => normalizeString(value))
    .filter(Boolean);

  const singleEmail = normalizeString(payload?.target_email ?? payload?.email);
  if (singleEmail) emails.unshift(singleEmail);

  return uniqueStrings(emails);
}

function getInviteCount(payload) {
  const explicitCount = Number(payload?.count ?? payload?.created_count ?? payload?.createdCount);
  if (Number.isFinite(explicitCount) && explicitCount > 0) return explicitCount;

  const emails = getPayloadEmails(payload);
  if (emails.length) return emails.length;

  const invites = payload?.invites ?? payload?.invite_urls ?? payload?.inviteIds ?? payload?.invite_ids;
  if (Array.isArray(invites) && invites.length) return invites.length;

  return null;
}

function getRoleLabelFromPayload(payload) {
  const role = payload?.target_role ?? payload?.role ?? payload?.new_role ?? payload?.user_role;
  if (role == null || role === "") return "";

  const inviteRoleLabel = getInviteRoleLabel(role);
  if (inviteRoleLabel && inviteRoleLabel !== "Не указано") return inviteRoleLabel.toLowerCase();

  return humanizeToken(role).toLowerCase();
}

function getSessionIdentifier(payload) {
  return normalizeString(
    payload?.session_id ??
    payload?.revoked_session_id ??
    payload?.sessionId ??
    payload?.refresh_jti ??
    payload?.jti
  );
}

function getFileNames(payload) {
  const source = payload?.files ?? payload?.file_names ?? payload?.fileNames ?? payload?.filenames ?? payload?.file_ids;
  if (!source) return [];

  return uniqueStrings(
    toArray(source).map((item) => {
      if (typeof item === "string") return item;
      if (typeof item === "number") return `#${item}`;

      return normalizeString(
        item?.original_name ??
        item?.originalName ??
        item?.file_name ??
        item?.filename ??
        item?.name ??
        item?.id
      );
    })
  );
}

function getFileCount(payload) {
  const explicitCount = Number(payload?.file_count ?? payload?.fileCount ?? payload?.files_count ?? payload?.filesCount);
  if (Number.isFinite(explicitCount) && explicitCount > 0) return explicitCount;

  const fileNames = getFileNames(payload);
  return fileNames.length || null;
}

function formatFileSummary(payload) {
  const count = getFileCount(payload);
  if (!count) return "";

  const names = getFileNames(payload);
  const head = names.slice(0, 3).join(", ");
  const tail = names.length > 3 ? ` +${names.length - 3}` : "";
  const base = formatCount(count, "файл", "файла", "файлов");

  return head ? `${base}: ${truncateText(`${head}${tail}`, 88)}` : base;
}

function buildGridLabel(payload) {
  const width = Number(payload?.width);
  const height = Number(payload?.height);

  if (!Number.isFinite(width) || !Number.isFinite(height)) return "";
  return `${width}×${height}`;
}

function formatEntityTail(entityLabel) {
  return entityLabel ? entityLabel.toLowerCase() : "сущность";
}

function withActor(actorLabel, actorPhrase, fallbackPhrase) {
  return actorLabel ? `${actorLabel} ${actorPhrase}` : fallbackPhrase;
}

function buildGenericUpdateSummary(payload, fallbackText = "Изменения сохранены.") {
  return formatChangedFieldsSummary(payload) || fallbackText;
}

function buildInviteCreateBatchSummary(payload) {
  const count = getInviteCount(payload);
  const roleLabel = getRoleLabelFromPayload(payload);
  const emails = getPayloadEmails(payload);
  const expiresAt = formatMaybeDate(payload?.expires_at ?? payload?.expiresAt);

  const parts = [];

  if (count) {
    parts.push(`Создано ${formatCount(count, "приглашение", "приглашения", "приглашений")}`);
  } else {
    parts.push("Созданы приглашения");
  }

  if (roleLabel) {
    parts.push(`для роли ${roleLabel}`);
  }

  parts.push(emails.length ? "тип: адресные" : "тип: массовые");

  if (expiresAt) {
    parts.push(`срок до ${expiresAt}`);
  }

  return parts.join(" • ");
}

function buildInviteSingleSummary(payload) {
  const roleLabel = getRoleLabelFromPayload(payload);
  const emails = getPayloadEmails(payload);
  const expiresAt = formatMaybeDate(payload?.expires_at ?? payload?.expiresAt);
  const parts = [];

  if (emails.length) parts.push(`для ${emails[0]}`);
  if (roleLabel) parts.push(`роль: ${roleLabel}`);
  if (expiresAt) parts.push(`до ${expiresAt}`);

  return parts.join(" • ");
}

function buildAudienceLocationSummary(payload) {
  const officeId = payload?.office_id ?? payload?.officeId;
  const floor = payload?.floor;
  const grid = buildGridLabel(payload);
  const parts = [];

  if (officeId != null && officeId !== "") parts.push(`корпус #${officeId}`);
  if (floor != null && floor !== "") parts.push(`этаж ${floor}`);
  if (grid) parts.push(`сетка ${grid}`);

  return parts.join(" • ");
}

function buildOfficeSummary(payload) {
  const address = truncateText(payload?.address, 90);
  return address ? `Адрес: ${address}` : "Изменения по корпусу сохранены.";
}

function buildHardwareUpdateSummary(payload) {
  const changedFields = formatChangedFieldsSummary(payload);
  if (changedFields) return changedFields;

  const state = formatStateLabel(payload?.state);
  if (state) return `Состояние: ${state}.`;

  return "Параметры оборудования обновлены.";
}

function buildUserSummary(payload) {
  const changedFields = formatChangedFieldsSummary(payload);
  if (changedFields) return changedFields;

  const roleLabel = getRoleLabelFromPayload(payload);
  const email = normalizeString(payload?.email ?? payload?.target_email);
  const parts = [];

  if (email) parts.push(email);
  if (roleLabel) parts.push(`роль: ${roleLabel}`);

  return parts.join(" • ") || "Изменения по пользователю сохранены.";
}

function buildRawPayload(payload) {
  if (!payload || typeof payload !== "object" || !Object.keys(payload).length) return "";

  try {
    return JSON.stringify(payload, null, 2);
  } catch {
    return String(payload);
  }
}

function maybePushRow(rows, label, value, options = {}) {
  const normalizedLabel = normalizeString(label);
  if (!normalizedLabel) return;

  let normalizedValue = "";

  if (Array.isArray(value)) {
    normalizedValue = value.filter(Boolean).join(", ");
  } else {
    normalizedValue = normalizeString(value);
  }

  if (!normalizedValue) return;

  const finalValue = options.truncate ? truncateText(normalizedValue, options.truncate) : normalizedValue;

  rows.push({
    label: normalizedLabel,
    value: finalValue,
  });
}

function buildPayloadDetailRows(payload) {
  const rows = [];
  if (!payload || typeof payload !== "object") return rows;

  maybePushRow(rows, "Изменённые поля", getChangedFields(payload).join(", "));
  maybePushRow(rows, "Email", getPayloadEmails(payload)[0]);

  const emailCount = getPayloadEmails(payload).length;
  if (emailCount > 1) {
    maybePushRow(rows, "Список email", formatCount(emailCount, "адрес", "адреса", "адресов"));
  }

  maybePushRow(rows, "Роль", getRoleLabelFromPayload(payload));
  maybePushRow(rows, "Срок действия", formatMaybeDate(payload?.expires_at ?? payload?.expiresAt));
  maybePushRow(rows, "Примечание", payload?.note, { truncate: 120 });
  maybePushRow(rows, "Состояние", formatStateLabel(payload?.state));
  maybePushRow(rows, "Название", payload?.title ?? payload?.name, { truncate: 96 });
  maybePushRow(rows, "Инвентарный номер", payload?.inv_number);
  maybePushRow(rows, "Корпус", payload?.office_id ?? payload?.officeId);
  maybePushRow(rows, "Этаж", payload?.floor);
  maybePushRow(rows, "Сетка", buildGridLabel(payload));
  maybePushRow(rows, "Сеанс", getSessionIdentifier(payload), { truncate: 72 });
  maybePushRow(rows, "Файлы", formatFileSummary(payload), { truncate: 96 });

  return rows;
}

function buildTechnicalRows(log) {
  const rows = [];

  maybePushRow(rows, "Метод", normalizeString(log?.method).toUpperCase());
  maybePushRow(rows, "Путь", log?.path, { truncate: 120 });
  maybePushRow(rows, "IP-адрес", log?.ip);
  maybePushRow(rows, "User-Agent", log?.user_agent ?? log?.userAgent, { truncate: 160 });

  return rows;
}

function buildSummaryTags(log, payloadRows) {
  const tags = [];

  const method = normalizeString(log?.method).toUpperCase();
  if (method) tags.push(method);

  payloadRows.forEach((row) => {
    if (row.label === "Изменённые поля" || row.label === "Примечание") return;
    tags.push(`${row.label}: ${row.value}`);
  });

  return uniqueStrings(tags).slice(0, 4);
}

function buildListMeta(log, actorMetaLabel, entityLabel) {
  const meta = [];

  meta.push(formatAuditDateTime(log?.created_at ?? log?.createdAt));
  if (actorMetaLabel) meta.push(actorMetaLabel);
  if (entityLabel) meta.push(entityLabel);

  const path = normalizeString(log?.path);
  const method = normalizeString(log?.method).toUpperCase();
  if (path) meta.push(method ? `${method} ${path}` : path);

  return meta;
}

function formatFallbackAction(log, payload, actorLabel, entityLabel) {
  const actionLabel = buildActionLabel(log?.action);
  const passiveTitle = entityLabel
    ? `${actionLabel}: ${entityLabel}`
    : actionLabel;

  return {
    title: withActor(actorLabel, `выполнил действие «${actionLabel.toLowerCase()}»`, passiveTitle),
    summary: formatChangedFieldsSummary(payload) || "Подробности события доступны в карточке записи.",
  };
}

const ACTION_FORMATTERS = Object.freeze({
  "auth.login": ({ actorLabel }) => ({
    title: withActor(actorLabel, "вошёл в систему", "Выполнен вход в систему"),
    summary: "Авторизация выполнена успешно.",
  }),
  "auth.refresh": ({ actorLabel }) => ({
    title: withActor(actorLabel, "обновил сессию", "Сессия обновлена"),
    summary: "Срок действия активной сессии продлён.",
  }),
  "auth.refresh_reuse": ({ actorLabel }) => ({
    title: withActor(actorLabel, "повторно использовал refresh token", "Обнаружено повторное использование refresh token"),
    summary: "Зафиксировано потенциально небезопасное повторное обновление сессии.",
  }),
  "auth.logout": ({ actorLabel }) => ({
    title: withActor(actorLabel, "вышел из системы", "Выполнен выход из системы"),
    summary: "Активный сеанс завершён.",
  }),
  "auth.logout_all": ({ actorLabel }) => ({
    title: withActor(actorLabel, "завершил все сеансы", "Выполнен выход со всех устройств"),
    summary: "Все активные сеансы пользователя были завершены.",
  }),
  "auth.session_revoke": ({ actorLabel, payload }) => ({
    title: withActor(actorLabel, "отозвал сеанс", "Сеанс отозван"),
    summary: getSessionIdentifier(payload)
      ? `Отозван сеанс ${truncateText(getSessionIdentifier(payload), 64)}.`
      : "Один из активных сеансов был отозван.",
  }),
  "auth.register_by_invite": ({ payload }) => ({
    title: "Пользователь зарегистрирован по приглашению",
    summary: (() => {
      const email = getPayloadEmails(payload)[0];
      const roleLabel = getRoleLabelFromPayload(payload);
      const parts = [];
      if (email) parts.push(email);
      if (roleLabel) parts.push(`роль: ${roleLabel}`);
      return parts.join(" • ") || "Завершена регистрация нового пользователя по приглашению.";
    })(),
  }),
  "audience.create": ({ actorLabel, entityLabel, payload }) => ({
    title: withActor(actorLabel, `создал ${formatEntityTail(entityLabel)}`, entityLabel ? `Создана ${formatEntityTail(entityLabel)}`.replace(/^./, (c) => c.toUpperCase()) : "Создана аудитория"),
    summary: buildAudienceLocationSummary(payload) || "Новая аудитория добавлена в систему.",
  }),
  "audience.update": ({ actorLabel, entityLabel, payload }) => ({
    title: withActor(actorLabel, `обновил ${formatEntityTail(entityLabel)}`, entityLabel ? `Обновлена ${formatEntityTail(entityLabel)}`.replace(/^./, (c) => c.toUpperCase()) : "Обновлена аудитория"),
    summary: buildGenericUpdateSummary(payload, "Параметры аудитории обновлены."),
  }),
  "audience.delete": ({ actorLabel, entityLabel }) => ({
    title: withActor(actorLabel, `удалил ${formatEntityTail(entityLabel)}`, entityLabel ? `Удалена ${formatEntityTail(entityLabel)}`.replace(/^./, (c) => c.toUpperCase()) : "Аудитория удалена"),
    summary: "Аудитория удалена из системы.",
  }),
  "office.create": ({ actorLabel, entityLabel, payload }) => ({
    title: withActor(actorLabel, `создал ${formatEntityTail(entityLabel)}`, entityLabel ? `Создан ${formatEntityTail(entityLabel)}`.replace(/^./, (c) => c.toUpperCase()) : "Создан корпус"),
    summary: buildOfficeSummary(payload),
  }),
  "office.update": ({ actorLabel, entityLabel, payload }) => ({
    title: withActor(actorLabel, `обновил ${formatEntityTail(entityLabel)}`, entityLabel ? `Обновлён ${formatEntityTail(entityLabel)}`.replace(/^./, (c) => c.toUpperCase()) : "Обновлён корпус"),
    summary: buildGenericUpdateSummary(payload, buildOfficeSummary(payload)),
  }),
  "office.delete": ({ actorLabel, entityLabel }) => ({
    title: withActor(actorLabel, `удалил ${formatEntityTail(entityLabel)}`, entityLabel ? `Удалён ${formatEntityTail(entityLabel)}`.replace(/^./, (c) => c.toUpperCase()) : "Корпус удалён"),
    summary: "Корпус удалён из системы.",
  }),
  "hardware.file_add": ({ actorLabel, entityLabel, payload }) => ({
    title: withActor(actorLabel, `добавил файлы к ${formatEntityTail(entityLabel)}`, entityLabel ? `К ${formatEntityTail(entityLabel)} добавлены файлы`.replace(/^./, (c) => c.toUpperCase()) : "Файлы добавлены к оборудованию"),
    summary: formatFileSummary(payload) || "К оборудованию добавлены новые файлы.",
  }),
  "hardware.update": ({ actorLabel, entityLabel, payload }) => ({
    title: withActor(actorLabel, `обновил ${formatEntityTail(entityLabel)}`, entityLabel ? `Обновлено ${formatEntityTail(entityLabel)}`.replace(/^./, (c) => c.toUpperCase()) : "Оборудование обновлено"),
    summary: buildHardwareUpdateSummary(payload),
  }),
  "hardware.file_delete": ({ actorLabel, entityLabel, payload }) => ({
    title: withActor(actorLabel, `удалил файлы у ${formatEntityTail(entityLabel)}`, entityLabel ? `У ${formatEntityTail(entityLabel)} удалены файлы`.replace(/^./, (c) => c.toUpperCase()) : "Файлы оборудования удалены"),
    summary: formatFileSummary(payload) || "Файлы оборудования удалены.",
  }),
  "user.create": ({ actorLabel, entityLabel, payload }) => ({
    title: withActor(actorLabel, `создал ${formatEntityTail(entityLabel)}`, entityLabel ? `Создан ${formatEntityTail(entityLabel)}`.replace(/^./, (c) => c.toUpperCase()) : "Создан пользователь"),
    summary: buildUserSummary(payload),
  }),
  "user.update": ({ actorLabel, entityLabel, payload, log }) => ({
    title: (() => {
      if (actorLabel && log?.user_id != null && log?.entity_id != null && Number(log.user_id) === Number(log.entity_id)) {
        return `${actorLabel} обновил свой профиль`;
      }

      return withActor(actorLabel, `изменил ${formatEntityTail(entityLabel)}`, entityLabel ? `Изменён ${formatEntityTail(entityLabel)}`.replace(/^./, (c) => c.toUpperCase()) : "Изменён пользователь");
    })(),
    summary: buildUserSummary(payload),
  }),
  "user.delete": ({ actorLabel, entityLabel }) => ({
    title: withActor(actorLabel, `удалил ${formatEntityTail(entityLabel)}`, entityLabel ? `Удалён ${formatEntityTail(entityLabel)}`.replace(/^./, (c) => c.toUpperCase()) : "Пользователь удалён"),
    summary: "Пользователь удалён из системы.",
  }),
  "user.password_change": ({ actorLabel, entityLabel, log }) => ({
    title: (() => {
      if (actorLabel && log?.user_id != null && log?.entity_id != null && Number(log.user_id) === Number(log.entity_id)) {
        return `${actorLabel} сменил пароль`;
      }

      return withActor(actorLabel, `сменил пароль для ${formatEntityTail(entityLabel)}`, entityLabel ? `Изменён пароль для ${formatEntityTail(entityLabel)}`.replace(/^./, (c) => c.toUpperCase()) : "Пароль изменён");
    })(),
    summary: "Пароль пользователя был обновлён.",
  }),
  "user.photo_upload": ({ actorLabel, entityLabel, log }) => ({
    title: (() => {
      if (actorLabel && log?.user_id != null && log?.entity_id != null && Number(log.user_id) === Number(log.entity_id)) {
        return `${actorLabel} загрузил фото профиля`;
      }

      return withActor(actorLabel, `загрузил фото для ${formatEntityTail(entityLabel)}`, entityLabel ? `Загружено фото для ${formatEntityTail(entityLabel)}`.replace(/^./, (c) => c.toUpperCase()) : "Фото пользователя загружено");
    })(),
    summary: "Фотография профиля успешно загружена.",
  }),
  "user.photo_delete": ({ actorLabel, entityLabel, log }) => ({
    title: (() => {
      if (actorLabel && log?.user_id != null && log?.entity_id != null && Number(log.user_id) === Number(log.entity_id)) {
        return `${actorLabel} удалил фото профиля`;
      }

      return withActor(actorLabel, `удалил фото у ${formatEntityTail(entityLabel)}`, entityLabel ? `Удалено фото у ${formatEntityTail(entityLabel)}`.replace(/^./, (c) => c.toUpperCase()) : "Фото пользователя удалено");
    })(),
    summary: "Фотография профиля удалена.",
  }),
  "invite.create": ({ actorLabel, payload }) => ({
    title: withActor(actorLabel, "создал приглашение", "Создано приглашение"),
    summary: buildInviteSingleSummary(payload),
  }),
  "invite.create_batch": ({ actorLabel, payload }) => ({
    title: withActor(actorLabel, "создал несколько приглашений", "Созданы приглашения"),
    summary: buildInviteCreateBatchSummary(payload),
  }),
  "invite.revoke": ({ actorLabel, payload }) => ({
    title: withActor(actorLabel, "отозвал приглашение", "Приглашение отозвано"),
    summary: buildInviteSingleSummary(payload) || "Приглашение больше не может быть использовано.",
  }),
  "invite.delete": ({ actorLabel, payload }) => ({
    title: withActor(actorLabel, "удалил приглашение", "Приглашение удалено"),
    summary: buildInviteSingleSummary(payload) || "Приглашение удалено из системы.",
  }),
});

export function formatAuditLogEntry(log) {
  const payload = log?.payload && typeof log.payload === "object" ? log.payload : null;
  const actorLabel = getActorTitleLabel(log);
  const actorMetaLabel = getActorMetaLabel(log);
  const entityLabel = getEntityLabel(log?.entity_type, log?.entity_id);
  const actionLabel = buildActionLabel(log?.action);
  const formatter = ACTION_FORMATTERS[log?.action];
  const formatted = formatter
    ? formatter({ log, payload, actorLabel, actorMetaLabel, entityLabel, actionLabel })
    : formatFallbackAction(log, payload, actorLabel, entityLabel);

  const payloadDetailRows = buildPayloadDetailRows(payload);
  const technicalRows = buildTechnicalRows(log);

  return {
    id: log?.id,
    original: log,
    action: log?.action || "",
    actionLabel,
    toneClass: getAuditToneClass(log?.action),
    title: formatted.title,
    summary: formatted.summary,
    actorLabel: actorMetaLabel,
    entityLabel,
    createdAtLabel: formatAuditDateTime(log?.created_at ?? log?.createdAt),
    summaryTags: buildSummaryTags(log, payloadDetailRows),
    listMeta: buildListMeta(log, actorMetaLabel, entityLabel),
    methodBadgeClass: getAuditMethodBadgeClass(log?.method),
    methodLabel: normalizeString(log?.method).toUpperCase() || "ANY",
    pathLabel: normalizeString(log?.path) || "—",
    technicalRows,
    payloadDetailRows,
    rawPayload: buildRawPayload(payload),
    hasTechnicalRows: technicalRows.length > 0,
    hasPayloadDetails: payloadDetailRows.length > 0,
    hasRawPayload: Boolean(buildRawPayload(payload)),
  };
}

export function formatAuditListResponse(data) {
  if (Array.isArray(data)) {
    return {
      items: data,
      total: data.length,
    };
  }

  if (Array.isArray(data?.items)) {
    return {
      items: data.items,
      total: Number.isFinite(Number(data.total)) ? Number(data.total) : null,
    };
  }

  return {
    items: [],
    total: 0,
  };
}

export function sortAuditLogItems(items, order = "desc") {
  const direction = order === "asc" ? 1 : -1;

  return [...items]
    .map((item, index) => ({ item, index }))
    .sort((left, right) => {
      const timestampDiff = getAuditCreatedAtTimestamp(left.item) - getAuditCreatedAtTimestamp(right.item);
      if (timestampDiff !== 0) {
        return timestampDiff * direction;
      }

      const idDiff = getAuditLogNumericId(left.item) - getAuditLogNumericId(right.item);
      if (idDiff !== 0) {
        return idDiff * direction;
      }

      return left.index - right.index;
    })
    .map(({ item }) => item);
}

export {
  ACTION_LABELS,
  AUDIT_ACTION_OPTIONS,
  AUDIT_ENTITY_TYPE_OPTIONS,
  formatAuditDateTime,
  getAuditMethodBadgeClass,
  getAuditToneClass,
};
