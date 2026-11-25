"""Exception definitions for SpecLoom."""

class SpecLoomError(Exception):
    """Base exception for all SpecLoom errors."""
    pass


class SchemaDefinitionError(SpecLoomError):
    """Raised when a schema definition is invalid."""
    pass


class SpecValidationError(SpecLoomError):
    """Raised when data validation fails during strict execution."""
    def __init__(self, message: str, errors: list):
        super().__init__(message)
        self.errors = errors
