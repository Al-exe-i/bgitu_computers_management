# repositories/audit_log_repo.py
from typing import Any, Sequence
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.audit_log import AuditLog

class AuditLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, entry: AuditLog) -> AuditLog:
        self.db.add(entry)
        await self.db.flush()  # чтобы получить id, но не коммитить
        return entry

    async def list(
        self,
        *,
        q: str | None = None,
        user_id: int | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[Any], Any]:
        stmt = select(AuditLog)
        count_stmt = select(func.count(AuditLog.id))

        filters = []
        if user_id is not None:
            filters.append(AuditLog.user_id == user_id)
        if action:
            filters.append(AuditLog.action == action)
        if entity_type:
            filters.append(AuditLog.entity_type == entity_type)
        if entity_id is not None:
            filters.append(AuditLog.entity_id == entity_id)

        if q:
            q_like = f"%{q.lower()}%"
            filters.append(or_(
                func.lower(AuditLog.action).like(q_like),
                func.lower(AuditLog.entity_type).like(q_like),
                func.lower(func.coalesce(AuditLog.path, "")).like(q_like),
            ))

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)

        items = (await self.db.execute(stmt)).scalars().all()
        total = (await self.db.execute(count_stmt)).scalar_one()

        return items, total
