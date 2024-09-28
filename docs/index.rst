Asyncio LD2410 Library
======================

.. module:: aio_ld2410
   :no-typesetting:

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

``aio-ld2410`` is a python library that allows interacting with the `Hi-Link LD2410`_ sensors
using :mod:`asyncio`.

.. _Hi-Link LD2410: https://hlktech.net/index.php?id=988

Such radar sensor would typically requires an USB-UART adapter on most computers but is
natively included on most embedded such as the `Raspberry Pi`_.

.. _Raspberry Pi: https://www.raspberrypi.com/

This library supports a wide range of variants in terms of models and firmware versions,
and was mostly tested on LD2410C_ with firmware ``v2.04.23022511``.

It features comprehensible methods to get and set various configuration parameters,
as well as :mod:`dataclasses` for output results and sensor reports.

.. _LD2410C: https://www.hlktech.net/index.php?id=1095

Here's how you can start reading sensor reports from a few lines of python:

.. literalinclude:: ../examples/read_simple_reports.py
   :language: python

.. toctree::
   :hidden:

   start/index
   api/index
   about/index
