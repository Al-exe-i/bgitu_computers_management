from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BUTTON_MENU = "📋 Главное меню"
BUTTON_STATUS = "🔗 Мой статус"
BUTTON_SUBSCRIPTIONS = "🔔 Мои подписки"
BUTTON_LINK = "🧭 Как подключить"
BUTTON_HELP = "❓ Помощь"


def build_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTON_MENU)],
            [
                KeyboardButton(text=BUTTON_STATUS),
                KeyboardButton(text=BUTTON_SUBSCRIPTIONS),
            ],
            [
                KeyboardButton(text=BUTTON_LINK),
                KeyboardButton(text=BUTTON_HELP),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )
