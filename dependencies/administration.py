from typing import Annotated

from fastapi import Depends

from dependencies.audit_log import audit_log_service_dep
from dependencies.storage import object_storage_dep
from modules.administration.application import (
    AdministrationAuditLogQueries,
    AdministrationProtectedFileQueries,
)


def get_administration_protected_file_queries(
    storage: object_storage_dep,
) -> AdministrationProtectedFileQueries:
    return AdministrationProtectedFileQueries(storage)


administration_protected_file_queries_dep = Annotated[
    AdministrationProtectedFileQueries,
    Depends(get_administration_protected_file_queries),
]


def get_administration_audit_log_queries(
    service: audit_log_service_dep,
) -> AdministrationAuditLogQueries:
    return AdministrationAuditLogQueries(service)


administration_audit_log_queries_dep = Annotated[
    AdministrationAuditLogQueries,
    Depends(get_administration_audit_log_queries),
]
