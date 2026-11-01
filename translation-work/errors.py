class LocalizationError(Exception):
    """Base error for expected localization failures."""


class ConfigurationError(LocalizationError):
    """Raised when runtime configuration is incomplete or unsafe."""


class FormatError(LocalizationError):
    """Raised when a source or target file cannot be handled losslessly."""


class ProtectionError(LocalizationError):
    """Raised when protected content is malformed or damaged."""


class ValidationError(LocalizationError):
    """Raised when translated output violates a project invariant."""
