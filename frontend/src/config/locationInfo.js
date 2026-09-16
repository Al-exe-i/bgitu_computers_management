export const FLOOR_INFO_FIELDS = Object.freeze([
  { key: 'name', label: 'Название', max: 120 },
  { key: 'description', label: 'Описание', multiline: true, max: 4000 },
]);
export const OFFICE_INFO_FIELDS = Object.freeze([
  { key: 'address', label: 'Адрес', readonly: true },
  ...FLOOR_INFO_FIELDS,
  { key: 'internet_provider', label: 'Интернет-провайдер', max: 120 },
]);
