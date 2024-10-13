from __future__ import annotations

from asyncio import start_unix_server
from typing import TYPE_CHECKING

from anyio import TASK_STATUS_IGNORED

from .device import EmulatedDevice

if TYPE_CHECKING:
    from asyncio import StreamReader, StreamWriter

    from anyio.abc import TaskStatus


class EmulatorServer:
    """Server used to emulate LD2410 devices on top of an unix socket."""

    def __init__(self, socket_path: str) -> None:
        """
        Create an emulation server for LD2410 devices on top of an unix socket.

        Args:
            socket_path: path to the unix socket

        """
        self._socket_path = socket_path

    @property
    def socket_path(self) -> str:
        """Get the server's unix socket path."""
        return self._socket_path

    async def _handle_connection(self, reader: StreamReader, writer: StreamWriter) -> None:
        """
        Handle a new connection for a new emulated device.

        This coroutine runs in a new :class:`asyncio.Task` as stated in the documentation
        from :meth:`start_unix_server`, which means that we don't have to handle anything
        else than the emulated device here.

        Args:
            reader: the read part of the connection stream
            writer: the write part of the connection stream

        """
        async with EmulatedDevice(reader, writer) as device:
            await device.wait_for_closing()

    async def run(self, *, task_status: TaskStatus[None] = TASK_STATUS_IGNORED) -> None:
        """
        Serve incoming connection requests forever.

        Connection server is closed when the underlying task is cancelled.

        Keyword Args:
            task_status: anyio specific used to tell when we are ready to serve

        """
        server = await start_unix_server(self._handle_connection, self._socket_path)
        async with server:
            task_status.started()
            await server.serve_forever()
