from typing import Annotated

from fastapi import Depends

from db.session import session_dep
from db.transaction import SessionTransaction
from dependencies.auth_service import auth_service_dep
from dependencies.user import user_service_dep
from modules.identity.application import (
    IdentityAuthUseCases,
    IdentityUserUseCases,
)


def get_identity_auth_use_cases(
    db: session_dep,
    auth_service: auth_service_dep,
) -> IdentityAuthUseCases:
    return IdentityAuthUseCases(
        auth_service=auth_service,
        transaction=SessionTransaction(db),
    )


identity_auth_use_cases_dep = Annotated[
    IdentityAuthUseCases,
    Depends(get_identity_auth_use_cases),
]


def get_identity_user_use_cases(
    user_service: user_service_dep,
    auth_service: auth_service_dep,
) -> IdentityUserUseCases:
    return IdentityUserUseCases(
        user_service=user_service,
        auth_service=auth_service,
    )


identity_user_use_cases_dep = Annotated[
    IdentityUserUseCases,
    Depends(get_identity_user_use_cases),
]
