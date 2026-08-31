#!/usr/bin/env python

import asyncio
from datetime import datetime, timezone
from aio_ld2410 import BackgroundNoiseStatus, LD2410

# How long the real calibration process lasts (in seconds).
DURATION = 15

async def main():
    async with LD2410('/dev/ttyUSB0') as device:
        async with device.configure():
            status = await device.get_noise_detection_status()
            print(f'[>] Initial status: {status.name}')

            print('[+] Starting automatic calibration...')
            await device.start_noise_detection(DURATION)

            start = datetime.now(timezone.utc)

            print('[1] Move away from the sensor within the next 10 seconds...')

            await asyncio.sleep(10)

            print(f'[2] Detecting background noise for {DURATION} seconds.')

            status = await device.get_noise_detection_status()
            while status != BackgroundNoiseStatus.COMPLETED:
                await asyncio.sleep(0.2)
                status = await device.get_noise_detection_status()
                print(f'[.] Process status: {status.name:15s}\r', end='')
            print()

            duration = datetime.now(timezone.utc) - start
            print(f'[+] Total duration was {duration.total_seconds():.2f} seconds')


if __name__ == '__main__':
    asyncio.run(main())
