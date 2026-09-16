export const RU_EMAIL_ERROR_MESSAGE = 'Email должен быть в домене .ru';

export function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(email ?? '').trim());
}

export function isRuEmail(email) {
  return isValidEmail(email) && String(email).trim().split('@').pop().toLowerCase().endsWith('.ru');
}

export function getUserRoleLabel(role) {
  const normalized = String(role ?? '').trim().toLowerCase();
  if (['teacher', '2'].includes(normalized)) return 'Преподаватель';
  if (['admin', 'administrator', '1'].includes(normalized)) return 'Администратор';
  return role || 'Не указано';
}

export function mapUserApiError(error, fallback = 'Не удалось создать пользователя.') {
  const status = error?.response?.status;
  if (error?.code === 'ECONNABORTED' || error?.code === 'ETIMEDOUT') return 'Сервер отвечает слишком долго. Попробуйте ещё раз.';
  if (!error?.response) return error?.request ? 'Не удалось связаться с сервером. Проверьте подключение к сети.' : fallback;
  if (status === 401) return 'Необходимо войти в систему';
  if (status === 403) return 'Недостаточно прав для выполнения действия';
  if (status === 409) return 'Пользователь с таким email уже существует';
  if (status >= 500) return 'На сервере произошла ошибка. Попробуйте позже.';
  const detail = error.response.data?.detail;
  if (status === 422 && Array.isArray(detail)) {
    const item = detail[0];
    const field = item?.loc?.at(-1);
    if (field === 'email') return /\.ru/i.test(item.msg ?? '') ? RU_EMAIL_ERROR_MESSAGE : 'Введите корректный email';
    if (field === 'password') {
      const min = Number(item.ctx?.min_length);
      return Number.isFinite(min) && min > 0 ? `Пароль должен быть не короче ${min} символов` : 'Введите корректный пароль';
    }
    if (field === 'role') return 'Выберите корректную роль';
    return 'Проверьте корректность заполнения полей формы.';
  }
  if (typeof detail === 'string') {
    if (/\.ru/i.test(detail)) return RU_EMAIL_ERROR_MESSAGE;
    if (/user.*already exists/i.test(detail)) return 'Пользователь с таким email уже существует';
  }
  return fallback;
}
