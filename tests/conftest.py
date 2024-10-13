from __future__ import annotations

import os
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import pytest
from anyio.from_thread import start_blocking_portal

from .emulator import EmulatorServer

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(scope='session')
def anyio_backend() -> str:
    return 'asyncio'


@pytest.fixture(scope='session')
def emulation_server() -> Iterator[str]:
    """Run an emulation server in a separate thread."""

    with TemporaryDirectory() as tmp:
        tmp_socket = os.path.join(tmp, 'server.sock')

        with start_blocking_portal(backend='asyncio') as portal:
            server = EmulatorServer(tmp_socket)
            future, _ = portal.start_task(server.run)
            try:
                yield server.socket_path
            finally:
                future.cancel()
