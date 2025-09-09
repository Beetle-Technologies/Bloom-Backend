from typing import Any, Optional, Union, get_args, get_origin

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo


def make_fields_optional(model_class: type[BaseModel]) -> type[BaseModel]:
    """
    Create a new Pydantic model with all fields made optional,
    except for fields that already have None as their default value.

    Args:
        model_class: The original Pydantic BaseModel class

    Returns:
        A new Pydantic model class with optional fields
    """
    fields = model_class.model_fields

    new_fields: dict[str, Any] = {}

    for field_name, field_info in fields.items():
        original_annotation = field_info.annotation

        from pydantic_core import PydanticUndefined

        has_default = field_info.default is not PydanticUndefined
        has_default_factory = field_info.default_factory is not None

        is_already_optional = get_origin(original_annotation) is Union and type(None) in get_args(original_annotation)

        if has_default or has_default_factory or is_already_optional:
            new_fields[field_name] = (original_annotation, field_info)
        else:
            new_annotation = Optional[original_annotation]
            new_field_info = FieldInfo(
                default=None,
                description=field_info.description,
                title=field_info.title,
                alias=field_info.alias,
                validation_alias=field_info.validation_alias,
                serialization_alias=field_info.serialization_alias,
                examples=field_info.examples,
                exclude=field_info.exclude,
                json_schema_extra=field_info.json_schema_extra,
                frozen=field_info.frozen,
                validate_default=field_info.validate_default,
                repr=field_info.repr,
                init=field_info.init,
                init_var=field_info.init_var,
                kw_only=field_info.kw_only,
                discriminator=field_info.discriminator,
            )
            new_fields[field_name] = (new_annotation, new_field_info)

    new_model_name = f"{model_class.__name__}Optional"
    new_model = create_model(new_model_name, **new_fields, __base__=BaseModel)

    if model_class.__doc__:
        new_model.__doc__ = f"Optional version of {model_class.__name__}. {model_class.__doc__}"

    return new_model


def optional(cls) -> type[BaseModel]:
    """
    Make all fields of a Pydantic model optional,
    """
    return make_fields_optional(cls)
