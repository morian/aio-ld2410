Python asyncio LD2410 Library
=============================

`aio_ld2410` allows you to interact with the LD2410 radar sensors from Hi-Link using asyncio.
Implementation was performed against a LD2410C device with firmware v2.04.23022511.
It works with a serial adapter on a typical computer, or natively on a Raspberry Pi.

## How to install

This package requires python 3.9 or later, and depends on the following packages:
- [construct](https://pypi.org/project/construct/) for binary serialization/deserialization
- [dacite](https://pypi.org/project/dacite/) to build dataclasses with a minimal footprint
- [pyserial-asyncio-fast](https://pypi.org/project/pyserial-asyncio-fast/) for serial async communication


### Install from pip

```console
pip install aio-ld2410
```

### Install for development
```console
$ python -m venv venv
$ source venv/bin/activate
$ make install
```

## Implementation references

User manual and serial communication protocol can be found on
[Hi-Link Website](https://www.hlktech.net/index.php?id=1095).
This implementation was originally based on `LD2410C Serial communication protocol V1.00.pdf`.

Auxiliary commands were implemented based on `LD2410B Serial communication protocol V1.06.pdf`,
translated from Chinese, as mentioned in the following comment:
- https://github.com/esphome/feature-requests/issues/2156#issuecomment-1472962509

Note that some commands may not be available depending on your device model and firmware version.


## Example usage

```python
from aio_ld2410 import LD2410

async def async_main():
    async with LD2410('/dev/ttyUSB0', baudrate=256000) as device:
        async with device.configure():
            ver = await device.get_firmware_version()
            print(f'Running with firmware {ver}')

            # Ask for engineering (advanced) reports as well.
            await device.set_engineering_mode(True)

        # Reports are generated every 100ms.
        async for report in device.get_reports():
            print(report)
```

Full documentation is not written yet.
