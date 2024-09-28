#!/usr/bin/env python

import asyncio
from aio_ld2410 import LD2410

async def main():
    # We want it less sensitive for moving people.
    MOVING_CONFIG = [50, 50, 40, 40, 35, 30]
    # But a little bit more for people standing in front of the sensor.
    STOPPED_CONFIG = [0, 0, 40, 35, 30, 25, 20]

    async with LD2410('/dev/ttyUSB0') as device:
        async with device.configure():
            for i in range(len(MOVING_CONFIG)):
                await device.set_gate_sensitivity(
                    distance_gate=i,
                    moving_threshold=MOVING_CONFIG[i],
                    stopped_threshold=STOPPED_CONFIG[i],
                )

if __name__ == '__main__':
    asyncio.run(main())
