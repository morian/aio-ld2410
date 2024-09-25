from __future__ import annotations

import asyncio
import json
import logging
from asyncio import StreamReader, StreamWriter
from contextlib import suppress
from dataclasses import asdict

import pytest

from aio_ld2410 import (
    LD2410,
    AuxiliaryControl,
    CommandError,
    CommandStatusError,
    ModuleRestartedError,
    OutPinLevel,
    ld2410,
)
from aio_ld2410.protocol import ReportFrame

from .emulator import EmulatorCode, EmulatorCommand

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.anyio


class FakeLD2410(LD2410):
    """Fake LD2410 connector, using an unix socket instead."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def _open_serial_connection(self) -> tuple[StreamReader, StreamWriter]:
        """Open a fake serial connection for this device."""
        # An unix socket cannot have None or 0 as a limit.
        bufsize = self._read_bufsize or 8192
        return await asyncio.open_unix_connection(path=self._device, limit=bufsize)

    async def send_emulator_command(self, command: EmulatorCommand) -> None:
        """Write arbitrary data to the fake server."""
        command = json.dumps(asdict(command)).encode()
        frame = ReportFrame.build({'data': command})
        self._writer.write(frame)
        await self._writer.drain()


@pytest.fixture
def raw_device(fake_device_socket):
    """A raw non-entered device."""
    return FakeLD2410(fake_device_socket)


@pytest.fixture
async def device(raw_device):
    """A device that has been entered."""
    async with raw_device:
        yield raw_device


def test_configuration_decorator_error():
    """Check that our decorator can only be used on async methods."""
    with pytest.raises(RuntimeError, match='is only suitable for async methods'):

        @ld2410.configuration
        def not_suitable():
            pass


class TestLD2410:
    """Test LD2410 commands against the emulator."""

    async def test_bad_device(self):
        """Check that we get a suitable error."""
        device = FakeLD2410('/dev/non_existent_device')
        with pytest.raises(FileNotFoundError):
            async with device:
                pass
        assert device.connected is False
        assert device.entered is False

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

    async def test_invalid_distanke_resolution(self, device):
        """Ensure we cannot set an arbitrary resolution value."""
        async with device.configure():
            with pytest.raises(CommandError, match='Unknown index for distance resolution'):
                await device.set_distance_resolution(90)

    async def test_factory_reset(self, device):
        """Check that we can ask for a factory reset."""
        async with device.configure():
            await device.reset_to_factory()

    @pytest.mark.parametrize(
        ('motion_max', 'standstill_max', 'idle_duration'),
        [
            (8, 8, 2),
            (4, 4, 764),
            (264, 264, 65537),
        ],
    )
    async def test_parameters(self, device, motion_max, standstill_max, idle_duration):
        """Check that we can set parameters."""
        async with device.configure():
            await device.set_parameters(
                motion_max_distance_gate=motion_max,
                standstill_max_distance_gate=standstill_max,
                no_one_idle_duration=idle_duration,
            )
            params = await device.get_parameters()
            assert params.motion_max_distance_gate == motion_max & 0xFF
            assert params.standstill_max_distance_gate == standstill_max & 0xFF
            assert params.no_one_idle_duration == idle_duration & 0xFFFF

    @pytest.mark.parametrize('gate', range(9))
    async def test_gate_sensitivity_set(self, device, gate):
        """Check sensitivity when set to individual gates."""
        async with device.configure():
            motion = 100 - 2 * gate
            standstill = 100 - 3 * gate
            await device.set_gate_sentivity(
                distance_gate=gate,
                motion_sensitivity=motion,
                standstill_sensitivity=standstill,
            )
            params = await device.get_parameters()
            assert params.motion_sensitivity[gate] == motion
            assert params.motion_sensitivity[gate] == motion

    @pytest.mark.parametrize(
        ('motion', 'standstill'),
        [
            (64, 64),
            (102, 102),
            (300, 300),
        ],
    )
    async def test_gate_sensitivity_set_broadcast(self, device, motion, standstill):
        """Check sensitivity when set through broadcast."""
        async with device.configure():
            await device.set_gate_sentivity(
                distance_gate=0xFFFF,
                motion_sensitivity=motion,
                standstill_sensitivity=standstill,
            )
            params = await device.get_parameters()
            for i in range(params.max_distance_gate + 1):
                assert params.motion_sensitivity[i] == motion & 0xFF
                assert params.standstill_sensitivity[i] == standstill & 0xFF

    @pytest.mark.parametrize('gate', [9, 100, 657, 65549])
    async def test_gate_sensitivity_error(self, device, gate):
        """Check bad gate indices."""
        async with device.configure():
            with pytest.raises(CommandStatusError, match='received bad status: FAILURE'):
                await device.set_gate_sentivity(
                    distance_gate=gate,
                    motion_sensitivity=10,
                    standstill_sensitivity=10,
                )

    async def test_module_restart(self, device):
        """Check a module restart in standard situation."""
        checked = True
        async with device.configure():
            await device.restart_module()
            # This is never reached because `restart_module` raises a ModuleRestartedError.
            checked = False
        assert checked is True

    async def test_module_restart_inhibited(self, device):
        """Check additional values when we prevent a ModuleRestartedError."""
        async with device.configure():
            assert device.configuring is True
            with suppress(ModuleRestartedError):
                await device.restart_module()

            assert device.configuring is False
            with pytest.raises(CommandError, match='requires a configuration context'):
                await device.set_engineering_mode(True)

    @pytest.mark.parametrize(
        ('control', 'threshold', 'default'),
        [
            (AuxiliaryControl.UNDER_THRESHOLD, 95, OutPinLevel.LOW),
            (AuxiliaryControl.ABOVE_THRESHOLD, 156, OutPinLevel.HIGH),
        ],
    )
    async def test_auxiliary(self, device, control, threshold, default):
        """Check auxiliary controls."""
        async with device.configure():
            await device.set_auxiliary_controls(
                control=control,
                threshold=threshold,
                default=default,
            )
            aux = await device.get_auxiliary_controls()
            assert aux.control == control
            assert aux.threshold == threshold & 0xFF
            assert aux.default == default

    async def test_good_basic_report(self, device):
        """Get a basic report and check for it."""
        async with device.configure():
            await device.set_engineering_mode(False)

        # Another way to get reports through the iterator.
        iterator = device.get_reports()
        report = await iterator.__anext__()
        last = device.get_last_report()
        assert report.engineering is None
        assert report == last

    async def test_good_engineering_report(self, device):
        """Get an advanced report and check for it."""
        async with device.configure():
            await device.set_engineering_mode(True)
            await device.set_distance_resolution(20)

        report = await device.get_next_report()
        assert report.engineering is not None

    async def test_no_report_while_config(self, device):
        """Check that we get no report while configuring."""
        async with device.configure():
            with pytest.raises(TimeoutError):
                # 500ms is enough since we generate a report every 100ms.
                await asyncio.wait_for(device.get_next_report(), timeout=0.5)

    async def test_corrupted_frame(self, device, caplog):
        """Ask the emulator to generate a bad frame."""
        caplog.set_level(logging.WARNING)
        async with device.configure():
            command = EmulatorCommand(code=EmulatorCode.GENERATE_CORRUPTED_FRAME)
            await device.send_emulator_command(command)
        assert len(caplog.records) == 1, caplog.records
        assert caplog.records[0].message.startswith('Skipping 25 garbage bytes')

    async def test_corrupted_command(self, device, caplog):
        async with device.configure():
            command = EmulatorCommand(code=EmulatorCode.GENERATE_CORRUPTED_COMMAND)
            await device.send_emulator_command(command)
        assert len(caplog.records) == 1, caplog.records
        assert caplog.records[0].message.startswith('Unable to handle frame:')

    async def test_disconnect(self, device):
        async with device.configure():
            command = EmulatorCommand(code=EmulatorCode.DISCONNECT)
            await device.send_emulator_command(command)
            with pytest.raises(ConnectionError, match='Device has disconnected'):
                await device.get_distance_resolution()
            with pytest.raises(ConnectionError, match='We are not connected to the device'):
                await device.get_distance_resolution()

    async def test_spurious_reply(self, device, caplog):
        async with device.configure():
            command = EmulatorCommand(code=EmulatorCode.GENERATE_SPURIOUS_REPLY)
            await device.send_emulator_command(command)
        assert len(caplog.records) == 1, caplog.records
        assert caplog.records[0].message.startswith('Got reply code 0 (request was 254)')

    async def test_invalid_resolution(self, device):
        async with device.configure():
            command = EmulatorCommand(code=EmulatorCode.RETURN_INVALID_RESOLUTION)
            await device.send_emulator_command(command)
            with pytest.raises(CommandError, match='Unhandled distance resolution index'):
                await device.get_distance_resolution()
