import unittest
from specloom import (
    Field,
    Schema,
    validate,
    transform,
    SpecValidationError,
)


class SimpleSchema(Schema):
    name = Field(type=str, required=True, min_length=2)
    score = Field(type=int, min_value=0, max_value=100, default=50)
    category = Field(choices=["A", "B", "C"], default="A")


class AddressSchema(Schema):
    city = Field(type=str, required=True)
    zipcode = Field(type=str, pattern=r"^\d{5}$")


class UserSchema(Schema):
    name = Field(type=str, required=True)
    age = Field(type=(int, float), min_value=0)
    address = Field(schema=AddressSchema, required=False)
    tags = Field(array_item=str, default_factory=list)


class TestSpecLoomValidation(unittest.TestCase):
    def test_valid_simple_schema(self):
        data = {"name": "Alice", "score": 85, "category": "B"}
        res = validate(SimpleSchema, data)
        self.assertTrue(res.ok)
        self.assertEqual(len(res.errors), 0)

    def test_missing_required_field(self):
        data = {"score": 85}
        res = validate(SimpleSchema, data)
        self.assertFalse(res.ok)
        self.assertEqual(res.errors[0].code, "missing_required")
        self.assertEqual(res.errors[0].path, "name")

    def test_type_mismatch(self):
        data = {"name": 12345}
        res = validate(SimpleSchema, data)
        self.assertFalse(res.ok)
        self.assertEqual(res.errors[0].code, "type_mismatch")

    def test_min_length_validation(self):
        data = {"name": "A"}
        res = validate(SimpleSchema, data)
        self.assertFalse(res.ok)
        self.assertEqual(res.errors[0].code, "min_length")

    def test_choice_validation(self):
        data = {"name": "Alice", "category": "Z"}
        res = validate(SimpleSchema, data)
        self.assertFalse(res.ok)
        self.assertEqual(res.errors[0].code, "choice_invalid")

    def test_range_validation(self):
        data = {"name": "Alice", "score": 150}
        res = validate(SimpleSchema, data)
        self.assertFalse(res.ok)
        self.assertEqual(res.errors[0].code, "max_value")

    def test_nested_schema_validation(self):
        data = {
            "name": "Bob",
            "age": 30,
            "address": {"city": "New York", "zipcode": "10001"},
            "tags": ["developer", "python"],
        }
        res = validate(UserSchema, data)
        self.assertTrue(res.ok)

    def test_nested_schema_failure(self):
        data = {
            "name": "Bob",
            "age": 30,
            "address": {"city": "New York", "zipcode": "INVALID"},
        }
        res = validate(UserSchema, data)
        self.assertFalse(res.ok)
        self.assertEqual(res.errors[0].path, "address.zipcode")
        self.assertEqual(res.errors[0].code, "pattern_mismatch")

    def test_array_item_validation(self):
        data = {"name": "Bob", "age": 30, "tags": ["dev", 123]}
        res = validate(UserSchema, data)
        self.assertFalse(res.ok)
        self.assertEqual(res.errors[0].path, "tags[1]")
        self.assertEqual(res.errors[0].code, "type_mismatch")


class TestSpecLoomTransformation(unittest.TestCase):
    def test_defaults_injection(self):
        data = {"name": "Charlie"}
        transformed = transform(SimpleSchema, data)
        self.assertEqual(transformed["score"], 50)
        self.assertEqual(transformed["category"], "A")

    def test_strip_unknown(self):
        data = {"name": "Charlie", "unknown_key": "should_be_removed"}
        transformed = transform(SimpleSchema, data, strip_unknown=True)
        self.assertNotIn("unknown_key", transformed)

    def test_preserve_unknown_when_disabled(self):
        data = {"name": "Charlie", "extra": "keep_me"}
        transformed = transform(SimpleSchema, data, strip_unknown=False)
        self.assertIn("extra", transformed)
        self.assertEqual(transformed["extra"], "keep_me")

    def test_coercion(self):
        class CoerceSchema(Schema):
            age = Field(type=int, coerce=int)

        data = {"age": "42"}
        transformed = transform(CoerceSchema, data)
        self.assertEqual(transformed["age"], 42)

    def test_raise_for_status(self):
        data = {"name": "A"}
        res = validate(SimpleSchema, data)
        with self.assertRaises(SpecValidationError):
            res.raise_for_status()


if __name__ == "__main__":
    unittest.main()
