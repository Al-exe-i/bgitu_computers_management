import asyncio
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from core.exceptions import OfficeAlreadyExistsError
from schemas.office import OfficeCreate
from services.office_service import OfficeService


class FakeOfficeRepo:
    def __init__(self, *, create_error: Exception | None = None) -> None:
        self.create_error = create_error
        self.created: list[object] = []

    async def create(self, office):
        if self.create_error is not None:
            raise self.create_error
        self.created.append(office)
        return SimpleNamespace(id=office.id, address=office.address)


def test_create_duplicate_office_raises_domain_error() -> None:
    async def scenario() -> None:
        service = OfficeService(
            FakeOfficeRepo(
                create_error=IntegrityError("insert offices", {}, Exception("duplicate")),
            )
        )

        with pytest.raises(OfficeAlreadyExistsError):
            await service.create(OfficeCreate(id=1, address="Main building"))

    asyncio.run(scenario())
