import asyncio

import pytest

from core.exceptions import ProtectedFileAccessDeniedError
from modules.administration.application import AdministrationProtectedFileQueries


class FakeStorage:
    def __init__(self) -> None:
        self.exists_calls: list[str] = []

    def exists(self, key: str) -> bool:
        self.exists_calls.append(key)
        return True

    def iter_range(self, key: str):
        yield b"content"


def test_protected_file_query_rejects_path_traversal_before_storage_access() -> None:
    async def scenario() -> None:
        storage = FakeStorage()
        queries = AdministrationProtectedFileQueries(storage)

        with pytest.raises(ProtectedFileAccessDeniedError):
            await queries.get_file(file_path="reports/../../secret.txt")

        assert storage.exists_calls == []

    asyncio.run(scenario())
