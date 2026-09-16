class FloorPlanConflictError(Exception):
    detail = "Схема этажа уже изменена. Обновите страницу и повторите сохранение."


class FloorPlanRoomError(Exception):
    detail = "В схеме есть кабинет, не принадлежащий этому этажу корпуса."
