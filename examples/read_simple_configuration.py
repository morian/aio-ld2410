#!/usr/bin/env python

import asyncio
from aio_ld2410 import LD2410
from collections.abc import Iterable

def format_values(values: Iterable[int]) -> str:
    return ' | '.join(map('{:3d}'.format, values))

async def main():
    async with LD2410('/dev/ttyUSB0') as device:
        async with device.configure():
            cfg = await device.get_parameters()

    print(f'Max distance gate           {cfg.max_distance_gate}')
    print(f'Max motion detection gate   {cfg.moving_max_distance_gate}')
    print(f'Max static detection gate   {cfg.static_max_distance_gate}')
    print(f'Presence timeout            {cfg.presence_timeout}')
    print('Detection thresholds:')
    print('  Gate    ' + format_values(range(cfg.max_distance_gate + 1)))
    print('  Moving  ' + format_values(cfg.moving_threshold))
    print('  Static  ' + format_values(cfg.static_threshold))

if __name__ == '__main__':
    asyncio.run(main())
