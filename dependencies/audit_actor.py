from typing import Annotated

from fastapi import Depends

from dependencies.audit_log import audit_log_service_dep
from dependencies.auth import admin_dep, superuser_dep, user_dep
from dependencies.request_meta import request_meta_dep
from modules.administration.adapters.audit_actor import AuditActor


def get_audit_ctx(
    service: audit_log_service_dep,
    meta: request_meta_dep,
) -> AuditActor:
    return AuditActor(service=service, meta=meta)


def get_user_audit_actor(
    service: audit_log_service_dep,
    meta: request_meta_dep,
    user: user_dep,
) -> AuditActor:
    return AuditActor(service=service, meta=meta, user=user)


def get_admin_audit_actor(
    service: audit_log_service_dep,
    meta: request_meta_dep,
    user: admin_dep,
) -> AuditActor:
    return AuditActor(service=service, meta=meta, user=user)


def get_superuser_audit_actor(
    service: audit_log_service_dep,
    meta: request_meta_dep,
    user: superuser_dep,
) -> AuditActor:
    return AuditActor(service=service, meta=meta, user=user)


audit_ctx_dep = Annotated[AuditActor, Depends(get_audit_ctx)]
user_audit_actor_dep = Annotated[AuditActor, Depends(get_user_audit_actor)]
admin_audit_actor_dep = Annotated[AuditActor, Depends(get_admin_audit_actor)]
superuser_audit_actor_dep = Annotated[AuditActor, Depends(get_superuser_audit_actor)]
