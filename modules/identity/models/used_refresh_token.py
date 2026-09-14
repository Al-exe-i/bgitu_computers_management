from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from db.orm import Base


class UsedRefreshToken(Base):
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("user_sessions.id", ondelete="CASCADE"), index=True
    )
