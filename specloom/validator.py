"""Validation logic for SpecLoom schemas."""

from __future__ import annotations
from dataclasses import dataclass
import re
from typing import Any, Dict, List, Type, Union

from specloom.schema import Field, Schema
from specloom.exceptions import SpecValidationError


@dataclass
class ValidationError:
    """Details of a single validation failure."""
    path: str
    message: str
    code: str
    value: Any = None


class ValidationResult:
    """Holds the result of a schema validation run."""
    def __init__(self, is_valid: bool, errors: List[ValidationError]):
        self.is_valid = is_valid
        self.errors = errors

    @property
    def ok(self) -> bool:
        return self.is_valid

    def raise_for_status(self) -> None:
        if not self.is_valid:
            msg = f"Validation failed with {len(self.errors)} error(s)"
            raise SpecValidationError(msg, self.errors)


def _validate_field(
    field_def: Field,
    value: Any,
    path: str,
    errors: List[ValidationError]
) -> None:
    if value is None:
        if not field_def.nullable:
            errors.append(
                ValidationError(
                    path=path,
                    message=f"Field '{path}' cannot be None.",
                    code="null_not_allowed",
                    value=value,
                )
            )
        return

    if field_def.type is not None:
        if not isinstance(value, field_def.type):
            expected = (
                tuple(t.__name__ for t in field_def.type)
                if isinstance(field_def.type, tuple)
                else field_def.type.__name__
            )
            errors.append(
                ValidationError(
                    path=path,
                    message=f"Field '{path}' expected type {expected}, got {type(value).__name__}.",
                    code="type_mismatch",
                    value=value,
                )
            )
            return

    if field_def.choices is not None and value not in field_def.choices:
        errors.append(
            ValidationError(
                path=path,
                message=f"Field '{path}' value '{value}' not in allowed choices: {field_def.choices}.",
                code="choice_invalid",
                value=value,
            )
        )

    if hasattr(value, "__len__"):
        length = len(value)
        if field_def.min_length is not None and length < field_def.min_length:
            errors.append(
                ValidationError(
                    path=path,
                    message=f"Field '{path}' length {length} is less than minimum {field_def.min_length}.",
                    code="min_length",
                    value=value,
                )
            )
        if field_def.max_length is not None and length > field_def.max_length:
            errors.append(
                ValidationError(
                    path=path,
                    message=f"Field '{path}' length {length} is greater than maximum {field_def.max_length}.",
                    code="max_length",
                    value=value,
                )
            )

    if isinstance(value, (int, float)):
        if field_def.min_value is not None and value < field_def.min_value:
            errors.append(
                ValidationError(
                    path=path,
                    message=f"Field '{path}' value {value} is less than minimum {field_def.min_value}.",
                    code="min_value",
                    value=value,
                )
            )
        if field_def.max_value is not None and value > field_def.max_value:
            errors.append(
                ValidationError(
                    path=path,
                    message=f"Field '{path}' value {value} is greater than maximum {field_def.max_value}.",
                    code="max_value",
                    value=value,
                )
            )

    if field_def.pattern is not None and isinstance(value, str):
        pattern = field_def.pattern
        compiled = re.compile(pattern) if isinstance(pattern, str) else pattern
        if not compiled.search(value):
            errors.append(
                ValidationError(
                    path=path,
                    message=f"Field '{path}' does not match pattern {compiled.pattern}.",
                    code="pattern_mismatch",
                    value=value,
                )
            )

    if field_def.validator is not None:
        try:
            if not field_def.validator(value):
                errors.append(
                    ValidationError(
                        path=path,
                        message=f"Field '{path}' failed custom validation.",
                        code="custom_validation",
                        value=value,
                    )
                )
        except Exception as exc:
            errors.append(
                ValidationError(
                    path=path,
                    message=f"Field '{path}' validator raised error: {exc}",
                    code="custom_validation_error",
                    value=value,
                )
            )

    if field_def.schema is not None and isinstance(value, dict):
        sub_errors = _validate_dict(field_def.schema, value, parent_path=path)
        errors.extend(sub_errors)

    if field_def.array_item is not None and isinstance(value, (list, tuple)):
        item_spec = field_def.array_item
        for idx, item in enumerate(value):
            item_path = f"{path}[{idx}]"
            if isinstance(item_spec, Field):
                _validate_field(item_spec, item, item_path, errors)
            elif isinstance(item_spec, type) and issubclass(item_spec, Schema):
                if isinstance(item, dict):
                    errors.extend(_validate_dict(item_spec, item, parent_path=item_path))
                else:
                    errors.append(
                        ValidationError(
                            path=item_path,
                            message=f"Item at '{item_path}' expected dict for sub-schema.",
                            code="type_mismatch",
                            value=item,
                        )
                    )
            elif isinstance(item_spec, (type, tuple)):
                if not isinstance(item, item_spec):
                    errors.append(
                        ValidationError(
                            path=item_path,
                            message=f"Item at '{item_path}' expected type {item_spec}, got {type(item).__name__}.",
                            code="type_mismatch",
                            value=item,
                        )
                    )


def _validate_dict(
    schema_cls: Union[Schema, Type[Schema]],
    data: Dict[str, Any],
    parent_path: str = ""
) -> List[ValidationError]:
    errors: List[ValidationError] = []
    if not isinstance(data, dict):
        errors.append(
            ValidationError(
                path=parent_path or "root",
                message=f"Expected dictionary at '{parent_path or 'root'}', got {type(data).__name__}.",
                code="root_not_dict",
                value=data,
            )
        )
        return errors

    fields = schema_cls.get_fields()
    for field_name, field_def in fields.items():
        curr_path = f"{parent_path}.{field_name}" if parent_path else field_name
        if field_name not in data:
            if field_def.required and field_def.get_default() is None and not field_def.nullable:
                errors.append(
                    ValidationError(
                        path=curr_path,
                        message=f"Missing required field '{curr_path}'.",
                        code="missing_required",
                        value=None,
                    )
                )
        else:
            _validate_field(field_def, data[field_name], curr_path, errors)

    return errors


def validate(
    schema: Union[Schema, Type[Schema]],
    data: Dict[str, Any]
) -> ValidationResult:
    """Validates data dict against schema definition."""
    errors = _validate_dict(schema, data)
    return ValidationResult(is_valid=len(errors) == 0, errors=errors)
