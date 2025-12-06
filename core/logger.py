# core/logger.py
import logging
import sys
from loguru import logger

# Настройка формата логов
# <green>{time:YYYY-MM-DD HH:mm:ss}</green> - время
# <level>{level: <8}</level> - уровень лога (INFO, ERROR...) с выравниванием
# <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - модуль:функция:строка
# <level>{message}</level> - само сообщение
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Получаем соответствующий уровень лога Loguru
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Находим глубину стека, чтобы лог указывал на правильное место вызова
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    # Удаляем стандартный обработчик Loguru (чтобы не дублировать)
    logger.remove()

    # Добавляем вывод в консоль (sys.stderr) с цветами
    logger.add(
        sys.stderr,
        format=LOG_FORMAT,
        level="INFO",
        colorize=True
    )

    # Добавляем вывод в файл (с ротацией и архивацией)
    # rotation="10 MB" - новый файл каждые 10 МБ
    # retention="10 days" - хранить логи 10 дней
    # compression="zip" - сжимать старые логи
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="10 days",
        compression="zip",
        level="DEBUG",  # В файл пишем всё, включая отладку
        format=LOG_FORMAT
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0)

    loggers_to_intercept = [
        "uvicorn",
        "uvicorn.error",
        "fastapi",
        "sqlalchemy.engine",
    ]

    for _log in loggers_to_intercept:
        _logger = logging.getLogger(_log)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False
        _logger.setLevel("INFO")

    return logger