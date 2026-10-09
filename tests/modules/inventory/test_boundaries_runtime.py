import asyncio
from datetime import UTC, datetime
from functools import partial
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

import db.base  # noqa: F401 -- load the complete ORM registry
from db.post_commit import (
    add_post_commit_hook,
    clear_post_commit_hooks,
    run_post_commit_hooks,
)
from modules.inventory.adapters.directories import (
    AudienceDirectoryReader,
    OfficeDirectoryReader,
)
from modules.inventory.models.audience import Audience
from modules.inventory.models.hardware import Hardware
from modules.inventory.models.hardware_file import HardwareFile
from modules.inventory.models.office import Office
from modules.inventory.models.spec_template import SpecTemplate
from modules.inventory.public import AudienceContext, OfficeContext
from modules.inventory.schemas.audience import (
    AudienceResponse,
    AudienceShortResponse,
    AudienceUpdate,
)
from modules.inventory.schemas.hardware import HardwareFullResponse, HardwareUpdate
from modules.inventory.schemas.office import OfficeResponse, OfficeShort, OfficeUpdate
from modules.inventory.schemas.spec_template import SpecTemplateResponse
from modules.inventory.services.audiences import AudienceService
from modules.inventory.services.hardware import HardwareService
from modules.inventory.services.offices import OfficeService
from modules.inventory.services.spec_templates import SpecTemplateService
from modules.inventory.types import HardwareType


@pytest.fixture
def graph():
    file = HardwareFile(
        id=3, hardware_id=2, file_path="uploads/test.png", file_type="image/png"
    )
    hardware = Hardware(
        id=2,
        audience_id=1,
        type=HardwareType.computer,
        x=0,
        y=0,
        width=1,
        height=1,
        state=True,
        specs={},
        files=[file],
        title="Computer",
    )
    audience = Audience(
        id=1,
        public_id=uuid4(),
        number=101,
        floor=1,
        office_id=4,
        width=5,
        height=5,
        landmarks={},
        hardware=[hardware],
        room_type="educational",
    )
    office = Office(id=4, address="Main", audiences=[audience])
    return SimpleNamespace(
        file=file, hardware=hardware, audience=audience, office=office
    )


def test_services_return_detached_nested_dtos(graph):
    async def scenario():
        audience_repo = SimpleNamespace(
            get_by_id=AsyncMock(return_value=graph.audience),
            get_by_public_id=AsyncMock(return_value=graph.audience),
            get_all=AsyncMock(return_value=[graph.audience]),
            flush=AsyncMock(),
            create=AsyncMock(return_value=graph.audience),
        )
        audiences = AudienceService(audience_repo, SimpleNamespace())
        dto = await audiences.get_one(1)
        assert type(dto) is AudienceResponse
        assert type(dto.hardware[0]) is HardwareFullResponse
        assert dto.hardware[0].files[0].url == "/hardware/files/3"
        assert (await audiences.get_one_by_public_id(graph.audience.public_id)) == dto
        assert (await audiences.get_list()) == [dto]
        updated = await audiences.update_audience(
            1, AudienceUpdate(description="Changed")
        )
        assert type(updated) is AudienceShortResponse
        assert updated.description == "Changed"

        hardware = await HardwareService(
            SimpleNamespace(get_by_id=AsyncMock(return_value=graph.hardware))
        ).get(2)
        assert type(hardware) is HardwareFullResponse
        offices = OfficeService(
            SimpleNamespace(
                get_one=AsyncMock(return_value=graph.office),
                get_list=AsyncMock(return_value=[graph.office]),
                get_one_short=AsyncMock(return_value=graph.office),
                update=AsyncMock(return_value=graph.office),
            )
        )
        assert type(await offices.get(4)) is OfficeResponse
        assert type((await offices.get_all())[0]) is OfficeResponse
        assert (
            type(await offices.update(4, OfficeUpdate(address="Changed")))
            is OfficeShort
        )
        graph.hardware.title = "Later ORM mutation"
        assert dto.hardware[0].title == hardware.title == "Computer"
        assert not hasattr(dto, "_sa_instance_state")

    asyncio.run(scenario())


def test_template_service_converts_persisted_type_to_public_enum():
    async def scenario():
        row = SpecTemplate(
            id=1,
            name="Lab",
            hardware_type="computer",
            specs={},
            created_at=datetime.now(UTC),
        )
        service = SpecTemplateService(
            SimpleNamespace(
                get=AsyncMock(return_value=row), list=AsyncMock(return_value=[row])
            )
        )
        dto = await service.get(1)
        assert type(dto) is SpecTemplateResponse
        assert dto.hardware_type is HardwareType.computer
        assert (await service.list())[0] == dto

    asyncio.run(scenario())


@pytest.mark.parametrize("found", [True, False])
def test_public_directories_return_only_context(graph, found):
    async def scenario():
        audience = await AudienceDirectoryReader(
            SimpleNamespace(
                get_one_short=AsyncMock(return_value=graph.audience if found else None),
            )
        ).get_one_short(1)
        office = await OfficeDirectoryReader(
            SimpleNamespace(
                get_one_short=AsyncMock(return_value=graph.office if found else None),
            )
        ).get_one_short(4)
        if not found:
            assert audience is office is None
            return
        assert type(audience) is AudienceContext
        assert type(office) is OfficeContext
        assert audience.public_id == graph.audience.public_id
        assert not hasattr(audience, "hardware")
        assert not hasattr(office, "audiences")

    asyncio.run(scenario())


@pytest.mark.parametrize("service_name", ["audiences", "hardware", "offices"])
@pytest.mark.parametrize("commit", [True, False])
def test_mutations_invalidate_only_after_commit_without_repo_session_introspection(
    graph, service_name, commit
):
    async def scenario():
        session = SimpleNamespace(info={})
        cache = SimpleNamespace(invalidate=AsyncMock())
        options = {
            "office_short_cache": cache,
            "on_commit": partial(add_post_commit_hook, session),
        }
        if service_name == "audiences":
            repo = SimpleNamespace(
                get_by_id=AsyncMock(return_value=graph.audience), flush=AsyncMock()
            )
            await AudienceService(repo, SimpleNamespace(), **options).update_audience(
                1, AudienceUpdate(description="Changed")
            )
        elif service_name == "hardware":
            repo = SimpleNamespace(
                get_by_id=AsyncMock(return_value=graph.hardware),
                update=AsyncMock(return_value=graph.hardware),
            )
            await HardwareService(repo, **options).update(
                2, HardwareUpdate(title="Changed")
            )
        else:
            repo = SimpleNamespace(
                get_one_short=AsyncMock(return_value=graph.office),
                update=AsyncMock(return_value=graph.office),
            )
            await OfficeService(repo, **options).update(
                4, OfficeUpdate(address="Changed")
            )
        cache.invalidate.assert_not_awaited()
        if not commit:
            clear_post_commit_hooks(session)
        await run_post_commit_hooks(session)
        assert cache.invalidate.await_count == int(commit)

    asyncio.run(scenario())


def test_rollback_does_not_populate_office_cache():
    async def scenario():
        session = SimpleNamespace(info={})
        cache = SimpleNamespace(get=AsyncMock(return_value=None), set=AsyncMock())
        repo = SimpleNamespace(
            get_list_short=AsyncMock(return_value=[{"id": 4, "address": "Uncommitted"}])
        )
        service = OfficeService(
            repo, cache, on_commit=partial(add_post_commit_hook, session)
        )
        await service.get_all_short()
        cache.set.assert_not_awaited()
        clear_post_commit_hooks(session)
        await run_post_commit_hooks(session)
        cache.set.assert_not_awaited()

    asyncio.run(scenario())
