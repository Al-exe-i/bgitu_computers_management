from typing import Annotated

from sqlalchemy import VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

str_64 = Annotated[Mapped[str], mapped_column(VARCHAR(64), nullable=True)]