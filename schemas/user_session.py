from datetime import datetime
from pydantic import BaseModel, ConfigDict

class UserSessionOut(BaseModel):
    sid: str
    created_at: datetime
    last_used_at: datetime | None = None
    expires_at: datetime
    revoked_at: datetime | None = None
    ip: str | None = None
    user_agent: str | None = None

    is_active: bool
    is_current: bool