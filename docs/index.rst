Asyncio LD2410 Library
======================

.. module:: aio_ld2410
   :no-typesetting:

|licence| |version| |pyversions| |coverage| |docs| |openssf|

.. |licence| image:: https://img.shields.io/pypi/l/aio-ld2410.svg
   :target: https://pypi.org/project/aio-ld2410/

.. |version| image:: https://img.shields.io/pypi/v/aio-ld2410.svg
   :target: https://pypi.org/project/aio-ld2410/

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/aio-ld2410.svg
   :target: https://pypi.org/project/aio-ld2410/

.. |coverage| image:: https://codecov.io/github/morian/aio-ld2410/graph/badge.svg
   :target: https://app.codecov.io/github/morian/aio-ld2410

.. |docs| image:: https://img.shields.io/readthedocs/aio-ld2410.svg
   :target: https://aio-ld2410.readthedocs.io/

.. |openssf| image:: https://www.bestpractices.dev/projects/9487/badge
   :target: https://www.bestpractices.dev/en/projects/9487

``aio-ld2410`` is a python library that allows interacting with the `Hi-Link LD2410`_ sensors
using :mod:`asyncio`.

.. _Hi-Link LD2410: https://hlktech.net/index.php?id=988

Such radar sensor would typically require an USB-UART adapter on most computers but is
natively included on most embedded platforms such as the `Raspberry Pi`_.

.. _Raspberry Pi: https://www.raspberrypi.com/

This library supports devices LD2410_, LD2410B_ and LD2410C_ and may require a recent firmware
to fully support all features. Obviously bluetooth-related methods are not available on LD2410_.
Tests were mostly performed on LD2410C_ with firmware ``v2.04.23022511`` and ``v2.44.25070917``.

LD2410D_ and LD2410S_ use a different protocol and are not supported yet, which would require
an important refactor of this code base. Support status for LD2410-AA_ is not clear for now.

It features comprehensible methods to get and set various configuration parameters,
as well as dataclasses_ for output results and sensor reports.

.. _LD2410: https://www.hlktech.net/index.php?id=988
.. _LD2410B: https://www.hlktech.net/index.php?id=1094
.. _LD2410C: https://www.hlktech.net/index.php?id=1095
.. _LD2410D: https://www.hlktech.net/index.php?id=1376
.. _LD2410S: https://www.hlktech.net/index.php?id=1176
.. _LD2410-AA: https://www.hlktech.net/index.php?id=1488
.. _dataclasses: https://docs.python.org/3/library/dataclasses.html

Here's how you can start reading sensor reports from a few lines of python:

.. literalinclude:: ../examples/read_simple_reports.py
   :language: python

.. toctree::
   :hidden:

   start/index
   reference/index
   about/index
