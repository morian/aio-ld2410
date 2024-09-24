import asyncio
from asyncio import StreamReader, StreamWriter

import pytest

from aio_ld2410 import LD2410

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.anyio


class FakeLD2410(LD2410):
    """Fake LD2410 connector, using an unix socket instead."""

    async def _open_serial_connection(self) -> tuple[StreamReader, StreamWriter]:
        """Open a fake serial connection for this device."""
        # An unix socket cannot have None or 0 as a limit.
        bufsize = self._read_bufsize or 8192
        return await asyncio.open_unix_connection(path=self._device, limit=bufsize)


class TestLD2410:

    async def test_initialized(self, fake_device):
        device = FakeLD2410(fake_device)
        assert device.configuring is False
        assert device.connected is False
        assert device.entered is False

    async def test_entered(self, fake_device):
        async with FakeLD2410(fake_device) as device:
            assert device.configuring is False
            assert device.connected is True
            assert device.entered is True
