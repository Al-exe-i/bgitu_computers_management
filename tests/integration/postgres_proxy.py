import asyncio


class LostCommitReplyProxy:
    """Forward PostgreSQL traffic but drop a successful COMMIT reply."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.commit_completed = asyncio.Event()
        self.handlers = set()
        self.writers = set()

    async def __aenter__(self):
        self.server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        self.listen_port = self.server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, *args):
        self.server.close()
        await self.server.wait_closed()
        for writer in list(self.writers):
            writer.close()
        for handler in list(self.handlers):
            handler.cancel()
        await asyncio.gather(*list(self.handlers), return_exceptions=True)

    async def _handle(self, reader, writer):
        handler = asyncio.current_task()
        self.handlers.add(handler)
        self.writers.add(writer)
        backend_writer = None
        relays = []
        try:
            backend_reader, backend_writer = await asyncio.open_connection(
                self.host, self.port
            )
            self.writers.add(backend_writer)
            relays = [
                asyncio.create_task(self._forward_client(reader, backend_writer)),
                asyncio.create_task(self._forward_server(backend_reader, writer)),
            ]
            await asyncio.gather(*relays)
        except (OSError, asyncio.IncompleteReadError):
            pass
        finally:
            for relay in relays:
                relay.cancel()
            await asyncio.gather(*relays, return_exceptions=True)
            for connection in (writer, backend_writer):
                if connection is not None:
                    connection.close()
                    try:
                        await connection.wait_closed()
                    except OSError:
                        pass
                    self.writers.discard(connection)
            self.handlers.discard(handler)

    @staticmethod
    async def _forward_client(reader, writer):
        try:
            while chunk := await reader.read(64 * 1024):
                writer.write(chunk)
                await writer.drain()
        finally:
            writer.close()

    async def _forward_server(self, reader, writer):
        try:
            while True:
                header = await reader.readexactly(5)
                body = await reader.readexactly(int.from_bytes(header[1:], "big") - 4)
                # CommandComplete proves that PostgreSQL already committed.
                if header[:1] == b"C" and body == b"COMMIT\x00":
                    self.commit_completed.set()
                    return
                writer.write(header + body)
                await writer.drain()
        finally:
            writer.close()
