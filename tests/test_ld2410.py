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


@pytest.fixture
def raw_device(fake_device_socket):
    return FakeLD2410(fake_device_socket)


@pytest.fixture
async def device(raw_device):
    async with raw_device:
        yield raw_device


class TestLD2410:
    """Test the LD2410 class against the emulator."""

    async def test_initialized(self, raw_device):
        """Check properties of a device that was not entered."""
        assert raw_device.configuring is False
        assert raw_device.connected is False
        assert raw_device.entered is False

    async def test_entered(self, device):
        """Check properties of a device that was entered."""
        assert device.configuring is False
        assert device.connected is True
        assert device.entered is True

    async def test_already_closed(self, raw_device):
        """Check that we can exit a device that was not entered."""
        assert raw_device.entered is False
        await raw_device.__aexit__(None, None, None)
        assert raw_device.entered is False

    async def test_already_entered(self, device):
        """Try to enter an already entered device."""
        with pytest.raises(RuntimeError, match='already entered'):
            await device.__aenter__()

    async def test_configuration_mode(self, device):
        """Enter and test configuration mode."""
        async with device.configure() as config:
            assert device.configuring is True
            assert config.protocol_version == 1
