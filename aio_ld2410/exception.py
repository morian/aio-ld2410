class AioLd2410Error(Exception):
    """Base error for exceptions generated by this library."""


class ConnectError(AioLd2410Error):
    """Raised when the device can no longer work."""


class CommandError(AioLd2410Error):
    """An error raised after a command was sent."""


class CommandStatusError(CommandError):
    """An error raised after a failure status was received."""