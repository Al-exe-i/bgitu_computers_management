export const INVITE_ROLE_OPTIONS = Object.freeze([
  { value: 2, label: 'Преподаватель' },
  { value: 1, label: 'Администратор' },
]);

export function normalizeInviteRoleValue(role) {
  const normalized = String(role ?? '').trim().toLowerCase();

  if (normalized === 'teacher' || normalized === '2') return 2;
  if (normalized === 'admin' || normalized === 'administrator' || normalized === '1') return 1;

  return null;
}

export function getInviteRoleLabel(role) {
  const normalizedRole = normalizeInviteRoleValue(role);

  if (normalizedRole === 2) return 'Преподаватель';
  if (normalizedRole === 1) return 'Администратор';

  return role || 'Не указано';
}

export function getInviteStatus(invite, now = new Date()) {
  if (invite?.used_at) return 'used';
  if (invite?.revoked_at) return 'revoked';

  if (invite?.expires_at) {
    const expiresAt = new Date(invite.expires_at);
    if (!Number.isNaN(expiresAt.getTime()) && expiresAt.getTime() < now.getTime()) {
      return 'expired';
    }
  }

  return 'active';
}

export function getInviteStatusLabel(status) {
  if (status === 'used') return 'Использована';
  if (status === 'revoked') return 'Отозвана';
  if (status === 'expired') return 'Истекла';
  return 'Активна';
}

export function formatInviteDate(value) {
  if (!value) return '—';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export function toLocalDateTimeInputValue(value) {
  if (!value) return '';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';

  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return localDate.toISOString().slice(0, 16);
}

export function getDefaultInviteExpiresAtValue(baseDate = new Date()) {
  const date = new Date(baseDate);
  if (Number.isNaN(date.getTime())) return '';

  date.setDate(date.getDate() + 30);
  date.setHours(0, 0, 0, 0);

  return toLocalDateTimeInputValue(date);
}

export function fromLocalDateTimeInputValue(value) {
  if (!value) return null;

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;

  return date.toISOString();
}

export function normalizeInviteListResponse(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.invites)) return data.invites;
  return [];
}

export function normalizeInviteCreateResponse(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.invites)) return data.invites;
  if (data && typeof data === 'object' && ('id' in data || 'invite_url' in data)) return [data];
  return [];
}

const INVITE_FIELD_LABELS = Object.freeze({
  token: 'Приглашение',
  email: 'Email',
  target_email: 'Email',
  emails: 'Список email-адресов',
  target_role: 'Роль',
  expires_at: 'Срок действия',
  note: 'Примечание',
  name: 'Имя',
  surname: 'Фамилия',
  password: 'Пароль',
});

export const RU_EMAIL_ERROR_MESSAGE = 'Email должен быть в домене .ru';
export const RU_EMAIL_LIST_ERROR_MESSAGE = 'Все email-адреса должны быть в домене .ru';

function normalizeInviteErrorText(value) {
  return String(value ?? '').trim().toLowerCase();
}

function isRuEmailDomainErrorText(value) {
  const normalized = normalizeInviteErrorText(value);

  return (
    normalized.includes('.ru domain') ||
    normalized.includes('must use a .ru') ||
    normalized.includes('email must use') ||
    normalized.includes('домене .ru')
  );
}

function getInviteFieldLabel(field) {
  return INVITE_FIELD_LABELS[String(field ?? '').trim()] ?? '';
}

function mapInviteKnownMessage(message) {
  const normalized = normalizeInviteErrorText(message);

  if (!normalized) return '';

  if (isRuEmailDomainErrorText(normalized)) return RU_EMAIL_ERROR_MESSAGE;

  if (
    normalized.includes('invite not found') ||
    normalized.includes('invalid invite') ||
    normalized.includes('invalid token') ||
    normalized.includes('invite_invalid')
  ) return 'Приглашение не найдено';

  if (normalized.includes('invite revoked')) return 'Приглашение отозвано';
  if (normalized.includes('invite expired')) return 'Срок действия приглашения истёк';
  if (normalized.includes('invite already used')) return 'Приглашение уже использовано';

  if (
    normalized.includes('this invite is assigned to another email') ||
    normalized.includes('assigned to another email') ||
    normalized.includes('for another email')
  ) return 'Это приглашение предназначено для другого email';

  if (
    normalized.includes('user with this email already exists') ||
    (normalized.includes('email') && normalized.includes('already exists'))
  ) return 'Пользователь с таким email уже существует';

  if (
    normalized.includes('not authenticated') ||
    normalized.includes('unauthorized') ||
    normalized.includes('authentication') ||
    normalized.includes('credentials') ||
    normalized.includes('login required')
  ) return 'Необходимо войти в систему';

  if (
    normalized.includes('permission') ||
    normalized.includes('forbidden') ||
    normalized.includes('access denied') ||
    normalized.includes('not enough rights')
  ) return 'Недостаточно прав для выполнения действия';

  if (normalized.includes('valid email')) return 'Введите корректный email';
  if (normalized.includes('expired')) return 'Срок действия приглашения истёк';
  if (normalized.includes('revoked')) return 'Приглашение отозвано';
  if (normalized.includes('already used') || normalized.includes('used')) return 'Приглашение уже использовано';
  if (normalized.includes('another email')) return 'Это приглашение предназначено для другого email';
  if (normalized.includes('not found') || normalized.includes('invalid')) return 'Приглашение не найдено';

  return '';
}

function getInviteResponseDetail(data) {
  if (!data) return null;

  if (Array.isArray(data?.detail)) return data.detail;
  if (typeof data?.detail === 'string') return data.detail;
  if (Array.isArray(data?.errors)) return data.errors;
  if (typeof data?.message === 'string') return data.message;
  if (typeof data?.error === 'string') return data.error;
  if (typeof data?.reason === 'string') return data.reason;
  if (typeof data === 'string') return data;

  return null;
}

function mapInviteValidationDetail(detail) {
  const location = Array.isArray(detail?.loc) ? detail.loc : [];
  const field = String(location[location.length - 1] ?? '').trim();
  const isEmailsField = location.map(item => String(item)).includes('emails');
  const label = getInviteFieldLabel(field);
  const message = normalizeInviteErrorText(detail?.msg);
  const type = normalizeInviteErrorText(detail?.type);
  const minLength = Number(detail?.ctx?.min_length);

  if (isRuEmailDomainErrorText(message) || isRuEmailDomainErrorText(type)) {
    return isEmailsField ? RU_EMAIL_LIST_ERROR_MESSAGE : RU_EMAIL_ERROR_MESSAGE;
  }

  if (field === 'token') return 'Приглашение не найдено';

  if (field === 'name') {
    return message.includes('required') || type.includes('missing')
      ? 'Введите имя'
      : 'Проверьте поле «Имя».';
  }

  if (field === 'surname') {
    return message.includes('required') || type.includes('missing')
      ? 'Введите фамилию'
      : 'Проверьте поле «Фамилия».';
  }

  if (field === 'email' || field === 'target_email') return 'Введите корректный email';
  if (field === 'emails') return 'Проверьте список email-адресов';

  if (field === 'password') {
    if (Number.isFinite(minLength) && minLength > 0) {
      return `Пароль должен быть не короче ${minLength} символов`;
    }

    return 'Введите корректный пароль';
  }

  if (field === 'target_role') return 'Выберите корректную роль';
  if (field === 'expires_at') return 'Укажите корректную дату окончания действия приглашения';

  if (message.includes('field required') || type.includes('missing')) {
    return label ? `Заполните поле «${label}».` : 'Заполните обязательные поля.';
  }

  if (message.includes('valid email') || type.includes('email')) {
    return 'Введите корректный email';
  }

  if (
    message.includes('valid datetime') ||
    message.includes('valid date') ||
    type.includes('datetime') ||
    type.includes('date')
  ) {
    return 'Укажите корректную дату окончания действия приглашения';
  }

  if (type.includes('too_short') || message.includes('at least')) {
    if (Number.isFinite(minLength) && minLength > 0 && field === 'password') {
      return `Пароль должен быть не короче ${minLength} символов`;
    }

    return label ? `Проверьте длину поля «${label}».` : 'Проверьте длину введённых данных.';
  }

  if (type.includes('enum') || type.includes('literal')) {
    return label ? `Выберите корректное значение поля «${label}».` : 'Выберите корректное значение.';
  }

  return label ? `Проверьте поле «${label}».` : 'Проверьте корректность заполнения полей.';
}

function mapInviteStatusCode(status, fallbackMessage) {
  if (status === 400) return fallbackMessage || 'Запрос отклонён. Проверьте данные приглашения.';
  if (status === 401) return 'Необходимо войти в систему';
  if (status === 403) return 'Недостаточно прав для выполнения действия';
  if (status === 404) return 'Приглашение не найдено';
  if (status === 409) return 'Возник конфликт данных. Проверьте email и состояние приглашения.';
  if (status === 422) return 'Проверьте корректность заполнения полей формы.';
  if (status >= 500) return 'На сервере произошла ошибка. Попробуйте позже.';

  return fallbackMessage || 'Не удалось выполнить операцию с приглашением.';
}

export function mapInviteApiError(error, fallbackMessage = 'Не удалось выполнить операцию с приглашением.') {
  const errorCode = normalizeInviteErrorText(error?.code);
  const errorMessage = normalizeInviteErrorText(error?.message);

  if (errorCode === 'econnaborted' || errorMessage.includes('timeout')) {
    return 'Сервер отвечает слишком долго. Попробуйте ещё раз.';
  }

  if (!error?.response) {
    if (error?.request || errorMessage.includes('network') || errorMessage.includes('failed to fetch')) {
      return 'Не удалось связаться с сервером. Проверьте подключение к сети.';
    }

    return fallbackMessage;
  }

  const detail = getInviteResponseDetail(error.response.data);

  if (Array.isArray(detail) && detail.length > 0) {
    return mapInviteValidationDetail(detail[0]);
  }

  if (typeof detail === 'string') {
    const mappedDetail = mapInviteKnownMessage(detail);

    if (mappedDetail) {
      return mappedDetail;
    }
  }

  return mapInviteStatusCode(error.response.status, fallbackMessage);
}

export function copyTextToClipboard(text) {
  if (!text) return Promise.reject(new Error('Nothing to copy'));

  if (navigator?.clipboard?.writeText) {
    return navigator.clipboard.writeText(text);
  }

  return new Promise((resolve, reject) => {
    try {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.setAttribute('readonly', '');
      textarea.style.position = 'fixed';
      textarea.style.top = '-9999px';
      textarea.style.opacity = '0';

      document.body.appendChild(textarea);
      textarea.select();
      const success = document.execCommand('copy');
      document.body.removeChild(textarea);

      if (success) resolve();
      else reject(new Error('Copy command failed'));
    } catch (error) {
      reject(error);
    }
  });
}

export function getInviteReasonText(reason) {
  const mappedReason = mapInviteKnownMessage(reason);
  return mappedReason || 'Приглашение недоступно. Попросите администратора отправить новую ссылку.';
}

export function parseInviteEmails(rawValue) {
  return Array.from(
    new Set(
      String(rawValue ?? '')
        .split(/[\n,;]+/g)
        .map(item => item.trim())
        .filter(Boolean)
    )
  );
}

export function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(email ?? '').trim());
}

export function isRuEmail(email) {
  if (!isValidEmail(email)) return false;

  const domain = String(email ?? '').trim().split('@').pop()?.toLowerCase() ?? '';
  return domain.endsWith('.ru');
}
