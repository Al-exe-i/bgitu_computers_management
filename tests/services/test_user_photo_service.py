import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from core.exceptions import UserAlreadyExistsError
from core.security import verify_password
from models.user import UserRole
from schemas.user import UserCreate, UserOut
from services.user_service import UserService


class FakeUserRepo:
    def __init__(self, user: SimpleNamespace | None, *, create_error: Exception | None = None) -> None:
        self.user = user
        self.create_error = create_error
        self.updates: list[dict] = []
        self.created_user = None

    async def get(self, user_id: int):
        if self.user is not None and self.user.id == user_id:
            return self.user
        return None

    async def update(self, user, data):
        changes = data.model_dump(exclude_unset=True)
        self.updates.append(changes)
        for key, value in changes.items():
            setattr(user, key, value)
        return user

    async def create(self, user):
        if self.create_error is not None:
            raise self.create_error
        user.id = 7
        user.reg_date = datetime(2026, 4, 21, tzinfo=timezone.utc)
        user.is_superuser = False
        user.telegram_id_confirmed = False
        self.created_user = user
        return user


class FakeAvatarStorage:
    def __init__(self, saved_filename: str = "new-avatar.jpg") -> None:
        self.saved_filename = saved_filename
        self.saved_files: list[object] = []
        self.deleted_filenames: list[str] = []

    async def save(self, file) -> str:
        self.saved_files.append(file)
        return self.saved_filename

    def delete(self, filename: str | None) -> bool:
        if filename:
            self.deleted_filenames.append(filename)
            return True
        return False


def make_user(*, photo: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=7,
        email="user@example.com",
        name="Alex",
        surname="Ivanov",
        telegram_id=None,
        telegram_id_confirmed=False,
        photo=photo,
        role=UserRole.teacher,
        reg_date=datetime(2026, 4, 21, tzinfo=timezone.utc),
        is_superuser=False,
    )


def test_upload_photo_saves_new_avatar_and_deletes_previous_one() -> None:
    async def scenario() -> None:
        repo = FakeUserRepo(make_user(photo="old-avatar.jpg"))
        storage = FakeAvatarStorage(saved_filename="new-avatar.jpg")
        service = UserService(repo, storage)
        upload = SimpleNamespace(filename="avatar.jpg", content_type="image/jpeg")

        result = await service.upload_photo(7, upload)

        assert result is not None
        assert result.had_photo is True
        assert result.user.photo == "new-avatar.jpg"
        assert repo.updates == [{"photo": "new-avatar.jpg"}]
        assert storage.saved_files == [upload]
        assert storage.deleted_filenames == ["old-avatar.jpg"]

    asyncio.run(scenario())


def test_delete_photo_removes_avatar_and_clears_user_photo() -> None:
    async def scenario() -> None:
        repo = FakeUserRepo(make_user(photo="avatar.jpg"))
        storage = FakeAvatarStorage()
        service = UserService(repo, storage)

        result = await service.delete_photo(7)

        assert result is not None
        assert result.had_photo is True
        assert result.user.photo is None
        assert repo.updates == [{"photo": None}]
        assert storage.deleted_filenames == ["avatar.jpg"]

    asyncio.run(scenario())


def test_create_hashes_password_and_returns_user_out() -> None:
    async def scenario() -> None:
        repo = FakeUserRepo(None)
        service = UserService(repo)

        result = await service.create(
            UserCreate(
                email="user@example.com",
                password="secret1",
                role=UserRole.teacher,
            )
        )

        assert isinstance(result, UserOut)
        assert not hasattr(result, "password")
        assert repo.created_user is not None
        assert repo.created_user.password != "secret1"
        assert verify_password("secret1", repo.created_user.password)

    asyncio.run(scenario())


def test_create_translates_duplicate_user_to_domain_error() -> None:
    async def scenario() -> None:
        repo = FakeUserRepo(
            None,
            create_error=IntegrityError("insert users", {}, Exception("duplicate")),
        )
        service = UserService(repo)

        with pytest.raises(UserAlreadyExistsError):
            await service.create(
                UserCreate(
                    email="user@example.com",
                    password="secret1",
                    role=UserRole.teacher,
                )
            )

    asyncio.run(scenario())
