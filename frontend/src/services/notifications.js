import api from "@/services/api";

const NOTIFICATIONS_BASE = "/notifications";

export const getNotificationSubscriptions = () =>
  api.get(`${NOTIFICATIONS_BASE}/subscriptions`);

export const createNotificationSubscription = (payload) =>
  api.post(`${NOTIFICATIONS_BASE}/subscriptions`, payload);

export const deleteNotificationSubscription = (id) =>
  api.delete(`${NOTIFICATIONS_BASE}/subscriptions/${id}`);

export const getNotificationOfficesDictionary = () => api.get("/offices/all_short");

export const getNotificationAudiencesDictionary = () => api.get("/audiences");
