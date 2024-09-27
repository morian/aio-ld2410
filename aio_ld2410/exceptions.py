"""
:mod:`aio_ld2410.exceptions` defines the following hierarchy of exceptions.

* :exc:`BaseAioLd2410Error`
    * :exc:`ModuleRestartedError`
    * :exc:`AioLd2410Error`
        * :exc:`ConnectionClosedError`
        * :exc:`CommandError`
            * :exc:`CommandContextError`
            * :exc:`CommandParamError`
            * :exc:`CommandReplyError`
            * :exc:`CommandStatusError`
"""

from __future__ import annotations


class BaseAioLd2410Error(BaseException):
    """Base error for all exceptions originating from this library."""


class AioLd2410Error(Exception, BaseAioLd2410Error):
    """Base error for all things that users would like to catch."""


class CommandError(AioLd2410Error):
    """Base error for everything related to commands sent to the device."""


class CommandContextError(CommandError):
    """Raised when a command was issued outside of a configuration context."""


class CommandParamError(CommandError):
    """Raised when command parameters are not suitable for the device."""


class CommandReplyError(CommandError):
    """Raised when the device replied with something we could not understand."""


class CommandStatusError(CommandError):
    """Raised after a failed status was received from device."""


class ConnectionClosedError(ConnectionError, AioLd2410Error):
    """
    Raised when we lost the connection to the target module.

    The only relevant action afterward is to close the current client.
    """


class ModuleRestartedError(BaseAioLd2410Error):
    """
    Raised when the module is being restarted.

    It is used internally to close the current configuration context.

    When the exception is asked from :meth:`.LD2410.restart_module`, make sure not to catch it.
    """
