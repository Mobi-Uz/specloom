"""Data transformation and sanitization for SpecLoom."""

from __future__ import annotations
from typing import Any, Dict, Type, Union

from specloom.schema import Field, Schema


def _transform_dict(
    schema_cls: Union[Schema, Type[Schema]],
    data: Dict[str, Any],
    strip_unknown: bool = True
) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return data

    result: Dict[str, Any] = {}
    fields = schema_cls.get_fields()

    for field_name, field_def in fields.items():
        if field_name in data:
            val = data[field_name]
            if val is None and field_def.nullable:
                result[field_name] = None
                continue

            if field_def.coerce is not None and val is not None:
                try:
                    val = field_def.coerce(val)
                except Exception:
                    pass

            if field_def.schema is not None and isinstance(val, dict):
                val = _transform_dict(field_def.schema, val, strip_unknown=strip_unknown)
            elif field_def.array_item is not None and isinstance(val, (list, tuple)):
                item_spec = field_def.array_item
                transformed_items = []
                for item in val:
                    if isinstance(item_spec, type) and issubclass(item_spec, Schema) and isinstance(item, dict):
                        transformed_items.append(_transform_dict(item_spec, item, strip_unknown=strip_unknown))
                    else:
                        transformed_items.append(item)
                val = transformed_items

            result[field_name] = val
        else:
            default_val = field_def.get_default()
            if default_val is not None or field_def.default_factory is not None:
                result[field_name] = default_val

    if not strip_unknown:
        for k, v in data.items():
            if k not in fields:
                result[k] = v

    return result


def transform(
    schema: Union[Schema, Type[Schema]],
    data: Dict[str, Any],
    strip_unknown: bool = True
) -> Dict[str, Any]:
    """Transforms and sanitizes input data according to schema rules."""
    return _transform_dict(schema, data, strip_unknown=strip_unknown)
