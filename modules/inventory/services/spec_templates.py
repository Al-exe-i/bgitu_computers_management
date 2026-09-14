from collections.abc import Sequence

from modules.inventory.models.spec_template import SpecTemplate
from modules.inventory.repositories.spec_templates import SpecTemplateRepository
from modules.inventory.schemas.spec_template import (
    SpecTemplateCreate,
    SpecTemplateResponse,
    SpecTemplateUpdate,
)
from modules.inventory.services.hw_specs import validate_specs
from modules.inventory.types import HardwareType


class SpecTemplateService:
    def __init__(self, repo: SpecTemplateRepository):
        self.repo = repo

    async def list(
        self, hardware_type: HardwareType | None = None
    ) -> Sequence[SpecTemplateResponse]:
        rows = await self.repo.list(
            hardware_type.value if hardware_type is not None else None
        )
        return [SpecTemplateResponse.model_validate(row) for row in rows]

    async def get(self, template_id: int) -> SpecTemplateResponse | None:
        row = await self.repo.get(template_id)
        return SpecTemplateResponse.model_validate(row) if row else None

    async def create(self, data: SpecTemplateCreate) -> SpecTemplateResponse:
        specs = validate_specs(data.hardware_type, data.specs)
        template = SpecTemplate(
            name=data.name.strip(),
            hardware_type=data.hardware_type.value,
            specs=specs,
        )
        return SpecTemplateResponse.model_validate(await self.repo.create(template))

    async def update(
        self, template_id: int, data: SpecTemplateUpdate
    ) -> SpecTemplateResponse | None:
        template = await self.repo.get(template_id)
        if not template:
            return None

        if data.name is not None:
            template.name = data.name.strip()
        if data.specs is not None:
            template.specs = validate_specs(
                HardwareType(template.hardware_type), data.specs
            )

        return SpecTemplateResponse.model_validate(await self.repo.update(template))

    async def delete(self, template_id: int) -> bool:
        template = await self.repo.get(template_id)
        if not template:
            return False
        await self.repo.delete(template)
        return True
