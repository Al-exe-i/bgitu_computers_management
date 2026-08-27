from core.exceptions import SpecTemplateNotFoundError
from models.hardware import HardwareType
from modules.inventory.ports import AuditLogger, SpecTemplateServicePort
from schemas.spec_template import (
    SpecTemplateCreate,
    SpecTemplateResponse,
    SpecTemplateUpdate,
)
from utils.audit import changed_fields


class InventorySpecTemplateUseCases:
    def __init__(self, service: SpecTemplateServicePort) -> None:
        self.service = service

    async def list_templates(
        self,
        *,
        hardware_type: HardwareType | None = None,
    ) -> list[SpecTemplateResponse]:
        templates = await self.service.list(hardware_type)
        return [
            SpecTemplateResponse.model_validate(template, from_attributes=True)
            for template in templates
        ]

    async def create_template(
        self,
        *,
        data: SpecTemplateCreate,
        audit: AuditLogger,
    ) -> SpecTemplateResponse:
        template = await self.service.create(data)
        result = SpecTemplateResponse.model_validate(template, from_attributes=True)

        await audit.log(
            action="spec_template.create",
            entity_type="spec_template",
            entity_id=result.id,
            payload={
                "name": result.name,
                "hardware_type": result.hardware_type.value,
            },
        )
        return result

    async def update_template(
        self,
        *,
        template_id: int,
        data: SpecTemplateUpdate,
        audit: AuditLogger,
    ) -> SpecTemplateResponse:
        template = await self.service.update(template_id, data)
        if template is None:
            raise SpecTemplateNotFoundError()

        result = SpecTemplateResponse.model_validate(template, from_attributes=True)
        await audit.log(
            action="spec_template.update",
            entity_type="spec_template",
            entity_id=template_id,
            payload={"changed_fields": changed_fields(data)},
        )
        return result

    async def delete_template(
        self,
        *,
        template_id: int,
        audit: AuditLogger,
    ) -> None:
        template = await self.service.get(template_id)
        if template is None or not await self.service.delete(template_id):
            raise SpecTemplateNotFoundError()

        await audit.log(
            action="spec_template.delete",
            entity_type="spec_template",
            entity_id=template_id,
            payload={
                "name": template.name,
                "hardware_type": str(template.hardware_type),
            },
        )
