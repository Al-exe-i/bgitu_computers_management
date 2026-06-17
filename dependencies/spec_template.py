from typing import Annotated

from fastapi import Depends

from db.session import session_dep
from repositories.spec_template_repo import SpecTemplateRepository
from services.spec_template_service import SpecTemplateService


def get_spec_template_service(db: session_dep) -> SpecTemplateService:
    return SpecTemplateService(SpecTemplateRepository(db))


spec_template_service_dep = Annotated[
    SpecTemplateService, Depends(get_spec_template_service)
]
