# models/base.py
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, declared_attr
import inflection

from core.config import settings


class Base(DeclarativeBase):

    metadata = MetaData(
        naming_convention=settings.db.naming_convention,
    )

    @declared_attr.directive
    def __tablename__(cls) -> str:
        name = inflection.underscore(cls.__name__)
        return inflection.pluralize(name)