import logging
import sys

from core.config import settings


def setup_logger(name: str = "app") -> logging.Logger:
    """
    Настраивает и возвращает логгер.

    Args:
        name: Имя логгера (по умолчанию "app")
        log_file: Путь к файлу логов
        log_level: Уровень логирования (DEBUG, INFO и т.д.)
        json_format: Использовать JSON-формат для файловых логов

    Returns:
        logging.Logger
    """
    logger = logging.getLogger(name)

    # Избегаем дублирования хендлеров при повторных вызовах
    if logger.handlers:
        return logger

    log_level = settings.logger.level
    logger.setLevel(log_level)

    # --- Консольный вывод (всегда читаемый) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        settings.logger.format,
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    return logger