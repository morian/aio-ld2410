from __future__ import annotations

import asyncio
import os
from asyncio import create_task, start_unix_server
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import pytest
from anyio.from_thread import start_blocking_portal

from .emulator import EmulatedDevice

if TYPE_CHECKING:
    from asyncio import StreamReader, StreamWriter
    from collections.abc import Iterator


@pytest.fixture(scope='session')
def anyio_backend() -> str:
    return 'asyncio'


class FakeServer:
    """Fake server used to spawn fake LD2410 devices."""

    def __init__(self, socket_path: str) -> None:
        """Create a fake unix socket server used to emulate a real device."""
        self.shutdown = asyncio.Event()
        self.socket_path = socket_path
        self.started = asyncio.Event()
        self.stopped = asyncio.Event()
        self._tasks = []

    async def handle_connection(self, reader: StreamReader, writer: StreamWriter) -> None:
        """Handle a new connection, which means a brand new device."""
        self._tasks.append(asyncio.current_task())
        async with EmulatedDevice(reader, writer) as device:
            await device.wait_for_closing()

    async def serve(self) -> None:
        """Serve requests until we are told to exit."""
        server = await start_unix_server(self.handle_connection, self.socket_path)
        try:
            async with server:
                self.started.set()
                task_wait = create_task(self.shutdown.wait())
                task_serve = create_task(server.serve_forever())
                done, pending = await asyncio.wait(
                    (task_wait, task_serve),
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
                for task in self._tasks:
                    task.cancel()
        finally:
            self.stopped.set()


@pytest.fixture(scope='class')
def fake_device_socket() -> Iterator[str]:
    """Run a real server in a separate thread."""

    with TemporaryDirectory() as tmp:
        tmp_socket = os.path.join(tmp, 'server.sock')
        with start_blocking_portal(backend='asyncio') as portal:
            server = FakeServer(tmp_socket)
            portal.start_task_soon(server.serve)
            try:
                portal.call(server.started.wait)
                yield server.socket_path
            finally:
                portal.call(server.shutdown.set)
                portal.call(server.stopped.wait)
