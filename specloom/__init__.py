"""SpecLoom: Declarative data structure contract validation and transformation."""

from specloom.schema import Field, Schema
from specloom.validator import ValidationResult, ValidationError, validate
from specloom.transformer import transform
from specloom.exceptions import SpecLoomError, SchemaDefinitionError, SpecValidationError

__version__ = "0.1.0"
__all__ = [
    "Field",
    "Schema",
    "ValidationResult",
    "ValidationError",
    "validate",
    "transform",
    "SpecLoomError",
    "SchemaDefinitionError",
    "SpecValidationError",
]
