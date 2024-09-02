from __future__ import annotations

import logging
import re

from .exceptions import logExceptionHelper

_logger = logging.getLogger(__name__)


def camelToSnake(value: str) -> str:
    """Convert CamelCase to snake_case."""
    return re.sub(r'(?<!^)(?=[A-Z])', '_', str(value)).lower()


def snakeToCamel(value: str) -> str:
    """Convert snake_case to CamelCase."""
    values = str(value).split('_')
    return values[0] + ''.join(ele.title() for ele in values[1:])


def toJson(obj: object, errors='raise'):
    """
    Serializer method will return the JSON representation of the object.

    :param obj: Object to be serialized, should be an object
    :param errors: Whether to 'ignore', 'warning' or 'raise' errors, should be str
    :return: json_data - Any
    """
    if hasattr(obj, 'toJson'):
        if callable(obj.toJson):
            return obj.toJson()

        msg = f"'{obj.__name__}': Expected type 'Callable', got '{type(obj.toJson).__name__}'"
        logExceptionHelper(msg, errors, TypeError)
    else:
        if isinstance(obj, set):
            return list(obj)

        msg = f"'{obj.__name__}' object has no attribute 'toJson'"
        logExceptionHelper(msg, errors, AttributeError)
