"""Core exceptions for OmniAudit."""


class OmniAuditError(Exception):
    """Base exception for all OmniAudit errors."""
    pass


class PluginError(OmniAuditError):
    """Base exception for plugin errors."""
    pass


class PluginLoadError(PluginError):
    """Raised when plugin cannot be loaded."""
    pass


class PluginExecutionError(PluginError):
    """Raised when plugin execution fails."""
    pass


class ConfigurationError(OmniAuditError):
    """Raised when configuration is invalid."""
    pass


class DataStoreError(OmniAuditError):
    """Raised when data storage operations fail."""
    pass


class APIError(OmniAuditError):
    """Raised when API operations fail."""
    pass
