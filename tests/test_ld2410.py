from __future__ import annotations

import asyncio
import json
import logging

# Python 3.9 and lower have a distinct class for asyncio.TimeoutError.
from asyncio import (
    StreamReader,
    StreamWriter,
    TimeoutError as AsyncTimeoutError,
)
from dataclasses import asdict

import pytest

from aio_ld2410 import (
    LD2410,
    CommandContextError,
    CommandParamError,
    CommandReplyError,
    CommandStatusError,
    ConnectionClosedError,
    LightControl,
    OutPinLevel,
    ld2410,
)
from aio_ld2410.protocol import ReportFrame

from .emulator import EmulatorCode, EmulatorCommand

# All test coroutines will be treated as marked for anyio.
pytestmark = pytest.mark.anyio


class FakeLD2410(LD2410):
    """Fake LD2410 connector, using an unix socket instead."""

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
def raw_device(emulation_server):
    """A raw non-entered device."""
    return FakeLD2410(emulation_server)


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

    async def test_client_reuse(self, raw_device):
        """Checked whether we can reuse the LD2410 object multiple times."""

        assert raw_device.entered is False
        async with raw_device:
            assert raw_device.entered is True

        assert raw_device.entered is False
        async with raw_device:
            assert raw_device.entered is True

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
        with pytest.raises(CommandContextError, match='requires a configuration context'):
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
            await device.set_baud_rate(rate)

    @pytest.mark.parametrize('rate', [256, 12345])
    async def test_invalid_baud_rate(self, device, rate):
        """Check that we cannot set invalid baud rates."""
        async with device.configure():
            with pytest.raises(CommandParamError):
                await device.set_baud_rate(rate)

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
            with pytest.raises(
                CommandParamError,
                match='must have less than 7 ASCII characters',
            ):
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
            with pytest.raises(
                CommandParamError,
                match='Unknown index for distance resolution',
            ):
                await device.set_distance_resolution(90)

    async def test_factory_reset(self, device):
        """Check that we can ask for a factory reset."""
        async with device.configure():
            await device.reset_to_factory()

    @pytest.mark.parametrize(
        ('moving_max', 'static_max', 'presence_timeout'),
        [
            (8, 8, 2),
            (4, 4, 764),
            (264, 264, 65537),
        ],
    )
    async def test_parameters(self, device, moving_max, static_max, presence_timeout):
        """Check that we can set parameters."""
        async with device.configure():
            await device.set_parameters(
                moving_max_distance_gate=moving_max,
                static_max_distance_gate=static_max,
                presence_timeout=presence_timeout,
            )
            params = await device.get_parameters()
            assert params.moving_max_distance_gate == moving_max & 0xFF
            assert params.static_max_distance_gate == static_max & 0xFF
            assert params.presence_timeout == presence_timeout & 0xFFFF

    async def test_parameters_missing_kwarg(self, device):
        """Check that we cannot skip a parameter."""
        async with device.configure():
            with pytest.raises(CommandParamError, match='Missing parameters'):
                await device.set_parameters(
                    static_max_distance_gate=6,
                    presence_timeout=5,
                )

    @pytest.mark.parametrize('gate', range(9))
    async def test_gate_sensitivity_set(self, device, gate):
        """Check sensitivity when set to individual gates."""
        async with device.configure():
            moving = 100 - 2 * gate
            static = 100 - 3 * gate
            await device.set_gate_sensitivity(
                distance_gate=gate,
                moving_threshold=moving,
                static_threshold=static,
            )
            params = await device.get_parameters()
            assert params.moving_threshold[gate] == moving
            assert params.moving_threshold[gate] == moving

    async def test_gate_sensitivity_missing_kwarg(self, device):
        """Check gate sensitivity setter with a missing argument."""
        async with device.configure():
            with pytest.raises(CommandParamError, match='Missing parameters'):
                await device.set_gate_sensitivity(distance_gate=4, moving_threshold=90)

    @pytest.mark.parametrize(
        ('moving', 'static'),
        [
            (64, 64),
            (102, 102),
            (300, 300),
        ],
    )
    async def test_gate_sensitivity_set_broadcast(self, device, moving, static):
        """Check sensitivity when set through broadcast."""
        async with device.configure():
            await device.set_gate_sensitivity(
                distance_gate=0xFFFF,
                moving_threshold=moving,
                static_threshold=static,
            )
            params = await device.get_parameters()
            for i in range(params.max_distance_gate + 1):
                assert params.moving_threshold[i] == moving & 0xFF
                assert params.static_threshold[i] == static & 0xFF

    @pytest.mark.parametrize('gate', [9, 100, 657, 65549])
    async def test_gate_sensitivity_error(self, device, gate):
        """Check bad gate indices."""
        async with device.configure():
            with pytest.raises(CommandStatusError, match='received bad status: FAILURE'):
                await device.set_gate_sensitivity(
                    distance_gate=gate,
                    moving_threshold=10,
                    static_threshold=10,
                )

    async def test_module_restart_with_context_close(self, device):
        """Check a module restart in standard situation."""
        checked = True
        async with device.configure():
            await device.restart_module(close_config_context=True)

            # This is never reached because `restart_module`
            # was told to raises a `ModuleRestartedError`.
            checked = False

        assert checked is True

    async def test_module_restart_without_context_close(self, device):
        """Check additional values when we don't raise on module restart."""
        async with device.configure():
            assert device.configuring is True
            await device.restart_module()
            assert device.configuring is False

            with pytest.raises(CommandContextError, match='requires a configuration context'):
                await device.set_engineering_mode(True)

    @pytest.mark.parametrize(
        ('control', 'threshold', 'default'),
        [
            (LightControl.BELOW, 95, OutPinLevel.LOW),
            (LightControl.ABOVE, 156, OutPinLevel.HIGH),
        ],
    )
    async def test_light(self, device, control, threshold, default):
        """Check light controls."""
        async with device.configure():
            await device.set_light_control(
                control=control,
                threshold=threshold,
                default=default,
            )
            light = await device.get_light_control()
            assert light.control == control
            assert light.threshold == threshold & 0xFF
            assert light.default == default

    async def test_light_missing_kwarg(self, device):
        """Check light setter with a missing argument."""
        async with device.configure():
            with pytest.raises(CommandParamError, match='Missing parameters'):
                await device.set_light_control(threshold=24, default=OutPinLevel.LOW)

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
            with pytest.raises(AsyncTimeoutError):
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
            command = EmulatorCommand(code=EmulatorCode.DISCONNECT_AFTER_COMMAND)
            await device.send_emulator_command(command)

            # Disconnect occurs right after the command was sent.
            with pytest.raises(
                ConnectionClosedError,
                match='Device has disconnected',
            ):
                await device.get_distance_resolution()

            # Device was already disconnected and we already know it.
            with pytest.raises(
                ConnectionClosedError,
                match='We are not connected to the device',
            ):
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
            with pytest.raises(
                CommandReplyError,
                match='Unhandled distance resolution index',
            ):
                await device.get_distance_resolution()
