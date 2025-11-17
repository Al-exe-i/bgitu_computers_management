from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models.audience import Audience, Row, Computer
from schemas.audience import AudienceCreateRequest, AudienceUpdate


class AudienceRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> Sequence[Audience]:
        stmt = (
            select(Audience).
            options
                (
                selectinload(Audience.rows).selectinload(Row.computers),
                selectinload(Audience.additional_hardware)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, aud_id: int) -> Audience | None:
        stmt = (
            select(Audience)
            .where(Audience.id == aud_id)
            .options(
                selectinload(Audience.rows).selectinload(Row.computers),
                selectinload(Audience.additional_hardware)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, audience_data: AudienceCreateRequest) -> Audience | None:
        db_audience = Audience(
            id=audience_data.id,
            type=audience_data.type,
            office_id=audience_data.office_id,
        )
        self.db.add(db_audience)
        await self.db.flush()

        # Создаем ряды и компьютеры
        for row_data in audience_data.rows:
            db_row = Row(
                name=row_data.name,
                audience_id=db_audience.id
            )
            self.db.add(db_row)
            await self.db.flush()

            # Создаем компьютеры для ряда
            computers = [
                Computer(
                    name=f"PC{row_data.name.replace('row_', '')}_{i:02d}",
                    row_id=db_row.id,
                    state=False if i in row_data.broken_ids else True,
                )
                for i in range(1, row_data.computers_count + 1)
            ]
            self.db.add_all(computers)

        await self.db.commit()
        await self.db.refresh(db_audience)
        return await self.get_by_id(db_audience.id)

    async def update(self, audience: Audience, update_schema: AudienceUpdate) -> Audience | None:
        update_data = update_schema.model_dump(exclude_unset=True)
        for (key, value) in update_data.items():
            setattr(audience, key, value)

        await self.db.commit()
        await self.db.refresh(audience)

        return audience

    async def delete(self, audience: Audience) -> None:
        await self.db.delete(audience)
        await self.db.commit()
