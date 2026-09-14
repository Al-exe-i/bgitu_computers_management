from typing import Annotated

from fastapi import Depends

from db.session import session_dep
from modules.administration.repositories.audit_log import AuditLogRepository
from modules.administration.services.audit_log import AuditLogService
from modules.identity.adapters.user_directory import UserSummaryReader
from modules.identity.repositories.users import UserRepository


def get_audit_log_service(db: session_dep):
    repo = AuditLogRepository(db)
    return AuditLogService(repo, UserSummaryReader(UserRepository(db)))

audit_log_service_dep = Annotated[AuditLogService, Depends(get_audit_log_service)]
