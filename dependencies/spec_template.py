from typing import Annotated

from fastapi import Depends

from db.session import session_dep
from modules.inventory.repositories.spec_templates import SpecTemplateRepository
from modules.inventory.services.spec_templates import SpecTemplateService


def get_spec_template_service(db: session_dep) -> SpecTemplateService:
    return SpecTemplateService(SpecTemplateRepository(db))


spec_template_service_dep = Annotated[
    SpecTemplateService, Depends(get_spec_template_service)
]
