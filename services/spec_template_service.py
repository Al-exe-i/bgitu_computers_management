from collections.abc import Sequence

from models.hardware import HardwareType
from models.spec_template import SpecTemplate
from repositories.spec_template_repo import SpecTemplateRepository
from schemas.spec_template import SpecTemplateCreate, SpecTemplateUpdate
from utils.hw_specs import validate_specs


class SpecTemplateService:
    def __init__(self, repo: SpecTemplateRepository):
        self.repo = repo

    async def list(
        self, hardware_type: HardwareType | None = None
    ) -> Sequence[SpecTemplate]:
        return await self.repo.list(
            hardware_type.value if hardware_type is not None else None
        )

    async def get(self, template_id: int) -> SpecTemplate | None:
        return await self.repo.get(template_id)

    async def create(self, data: SpecTemplateCreate) -> SpecTemplate:
        specs = validate_specs(data.hardware_type, data.specs)
        template = SpecTemplate(
            name=data.name.strip(),
            hardware_type=data.hardware_type.value,
            specs=specs,
        )
        return await self.repo.create(template)

    async def update(
        self, template_id: int, data: SpecTemplateUpdate
    ) -> SpecTemplate | None:
        template = await self.repo.get(template_id)
        if not template:
            return None

        if data.name is not None:
            template.name = data.name.strip()
        if data.specs is not None:
            template.specs = validate_specs(
                HardwareType(template.hardware_type), data.specs
            )

        return await self.repo.update(template)

    async def delete(self, template_id: int) -> bool:
        template = await self.repo.get(template_id)
        if not template:
            return False
        await self.repo.delete(template)
        return True
