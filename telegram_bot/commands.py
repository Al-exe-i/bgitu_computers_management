from aiogram.types import BotCommand


def build_default_commands() -> list[BotCommand]:
    return [
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="status", description="Статус привязки"),
        BotCommand(command="subscriptions", description="Мои подписки"),
        BotCommand(command="help", description="Справка"),
    ]
