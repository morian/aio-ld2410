import asyncio
from asyncio import StreamReader, StreamWriter

import pytest

from aio_ld2410 import LD2410, CommandError

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

    @pytest.mark.parametrize('mode', [True, False])
    async def test_engineering_mode_with_config_mode(self, device, mode):
        """Try to set the engineering mode with the configuration mode."""
        async with device.configure():
            await device.set_engineering_mode(mode)

    @pytest.mark.parametrize('mode', [True, False])
    async def test_engineering_mode_with_no_config_mode(self, device, mode):
        """Try to set the engineering mode without the configuration mode."""
        with pytest.raises(CommandError, match='requires a configuration context'):
            await device.set_engineering_mode(mode)

    async def test_bluetooth_mac_get(self, device):
        """Get and test the bluetooth's mac address."""
        async with device.configure():
            address = await device.get_bluetooth_address()
            assert isinstance(address, bytes)
            assert address.hex() == '8f272eb80f65'

    @pytest.mark.parametrize('rate', [256000, 9600])
    async def test_valid_baud_rate(self, device, rate):
        """Check that we can set valid baud rates."""
        async with device.configure():
            await device.set_baudrate(rate)

    @pytest.mark.parametrize('rate', [256, 12345])
    async def test_invalid_baud_rate(self, device, rate):
        """Check that we cannot set invalid baud rates."""
        async with device.configure():
            with pytest.raises(KeyError):
                await device.set_baudrate(rate)

    @pytest.mark.parametrize('mode', [True, False])
    async def test_bluetooth_set(self, device, mode):
        """Set the bluetooth mode."""
        async with device.configure():
            await device.set_bluetooth_mode(mode)

    @pytest.mark.parametrize('password', ['', 'abc', '4bcD3!'])
    async def test_valid_bluetooth_passwords(self, device, password):
        async with device.configure():
            await device.set_bluetooth_password(password)

    @pytest.mark.parametrize('password', ['4bcD3!G', 'Привет'])
    async def test_invalid_bluetooth_passwords(self, device, password):
        async with device.configure():
            with pytest.raises(CommandError, match='must have less than 7 ascii characters'):
                await device.set_bluetooth_password(password)

    async def test_firmware_version(self, device):
        """Check the firmware version and its __str__ method."""
        async with device.configure():
            fw_ver = await device.get_firmware_version()
            assert str(fw_ver) == '1.02.22062416'

    @pytest.mark.parametrize('resolution', [75, 20])
    async def test_valid_distance_resolution(self, device, resolution):
        """Set and get the distance resolution.

        Note that the read value here is taken into account immediately even if the device
        needs a restart to take it into account. This was observed on a real device.
        """
        async with device.configure():
            await device.set_distance_resolution(resolution)
            value = await device.get_distance_resolution()
            assert value == resolution

    async def test_invalid_distance_resolution(self, device):
        """Ensure we cannot set an arbitrary resolution value."""
        async with device.configure():
            with pytest.raises(CommandError, match='Unknown index for distance resolution'):
                await device.set_distance_resolution(90)

    async def test_factory_reset(self, device):
        """Check that we can ask for a factory reset."""
        async with device.configure():
            await device.reset_to_factory()
