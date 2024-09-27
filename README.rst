Python asyncio LD2410 Library
=============================

|licence| |version| |pyversions| |coverage| |docs| |openssf|

.. |licence| image:: https://img.shields.io/pypi/l/aio-ld2410.svg
   :target: https://pypi.python.org/pypi/aio-ld2410

.. |version| image:: https://img.shields.io/pypi/v/aio-ld2410.svg
   :target: https://pypi.python.org/pypi/aio-ld2410

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/aio-ld2410.svg
   :target: https://pypi.python.org/pypi/aio-ld2410

.. |coverage| image:: https://codecov.io/github/morian/aio-ld2410/graph/badge.svg
   :target: https://codecov.io/github/morian/aio-ld2410

.. |docs| image:: https://img.shields.io/readthedocs/aio-ld2410.svg
   :target: https://aio-ld2410.readthedocs.io/en/latest/

.. |openssf| image:: https://bestpractices.coreinfrastructure.org/projects/9487/badge
   :target: https://bestpractices.coreinfrastructure.org/projects/9487

``aio-ld2410`` is a python library that allows you to interact with the `Hi-Link LD2410`_ radar
sensors from Hi-Link using asyncio_.

.. _Hi-Link LD2410: https://hlktech.net/index.php?id=988
.. _asyncio: https://docs.python.org/3/library/asyncio.html

Such sensor would typically requires an USB-UART adapter on most computers but is natively
included on most embedded such as the `Raspberry Pi`_.

.. _Raspberry Pi: https://www.raspberrypi.com/

This library supports a wide range of variants in terms of models and firmware versions,
and was mostly tested on LD2410C_ with firmware ``v2.04.23022511``.

It features comprehensible methods to get and set various configuration parameters,
as well as dataclasses_ for output results and sensor reports.

.. _LD2410C: https://www.hlktech.net/index.php?id=1095
.. _dataclasses: https://docs.python.org/3/library/dataclasses.html


Installation
------------

This package requires Python 3.9 or later and pulls a few other packages as dependencies.

To install ``aio-ld2410``, simply run the following command:

.. code-block:: console

    $ pip install aio-ld2410


Usage
-----

Here's how you can start reading sensor reports from a few lines of python:

.. code-block:: python

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

   asyncio.run(main())

To go further please refer to the documentation_.

.. _documentation: https://aio-ld2410.readthedocs.io/en/latest/


Contributing
------------

Contributions, bug reports and feedbacks are very welcome, feel free to open
an issue_, send a `pull request`_. or `start a discussion`_.

Participants must uphold the `code of conduct`_.

.. _issue: https://github.com/morian/aio-ld2410/issues/new
.. _pull request: https://github.com/morian/aio-ld2410/compare/
.. _start a discussion: https://github.com/morian/aio-ld2410/discussions
.. _code of conduct: https://github.com/python-websockets/websockets/blob/main/CODE_OF_CONDUCT.md

``aio-ld2410`` is released under the `MIT license`_.

.. _MIT license: https://github.com/morian/aio-ld2410/blob/main/LICENSE
