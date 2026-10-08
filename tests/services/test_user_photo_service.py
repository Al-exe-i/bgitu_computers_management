import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from core.exceptions import UserAlreadyExistsError
from core.security import verify_password
from db.transaction import SessionTransaction
from modules.identity.adapters.avatar_storage import AvatarStorage
from modules.identity.public import UserRole
from modules.identity.schemas.user import UserCreate, UserOut
from modules.identity.services.users import UserService
from services.object_storage import LocalObjectStorage
from tests.transaction_helpers import make_transaction_session, transaction_callbacks


class FakeUserRepo:
    def __init__(
        self, user: SimpleNamespace | None, *, create_error: Exception | None = None
    ) -> None:
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

    async def update_photo(self, user, photo: str | None):
        self.updates.append({"photo": photo})
        user.photo = photo
        return user

    async def update_password(self, user, password: str):
        self.updates.append({"password": password})
        user.password = password
        return user

    async def create(self, user):
        if self.create_error is not None:
            raise self.create_error
        user.id = 7
        user.reg_date = datetime(2026, 4, 21, tzinfo=UTC)
        user.is_superuser = False
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
        photo=photo,
        role=UserRole.teacher,
        reg_date=datetime(2026, 4, 21, tzinfo=UTC),
        is_superuser=False,
        password="hashed-password",
    )


def test_upload_photo_saves_new_avatar_and_deletes_previous_one() -> None:
    async def scenario() -> None:
        repo = FakeUserRepo(make_user(photo="old-avatar.jpg"))
        storage = FakeAvatarStorage(saved_filename="new-avatar.jpg")
        session = make_transaction_session()
        service = UserService(repo, storage, **transaction_callbacks(session))
        upload = SimpleNamespace(filename="avatar.jpg", content_type="image/jpeg")

        result = await service.upload_photo(7, upload)

        assert result is not None
        assert result.had_photo is True
        assert result.user.photo == "new-avatar.jpg"
        assert repo.updates == [{"photo": "new-avatar.jpg"}]
        assert storage.saved_files == [upload]
        assert storage.deleted_filenames == []
        await SessionTransaction(session).commit()
        assert storage.deleted_filenames == ["old-avatar.jpg"]
        assert session.info == {}

    asyncio.run(scenario())


def test_delete_photo_removes_avatar_and_clears_user_photo() -> None:
    async def scenario() -> None:
        repo = FakeUserRepo(make_user(photo="avatar.jpg"))
        storage = FakeAvatarStorage()
        session = make_transaction_session()
        service = UserService(repo, storage, **transaction_callbacks(session))

        result = await service.delete_photo(7)

        assert result is not None
        assert result.had_photo is True
        assert result.user.photo is None
        assert repo.updates == [{"photo": None}]
        assert storage.deleted_filenames == []
        await SessionTransaction(session).commit()
        assert storage.deleted_filenames == ["avatar.jpg"]
        assert session.info == {}

    asyncio.run(scenario())


@pytest.mark.parametrize("operation", ["upload", "delete"])
@pytest.mark.parametrize(
    "failure", ["write", "audit", "flush", "commit", "cancel", "cancel_commit"]
)
def test_photo_failure_preserves_files_according_to_commit_boundary(operation, failure):
    async def scenario():
        repo = FakeUserRepo(make_user(photo="old-avatar.jpg"))
        storage = FakeAvatarStorage()
        session = make_transaction_session()
        transaction = SessionTransaction(session)
        service = UserService(repo, storage, **transaction_callbacks(session))
        error = (
            asyncio.CancelledError
            if failure in {"cancel", "cancel_commit"}
            else RuntimeError
        )
        if failure == "write":
            repo.update_photo = AsyncMock(side_effect=RuntimeError("write failed"))
        if failure in {"commit", "cancel_commit"}:
            session.commit.side_effect = error("commit failed")
        if failure == "flush":
            session.flush.side_effect = RuntimeError("flush failed")

        with pytest.raises(error):
            if failure in {"flush", "commit", "cancel_commit"}:
                if operation == "upload":
                    await service.upload_photo(7, object())
                else:
                    await service.delete_photo(7)
                await transaction.commit()
            else:
                try:
                    if operation == "upload":
                        await service.upload_photo(7, object())
                    else:
                        await service.delete_photo(7)
                    raise error("later request failure")
                except BaseException:
                    await transaction.rollback()
                    raise

        assert storage.deleted_filenames == (
            ["new-avatar.jpg"]
            if operation == "upload" and failure not in {"commit", "cancel_commit"}
            else []
        )
        assert session.info == {}
        session.rollback.assert_awaited_once()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "on_commit,on_rollback",
    [(None, None), (list().append, None), (None, list().append)],
)
def test_avatar_storage_requires_transaction_callbacks(on_commit, on_rollback):
    with pytest.raises(ValueError, match="commit and rollback schedulers"):
        UserService(
            FakeUserRepo(make_user()),
            FakeAvatarStorage(),
            on_commit=on_commit,
            on_rollback=on_rollback,
        )


@pytest.mark.parametrize("failure", [None, "flush", "commit", "cancel_commit"])
def test_avatar_transaction_preserves_real_files_on_disk(tmp_path, failure):
    def upload(content):
        return SimpleNamespace(
            filename="avatar.png",
            content_type="image/png",
            read=AsyncMock(side_effect=[content, b""]),
            close=AsyncMock(),
        )

    async def scenario():
        objects = LocalObjectStorage(tmp_path)
        storage = AvatarStorage(objects)
        old_photo = await storage.save(upload(b"old-avatar"))
        session = make_transaction_session()
        service = UserService(
            FakeUserRepo(make_user(photo=old_photo)),
            storage,
            **transaction_callbacks(session),
        )
        result = await service.upload_photo(7, upload(b"new-avatar"))
        old_key, new_key = f"avatars/{old_photo}", f"avatars/{result.user.photo}"
        assert objects.exists(old_key) and objects.exists(new_key)

        if failure:
            error = (
                asyncio.CancelledError if failure == "cancel_commit" else RuntimeError
            )
            getattr(
                session, "flush" if failure == "flush" else "commit"
            ).side_effect = error("transaction failed")
            with pytest.raises(error, match="transaction failed"):
                await SessionTransaction(session).commit()
        else:
            await SessionTransaction(session).commit()

        assert objects.exists(old_key) is (failure is not None)
        assert objects.exists(new_key) is (failure != "flush")
        assert len(list(tmp_path.rglob("*.png"))) == (
            2 if failure in {"commit", "cancel_commit"} else 1
        )

    asyncio.run(scenario())


def test_create_hashes_password_and_returns_user_out() -> None:
    async def scenario() -> None:
        repo = FakeUserRepo(None)
        service = UserService(repo)

        result = await service.create(
            UserCreate(
                email="user@example.ru",
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
                    email="user@example.ru",
                    password="secret1",
                    role=UserRole.teacher,
                )
            )

    asyncio.run(scenario())
