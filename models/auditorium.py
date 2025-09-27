from sqlalchemy import Column, Integer, JSON, Enum
from models.base import Base
import enum

class AuditoriumTypes(enum.Enum):
    row = 0
    perimeter = 1


class Auditorium(Base):
    __tablename__ = 'auditoriums'

    id = Column(Integer, primary_key=True, nullable=False)
    rows = Column(JSON)
    additional_hardware = Column(JSON)
    type = Column(Enum(AuditoriumTypes), default=AuditoriumTypes.row)