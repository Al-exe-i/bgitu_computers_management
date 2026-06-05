import asyncio
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from core.exceptions import AudienceAlreadyExistsError, AudienceNotFoundError
from schemas.audience import AudienceCreate
from schemas.audience import AudienceUpdate
from services.audience_service import AudienceService


class FakeAudienceRepo:
    def __init__(
        self,
        audience=None,
        *,
        create_error: Exception | None = None,
        flush_error: Exception | None = None,
    ) -> None:
        self.audience = audience
        self.create_error = create_error
        self.flush_error = flush_error

    async def get_by_id(self, audience_id: int):
        if self.audience and self.audience.id == audience_id:
            return self.audience
        return None

    async def create(self, audience):
        if self.create_error is not None:
            raise self.create_error
        return audience

    async def flush(self) -> None:
        if self.flush_error is not None:
            raise self.flush_error


class FakeAudienceGrid:
    def validate(self, items, width: int, height: int) -> None:
        pass

    def build_hardware_models(self, items):
        return []

    async def sync(self, audience_id: int, incoming) -> None:
        pass


def test_get_one_missing_audience_raises_application_error() -> None:
    async def scenario() -> None:
        service = AudienceService(FakeAudienceRepo(), FakeAudienceGrid())

        with pytest.raises(AudienceNotFoundError):
            await service.get_one(12)

    asyncio.run(scenario())


def test_update_missing_audience_raises_application_error() -> None:
    async def scenario() -> None:
        service = AudienceService(FakeAudienceRepo(SimpleNamespace(id=13)), FakeAudienceGrid())

        with pytest.raises(AudienceNotFoundError):
            await service.update_audience(12, AudienceUpdate(description="212"))

    asyncio.run(scenario())


def test_create_duplicate_audience_raises_domain_error() -> None:
    async def scenario() -> None:
        service = AudienceService(
            FakeAudienceRepo(create_error=IntegrityError("insert audiences", {}, Exception("duplicate"))),
            FakeAudienceGrid(),
        )

        with pytest.raises(AudienceAlreadyExistsError):
            await service.create_audience(
                AudienceCreate(
                    number=212,
                    floor=2,
                    description="212",
                    office_id=1,
                    width=10,
                    height=10,
                    hardware=[],
                )
            )

    asyncio.run(scenario())


def test_update_duplicate_audience_number_raises_domain_error() -> None:
    async def scenario() -> None:
        service = AudienceService(
            FakeAudienceRepo(
                SimpleNamespace(id=12, width=10, height=10),
                flush_error=IntegrityError("update audiences", {}, Exception("duplicate")),
            ),
            FakeAudienceGrid(),
        )

        with pytest.raises(AudienceAlreadyExistsError):
            await service.update_audience(12, AudienceUpdate(number=212))

    asyncio.run(scenario())
