from models.base import Base
from sqlalchemy import Column, Integer, String, Boolean, VARCHAR, DateTime
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    surname = Column(String(64))
    email = Column(String(50), unique=True)
    telegram_id = Column(VARCHAR(16))
    telegram_id_confirmed = Column(Boolean, default=False)
    password = Column(String(500), nullable=False)
    reg_date = Column(DateTime, default=datetime.now)
    is_superuser = Column(Boolean, default=False)
    photo = Column(String(500))