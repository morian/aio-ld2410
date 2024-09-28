#!/usr/bin/env python

import asyncio
from aio_ld2410 import LD2410

async def main():
    async with LD2410('/dev/ttyUSB0') as device:
        async with device.configure():
            await device.set_distance_resolution(20)
            await device.restart_module()

        print('....DEVICE IS RESTARTING....')
        await asyncio.sleep(2.0)

        async with device.configure():
            res = await device.get_distance_resolution()

    print(f'Each gate covers {res} centimeters')

if __name__ == '__main__':
    asyncio.run(main())
