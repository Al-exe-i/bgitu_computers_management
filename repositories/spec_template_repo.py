from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.spec_template import SpecTemplate


class SpecTemplateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, hardware_type: str | None = None) -> Sequence[SpecTemplate]:
        stmt = select(SpecTemplate)
        if hardware_type is not None:
            stmt = stmt.where(SpecTemplate.hardware_type == hardware_type)
        stmt = stmt.order_by(SpecTemplate.hardware_type, SpecTemplate.name)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get(self, template_id: int) -> SpecTemplate | None:
        result = await self.db.execute(
            select(SpecTemplate).where(SpecTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def create(self, template: SpecTemplate) -> SpecTemplate:
        self.db.add(template)
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def update(self, template: SpecTemplate) -> SpecTemplate:
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def delete(self, template: SpecTemplate) -> None:
        await self.db.delete(template)
        await self.db.flush()
