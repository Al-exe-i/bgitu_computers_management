export function passwordStrength(value) {
  const text = String(value || '');
  if (!text) return { score: 0, label: 'От 6 символов; лучше длинная уникальная фраза' };
  const common = /password|qwerty|123456|пароль|йцукен/i.test(text);
  const repeated = /^(.{1,4})\1+$/u.test(text);
  const unique = new Set(text.toLocaleLowerCase()).size;
  if (text.length < 10 || common || repeated || unique < 5) return { score: 1, label: 'Слабый: увеличьте длину, избегайте повторов' };
  const characterTypes = [/\p{Ll}/u, /\p{Lu}/u, /\p{N}/u, /[^\p{L}\p{N}\s]/u]
    .filter(pattern => pattern.test(text)).length;
  const varied = text.length >= 14 && unique >= 10 && characterTypes === 4;
  const long = text.length >= 16 && unique >= 8;
  if (!varied && !long) return { score: 2, label: 'Средний: добавьте длину или разнообразие символов' };
  return { score: 3, label: 'Хорошая длина и разнообразие символов' };
}
