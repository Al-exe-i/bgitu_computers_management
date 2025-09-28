# models/base.py
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, declared_attr
import inflection

class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        name = inflection.underscore(cls.__name__)
        return inflection.pluralize(name)