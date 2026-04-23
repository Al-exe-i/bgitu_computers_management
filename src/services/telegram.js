import api from "@/services/api";

const TELEGRAM_BASE = "/telegram";

export const getTelegramStatus = () => api.get(`${TELEGRAM_BASE}/me`);

export const createTelegramLinkToken = () => api.post(`${TELEGRAM_BASE}/link-token`);

export const unlinkTelegramAccount = () => api.delete(`${TELEGRAM_BASE}/link`);

export const getTelegramSubscriptions = () => api.get(`${TELEGRAM_BASE}/subscriptions`);

export const createTelegramSubscription = (payload) =>
  api.post(`${TELEGRAM_BASE}/subscriptions`, payload);

export const deleteTelegramSubscription = (id) =>
  api.delete(`${TELEGRAM_BASE}/subscriptions/${id}`);

export const getTelegramOfficesDictionary = () => api.get("/offices/all_short");

export const getTelegramAudiencesDictionary = () => api.get("/audiences");
