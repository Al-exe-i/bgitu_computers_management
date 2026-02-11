from typing import Annotated
from fastapi import Depends

from db.session import session_dep
from repositories.audit_log_repo import AuditLogRepository
from services.audit_log_service import AuditLogService

def get_audit_log_service(db: session_dep):
    repo = AuditLogRepository(db)
    return AuditLogService(repo)

audit_log_service_dep = Annotated[AuditLogService, Depends(get_audit_log_service)]