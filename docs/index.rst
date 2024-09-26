Asyncio LD2410 Library
======================

|licence| |version| |pyversions| |coverage| |docs| |openssf|

.. |licence| image:: https://img.shields.io/pypi/l/aio_ld2410.svg
    :target: https://pypi.python.org/pypi/aio_ld2410

.. |version| image:: https://img.shields.io/pypi/v/aio_ld2410.svg
    :target: https://pypi.python.org/pypi/aio_ld2410

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/aio_ld2410.svg
    :target: https://pypi.python.org/pypi/aio_ld2410

.. |coverage| image:: https://codecov.io/github/morian/aio_ld2410/graph/badge.svg
   :target: https://codecov.io/github/morian/aio_ld2410

.. |docs| image:: https://img.shields.io/readthedocs/aio_ld2410.svg
   :target: https://aio_ld2410.readthedocs.io

.. |openssf| image:: https://bestpractices.coreinfrastructure.org/projects/9487/badge
   :target: https://bestpractices.coreinfrastructure.org/projects/9487

`aio_ld2410` is a library for interacting with `Hi-Link LD2410`_ radar sensors using asyncio.

.. _Hi-Link LD2410: https://hlktech.net/index.php?id=988

Such sensor would typically requires an USB-UART adapter on most computers but is natively
included on most embedded such as the `Raspberry Pi`_.

.. _Raspberry Pi: https://www.raspberrypi.com/

This library supports a wide range of variants in terms of models and firmware versions,
and was mostly tested on `LD2410C` with firmware `v2.04.23022511`. It features comprehensible
methods to get and set various configuration parameters, as well as :mod:`dataclasses` for
output results and sensor reports.

Here's how you can start reading sensor reports from a few lines of python:

.. literalinclude:: ../examples/read_simple_reports.py

.. toctree::
   :hidden:
