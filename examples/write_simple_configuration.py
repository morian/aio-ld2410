#!/usr/bin/env python

import asyncio
from aio_ld2410 import LD2410

async def main():
    async with LD2410('/dev/ttyUSB0') as device:
        async with device.configure():
            await device.set_parameters(
                moving_max_distance_gate=4,
                stopped_max_distance_gate=6,
                presence_timeout=10,
            )

if __name__ == '__main__':
    asyncio.run(main())
