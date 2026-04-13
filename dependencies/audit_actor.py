from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends

from dependencies.audit_log import audit_log_service_dep
from dependencies.auth import admin_dep, superuser_dep, user_dep
from dependencies.request_meta import request_meta_dep
from models.user import User
from services.audit_log_service import AuditLogService
from utils.request_meta import RequestMeta


@dataclass(slots=True)
class AuditActor:
    service: AuditLogService
    meta: RequestMeta
    user: User | None = None

    async def log(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        payload: dict | None = None,
        user_id: int | None = None,
    ):
        actor_id = self.user.id if user_id is None and self.user is not None else user_id
        return await self.service.log(
            user_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            **self.meta,
        )


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
