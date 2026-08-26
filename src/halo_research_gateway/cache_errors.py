"""Custom exceptions for Halo Research Gateway cache."""

class SchemaTooNewError(Exception):
    """Raised when database schema is newer than what this code understands."""
    pass


class EntryTooLargeError(Exception):
    """Raised when a cache entry exceeds the maximum allowed size."""
    pass
