from __future__ import annotations

import asyncio
import os
from asyncio import create_task, start_unix_server
from contextlib import asynccontextmanager
from queue import Queue
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import pytest
from anyio.from_thread import start_blocking_portal

from .emulator import EmulatedDevice

if TYPE_CHECKING:
    from asyncio import StreamReader, StreamWriter
    from collections.abc import AsyncIterator, Iterator


@pytest.fixture(scope='session')
def anyio_backend() -> str:
    return 'asyncio'


class FakeServer:
    """Fake server used to spawn fake LD2410 devices."""

    def __init__(self, socket_path: str, lifespan):
        """Create a fake unix socket server used to emulate a real device."""
        self.lifespan = lifespan
        self.should_exit = False
        self.socket_path = socket_path
        self._tasks = []

    async def handle_connection(self, reader: StreamReader, writer: StreamWriter) -> None:
        """Handle a new connection, which means a brand new device."""
        self._tasks.append(asyncio.current_task())
        async with EmulatedDevice(reader, writer) as device:
            await device.wait_for_closing()

    async def wait_for_shutdown(self) -> None:
        """Wait for the shutdown signal."""
        # An asyncio event does not work well here
        # This may be because multiple loops are being used.
        while not self.should_exit:  # noqa: ASYNC110
            await asyncio.sleep(0.1)

    async def serve(self) -> None:
        """Serve requests until we are told to exit."""
        server = await start_unix_server(self.handle_connection, self.socket_path)
        async with server, self.lifespan():
            task_wait = create_task(self.wait_for_shutdown())
            task_serve = create_task(server.serve_forever())
            done, pending = await asyncio.wait(
                (task_wait, task_serve),
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            for task in self._tasks:
                task.cancel()


@pytest.fixture(scope='class')
def fake_device_socket() -> Iterator[str]:
    """Run a real server in a separate thread."""

    # Inspired by https://github.com/frankie567/httpx-ws/blob/main/tests/conftest.py.
    q_startup: Queue[bool] = Queue()
    q_shutdown: Queue[bool] = Queue()

    @asynccontextmanager
    async def lifespan() -> AsyncIterator[None]:
        q_startup.put(True)
        yield
        q_shutdown.put(True)

    with start_blocking_portal(backend='asyncio') as portal, TemporaryDirectory() as tmp:
        server = FakeServer(os.path.join(tmp, 'server.sock'), lifespan)
        portal.start_task_soon(server.serve)
        try:
            q_startup.get(True)
            yield server.socket_path
        finally:
            server.should_exit = True
            q_shutdown.get(True)
