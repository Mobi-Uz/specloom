"""Schema and Field definitions for SpecLoom."""

from __future__ import annotations
from dataclasses import dataclass
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union


@dataclass
class Field:
    """Represents a schema rule for a single field in a structure."""
    type: Union[Type, Tuple[Type, ...], None] = None
    required: bool = True
    nullable: bool = False
    default: Any = None
    default_factory: Optional[Callable[[], Any]] = None
    validator: Optional[Callable[[Any], bool]] = None
    coerce: Optional[Callable[[Any], Any]] = None
    choices: Optional[List[Any]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[Union[str, re.Pattern]] = None
    schema: Optional[Union[Schema, Type[Schema]]] = None
    array_item: Optional[Union[Field, Type, Schema, Type[Schema]]] = None

    def get_default(self) -> Any:
        if self.default_factory is not None:
            return self.default_factory()
        return self.default


class Schema:
    """Base schema class for declaring nested data contracts."""
    _fields: Dict[str, Field] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        fields: Dict[str, Field] = {}
        for base in reversed(cls.__mro__):
            if issubclass(base, Schema) and hasattr(base, "_fields"):
                fields.update(base._fields)
        
        for name, value in cls.__dict__.items():
            if name.startswith("_"):
                continue
            if isinstance(value, Field):
                fields[name] = value
            elif isinstance(value, type) and issubclass(value, Schema):
                fields[name] = Field(schema=value)
            elif isinstance(value, (type, tuple)):
                fields[name] = Field(type=value)
        cls._fields = fields

    @classmethod
    def get_fields(cls) -> Dict[str, Field]:
        return cls._fields
