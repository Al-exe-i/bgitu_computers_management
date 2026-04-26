from typing import Annotated

from fastapi import Depends

from dependencies.auth_service import auth_service_dep
from dependencies.invite import invite_service_dep
from dependencies.user import user_service_dep
from modules.identity.application import (
    IdentityAuthUseCases,
    IdentityInviteUseCases,
    IdentityUserUseCases,
)


def get_identity_auth_use_cases(
    auth_service: auth_service_dep,
    invite_service: invite_service_dep,
    user_service: user_service_dep,
) -> IdentityAuthUseCases:
    return IdentityAuthUseCases(
        auth_service=auth_service,
        invite_service=invite_service,
        user_service=user_service,
    )


identity_auth_use_cases_dep = Annotated[
    IdentityAuthUseCases,
    Depends(get_identity_auth_use_cases),
]


def get_identity_user_use_cases(
    user_service: user_service_dep,
) -> IdentityUserUseCases:
    return IdentityUserUseCases(user_service=user_service)


identity_user_use_cases_dep = Annotated[
    IdentityUserUseCases,
    Depends(get_identity_user_use_cases),
]


def get_identity_invite_use_cases(
    invite_service: invite_service_dep,
) -> IdentityInviteUseCases:
    return IdentityInviteUseCases(invite_service=invite_service)


identity_invite_use_cases_dep = Annotated[
    IdentityInviteUseCases,
    Depends(get_identity_invite_use_cases),
]
