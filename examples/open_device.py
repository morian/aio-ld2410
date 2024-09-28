#!/usr/bin/env python

import asyncio
from aio_ld2410 import LD2410

async def main():
    async with LD2410('/dev/ttyUSB0') as device:
        ...

if __name__ == '__main__':
    asyncio.run(main())
