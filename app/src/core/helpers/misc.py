from datetime import date, datetime
from json import JSONEncoder
from typing import Any


def call(type: Any, name: str, *args, **kwargs) -> Any:
    """
    Call any object method or attributes safely

    Attributes:\n
        type (Any): Any object or type
        name (str): The name of the method or attributes

    Returns:\n
        Any: The object's value

    Raises:
        AttributeError - when the called method or attribute is not found
    """

    if hasattr(type, name):
        obj = getattr(type, name)
        if callable(obj):
            return obj(*args, **kwargs)
        else:
            if args or kwargs:
                raise AttributeError(f"{name} cannot accept arguments")
            return obj
    else:
        raise AttributeError(f"{type.__name__} has no attribute {name}")


class DateTimeEncoder(JSONEncoder):
    """Custom JSON encoder for datetime objects."""

    def default(self, obj: Any) -> Any:  # type: ignore
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)
