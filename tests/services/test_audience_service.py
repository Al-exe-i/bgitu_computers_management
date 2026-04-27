import asyncio
from types import SimpleNamespace

import pytest

from core.exceptions import AudienceNotFoundError
from schemas.audience import AudienceUpdate
from services.audience_service import AudienceService


class FakeAudienceRepo:
    def __init__(self, audience=None) -> None:
        self.audience = audience

    async def get_by_id(self, audience_id: int):
        if self.audience and self.audience.id == audience_id:
            return self.audience
        return None


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
