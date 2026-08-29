Protocol references
===================

The protocol implementation is based on multiple sources as well as observed behavior
from a ``LD2410C`` module with firmware ``v2.04.23022511``.


Official English documentation
------------------------------

The first source of protocol information is the official documentation.
These can be found on the `official website`_, through Google drive links.

.. _official website: https://www.hlktech.net/index.php?id=1095

``aio-LD2410`` only implements protocols for the ``LD2410`` variants:

- ``LD2410 Serial Communication Protocol V1.02.pdf``
- ``LD2410B Serial communication protocol V1.07.pdf``
- ``HLK-LD2410C Serial communication protocol V1.07.pdf``

The ``LD2410D`` and ``LD2410S`` variants use a different protocol and are not covered
by this library.
