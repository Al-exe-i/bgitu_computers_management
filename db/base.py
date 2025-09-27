# Импортируем все модели, чтобы Alembic их видел
from models.base import Base
from models.user import User  # обязательно импортировать!

# Эта строка нужна, чтобы не удалили импорт при форматировании
__all__ = [Base]