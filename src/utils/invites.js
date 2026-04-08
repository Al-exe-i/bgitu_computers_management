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
  const normalized = String(reason ?? '').trim().toLowerCase();

  if (!normalized) return 'Приглашение недоступно.';
  if (normalized.includes('expired')) return 'Срок действия приглашения уже истек.';
  if (normalized.includes('revoked')) return 'Это приглашение было отозвано администратором.';
  if (normalized.includes('used')) return 'Это приглашение уже было использовано.';
  if (normalized.includes('not found') || normalized.includes('invalid')) {
    return 'Приглашение не найдено или ссылка повреждена.';
  }

  return reason;
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
