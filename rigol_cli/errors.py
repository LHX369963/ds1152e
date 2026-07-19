class RigolError(Exception):
    """Base error shown by the CLI."""


class TransportError(RigolError):
    """Raised when USBTMC communication fails."""


class ProtocolError(RigolError):
    """Raised when a command or instrument response is invalid."""
