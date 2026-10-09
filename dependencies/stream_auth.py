from typing import Annotated

from fastapi import Depends

from core.exceptions import HTTP401
from core.security import verify_access_token
from dependencies.auth import get_access_token, user_dep
from modules.identity.adapters.stream_auth import StreamAuthorization


def get_stream_authorization(
    user: user_dep,
    token: Annotated[str, Depends(get_access_token)],
) -> StreamAuthorization:
    payload = verify_access_token(token)
    if payload is None:
        raise HTTP401("Couldn't validate credentials")
    return StreamAuthorization(
        user_id=user.id,
        token_version=int(payload["token_version"]),
        expires_at=float(payload["exp"]),
    )


stream_authorization_dep = Annotated[
    StreamAuthorization, Depends(get_stream_authorization)
]
