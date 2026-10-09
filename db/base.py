"""Complete ORM registry for application startup and Alembic."""

import models  # noqa: F401 -- register every mapped table on the shared metadata
from db.orm import Base

__all__ = ["Base"]
