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
- ``LD2410B Serial communication protocol V1.04.pdf``
- ``LD2410C Serial communication protocol V1.00.pdf``

The ``LD2410S`` variant seems to be quite different and was not covered by this library.


That anonymous hero on github
-----------------------------

There is a Chinese version of the ``LD2410B Serial communication protocol V1.06``
from which were extracted the following additional commands:

- Read the distance resolution parameter
- Write the distance resolution parameter
- Read auxiliary control parameters
- Write auxiliary control parameters

We also get details on two additional fields provided in the engineering report:

- Photo-sensitivity detection value
- ``OUT`` pin status

It was found, translated and provided on `this github issue`_.

These features seems to only be available on the latest firmware versions.

.. _this github issue: https://github.com/esphome/feature-requests/issues/2156#issuecomment-1472962509
