from __future__ import annotations


class BaseAioLd2410Error(BaseException):
    """Base error for all exceptions originating from this library."""


class AioLd2410Error(Exception, BaseAioLd2410Error):
    """Base error for all things that should be caught by users."""


class CommandError(AioLd2410Error):
    """Base error for everything related to commands sent to the device."""


class CommandContextError(CommandError):
    """Raised when a command was issued outside of the configuration context."""


class CommandParamError(CommandError):
    """Raised when command parameters are not suitable for the device."""


class CommandStatusError(CommandError):
    """Raised after a failure status was received from device."""


class ConnectionClosedError(ConnectionError, AioLd2410Error):
    """Raised when we lost the connection to the target module.

    The only relevant action afterward is to close the current client.
    """


class CommandReplyError(CommandError):
    """Raised when the device replied with something we could not understand."""


class ModuleRestartedError(BaseAioLd2410Error):
    """Raised when told to when the module is restarting.

    It is used internally to close the current configuration context.
    If you ask for this exception, make sure not to catch it.
    """
