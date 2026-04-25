import asyncio

import pytest
from sqlalchemy.dialects import postgresql

from repositories.office_repo import OfficeRepository


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class FakeSession:
    def __init__(self, rows):
        self.rows = rows
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return FakeResult(self.rows)


@pytest.fixture
def fake_session() -> FakeSession:
    return FakeSession(
        rows=[
            (1, "Корпус 1", 2, 1),
            (2, "Корпус 2", 0, 0),
        ]
    )


def test_get_list_short_maps_audience_and_faulty_counts(fake_session: FakeSession) -> None:
    result = asyncio.run(OfficeRepository(fake_session).get_list_short())

    assert result == [
        {
            "id": 1,
            "address": "Корпус 1",
            "audiences_count": 2,
            "faulty_hw_count": 1,
        },
        {
            "id": 2,
            "address": "Корпус 2",
            "audiences_count": 0,
            "faulty_hw_count": 0,
        },
    ]


def test_get_list_short_keeps_empty_offices_and_counts_faults_with_filter(
    fake_session: FakeSession,
) -> None:
    asyncio.run(OfficeRepository(fake_session).get_list_short())

    sql = " ".join(
        str(
            fake_session.statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        ).split()
    )

    assert "LEFT OUTER JOIN audiences" in sql
    assert "LEFT OUTER JOIN hardwares" in sql
    assert "count(distinct(audiences.id)) AS audiences_count" in sql
    assert "FILTER (WHERE hardwares.state IS false) AS faulty_hw_count" in sql

    join_section = sql.split(" FROM ", maxsplit=1)[1].split(" GROUP BY ", maxsplit=1)[0]
    assert " WHERE " not in join_section
