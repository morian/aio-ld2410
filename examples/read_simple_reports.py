#!/usr/bin/env python

import asyncio
from aio_ld2410 import LD2410

async def main():
    async with LD2410('/dev/ttyUSB0') as device:
        async with device.configure():
            ver = await device.get_firmware_version()
            print(f'[+] Running with firmware v{ver}')

        # Reports are typically generated every 100ms.
        async for report in device.get_reports():
            print(report)

if __name__ == '__main__':
    asyncio.run(main())
