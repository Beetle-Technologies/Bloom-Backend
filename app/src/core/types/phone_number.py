from typing import Any

import phonenumbers
from phonenumbers import NumberParseException
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import InitErrorDetails, PydanticCustomError, ValidationError, core_schema


class PhoneNumber(str):
    """
    Pydantic type for international phone numbers in E.164 format.
    """

    DEFAULT_REGION: str | None = None  # No default region

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(core_schema)
        json_schema.update(
            type="string",
            pattern=r"^\+[1-9]\d{1,14}$",
            example="+1234567890",
            description="International phone number in E.164 format",
            defaultRegion=cls.DEFAULT_REGION,
        )
        return json_schema

    @classmethod
    def validate(cls, value: Any) -> "PhoneNumber":
        errors = []

        if not isinstance(value, str):
            errors.append(
                InitErrorDetails(
                    type=PydanticCustomError("value_error", "Phone number should be a string"),
                    input=value,
                )
            )

        if isinstance(value, str):
            if not value.strip():
                errors.append(
                    InitErrorDetails(
                        type=PydanticCustomError("value_error", "Phone number cannot be empty"),
                        input=value,
                    )
                )
            else:
                try:
                    parsed = phonenumbers.parse(value, cls.DEFAULT_REGION)

                    if not phonenumbers.is_valid_number(parsed):
                        errors.append(
                            InitErrorDetails(
                                type=PydanticCustomError(
                                    "value_error",
                                    "Invalid phone number: {value}",
                                    {"value": value},
                                ),
                                input=value,
                            )
                        )

                    # If no errors, format to E.164
                    if not errors:
                        formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                        return cls(formatted)

                except NumberParseException as e:
                    errors.append(
                        InitErrorDetails(
                            type=PydanticCustomError(
                                "value_error",
                                "Invalid phone number format: {error}",
                                {"error": str(e)},
                            ),
                            input=value,
                        )
                    )

        if errors:
            raise ValidationError.from_exception_data(
                title="invalid_phone_number",
                line_errors=errors,
            )

        return cls(value)

    def format_national(self) -> str:
        """Format phone number in national format"""
        try:
            parsed = phonenumbers.parse(str(self), None)
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
        except NumberParseException:
            return str(self)

    def format_international(self) -> str:
        """Format phone number in international format"""
        try:
            parsed = phonenumbers.parse(str(self), None)
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except NumberParseException:
            return str(self)

    def __repr__(self) -> str:
        return f"PhoneNumber('{str(self)}')"
