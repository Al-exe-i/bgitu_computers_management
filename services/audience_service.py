from fastapi import HTTPException
from core.exceptions import HTTP404
from models import Hardware, Audience
from repositories.audience_repo import AudienceRepository
from schemas.audience import AudienceCreate


class AudienceService:
    def __init__(self, repo: AudienceRepository):
        self.repo = repo

    async def get_list(self):
        return await self.repo.get_all()

    async def get_one(self, audience_id: int):
        audience = await self.repo.get_by_id(audience_id)
        if not audience:
            raise HTTP404("Audience not found")
        return audience

    async def create_audience(self, schema: AudienceCreate):
        if await self.repo.get_by_id(schema.id):
            raise HTTPException(status_code=409, detail="Audience already exists")
        audience_data = schema.model_dump(exclude={'hardware'})

        hardware_orm_list = [
            Hardware(**hw.model_dump()) for hw in schema.hardware
        ]

        audience_orm = Audience(
            **audience_data,
            hardware=hardware_orm_list
        )

        return await self.repo.create(audience_orm)

    async def delete_audience(self, audience_id: int):
        await self.get_one(audience_id)
        await self.repo.delete(audience_id)



