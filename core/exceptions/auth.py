class AuthServiceError(Exception):
    detail = "Authentication failed"


class InvalidCredentialsError(AuthServiceError):
    detail = "Invalid credentials"


class RefreshTokenMissingError(AuthServiceError):
    detail = "No refresh token provided"


class RefreshSessionNotFoundError(AuthServiceError):
    detail = "Couldn't validate refresh token"


class RefreshUserNotFoundError(AuthServiceError):
    detail = "User not found"

    def __init__(self, *, user_id: int, sid: str) -> None:
        self.user_id = user_id
        self.sid = sid


class RefreshTokenReuseDetectedError(AuthServiceError):
    detail = "Refresh token revoked"

    def __init__(self, *, user_id: int, sid: str) -> None:
        self.user_id = user_id
        self.sid = sid


class SessionNotFoundError(AuthServiceError):
    detail = "Session not found"
