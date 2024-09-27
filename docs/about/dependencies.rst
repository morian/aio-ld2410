Dependencies
============

Runtime dependencies
--------------------

``aio-ld2410`` would not have been possible without the following great projects:

- construct_: library used to serialize and deserialize LD2410's protocol structures
  to binary bytes that are then sent and received on top of the asynchronous UART link.
- dacite_: ligthweight library used to build :mod:`dataclasses` out of the construct_ structures.
- pyserial-asyncio-fast_: a fast and reliable :mod:`asyncio` library for serial communication.

.. _construct: https://pypi.org/project/construct/
.. _dacite: https://pypi.org/project/dacite/
.. _pyserial-asyncio-fast: https://pypi.org/project/pyserial-asyncio-fast/


Development dependencies
------------------------

.. literalinclude:: ../../tests/requirements-linting.txt
   :caption: Linting requirements
   :language: text

.. literalinclude:: ../../tests/requirements-testing.txt
   :caption: Testing requirements
   :language: text

.. literalinclude:: ../../docs/requirements.txt
   :caption: Documentation requirements
   :language: text
