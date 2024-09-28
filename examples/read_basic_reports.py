#!/usr/bin/env python

import asyncio
from aio_ld2410 import LD2410, TargetStatus

def format_basic_report(rep) -> str:
    items = []

    if rep.target_status & TargetStatus.STATIC:
        items.append(
            f'STATIC > dist {rep.static_distance:3d}'
            f' (energy {rep.static_energy:3d})'
        )
    else:
        items.append(30 * ' ')

    if rep.target_status & TargetStatus.MOVING:
        items.append(
            f'MOVING > dist {rep.moving_distance:3d}'
            f' (energy {rep.moving_energy:3d})'
        )
    else:
        items.append(30 * ' ')

    if rep.target_status:
        items.append(f'DETECT > dist {rep.detection_distance:3d}')
    else:
        items.append('')

    return ' | '.join(items)


async def main():
    async with LD2410('/dev/ttyUSB0') as device:
        async for report in device.get_reports():
            print('  ' + format_basic_report(report.basic))

if __name__ == '__main__':
    asyncio.run(main())
