# SpecLoom

> Declarative data structure contract validation and transformation for Python.

SpecLoom is a lightweight, zero-dependency Python 3.12 library for defining declarative contracts on dictionary and JSON-like structures. It provides rich type validation, nested schema enforcement, regex checking, custom validator callbacks, array item rules, and non-destructive data coercion.

## Features

- **Zero Dependencies**: Pure Python 3.12 standard library.
- **Declarative Schemas**: Class-based schema definitions with clean syntax.
- **Nested Validation**: Support for deeply nested sub-schemas and list/array item contracts.
- **Field Constraints**: Min/max values, string length, regex patterns, enum choices, and custom validation callables.
- **Data Transformation**: Coerce raw input, inject default values, and strip undeclared keys.
- **Detailed Diagnostics**: Path-based error reporting (`user.addresses[0].zipcode`).

## Quick Start

```python
from specloom import Schema, Field, validate, transform

class AddressSchema(Schema):
    street = Field(type=str, required=True, min_length=3)
    zipcode = Field(type=str, pattern=r"^\d{5}$")

class UserSchema(Schema):
    username = Field(type=str, required=True, min_length=3)
    email = Field(type=str, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    age = Field(type=int, min_value=18, max_value=120, default=18)
    address = Field(schema=AddressSchema, required=False)
    roles = Field(array_item=str, default_factory=list)

data = {
    "username": "alex",
    "email": "alex@example.com",
    "age": "25",
    "address": {
        "street": "123 Main St",
        "zipcode": "90210"
    },
    "roles": ["admin", "editor"]
}

cleaned = transform(UserSchema, data)
result = validate(UserSchema, cleaned)
if result.ok:
    print("Data is valid!")
else:
    for err in result.errors:
        print(f"Error at {err.path}: {err.message}")
```

## Running Tests

```bash
python -m unittest discover -v
```

## License

MIT License.
