Exceptions
==========

.. currentmodule:: aio_ld2410


Exception hierarchy
-------------------

.. automodule:: aio_ld2410.exceptions


Base exceptions
---------------

These exceptions are never raised but are used as a base for others.

.. autoexception:: BaseAioLd2410Error
.. autoexception:: AioLd2410Error
.. autoexception:: CommandError


General exceptions
------------------

These are raised when there is a global issue with the device.

.. autoexception:: ConnectionClosedError


Command exceptions
------------------

These exceptions can be raised consequently to a command method.

.. autoexception:: CommandContextError
.. autoexception:: CommandParamError
.. autoexception:: CommandReplyError
.. autoexception:: CommandStatusError


Internal exceptions
-------------------

.. autoexception:: ModuleRestartedError
