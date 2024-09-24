from __future__ import annotations

import logging
import re

_logger = logging.getLogger(__name__)


def camelToSnake(value: str) -> str:
    """Convert CamelCase to snake_case."""
    return re.sub(r'(?<!^)(?=[A-Z])', '_', str(value)).lower()


def snakeToCamel(value: str) -> str:
    """Convert snake_case to CamelCase."""
    values = str(value).split('_')
    return values[0] + ''.join(ele.title() for ele in values[1:])


def stripText(text: str, replace_with: str = '_', lower: bool = True, strip: bool = True, default: set = None,
              include: set = None, exclude: set = None) -> str:
    """
    Strip text by replacing substrings and remove excess values.

    :param text: Input string to be stripped, should be a str
    :param replace_with: Value to replace the substrings, should be a str
    :param lower: Whether to convert text to lowercase, should be a bool
    :param strip: Whether to strip excess values from the text, should be a bool
    :param default: Default array of substrings to replace, should be a set[str]
    :param include: Substrings to include in replace array, should be a set[str]
    :param exclude: Substrings to excluded from replace array, should be a set[str]
    :return: stripped_text - str
    """
    if default is None:
        default = set(" `~!@#$%^&*()-_=+|[{]};:',<.>/?\\\n\t" + '"')
    if include is None:
        include = set()
    if exclude is None:
        exclude = set()

    text = str(text)
    if lower:
        text = text.lower()

    substrings_to_replace = default.union(include) - exclude

    # Replace longer substrings first
    for char in sorted(substrings_to_replace, key=len, reverse=True):
        if char != replace_with:
            text = text.replace(char, replace_with)
        if not text:
            break

    # Remove excess replace with values
    if replace_with and text:
        text = re.sub(f"{re.escape(replace_with)}+", replace_with, text)
    if strip and text:
        return text.strip(replace_with or None)
    return text


def sanitiseText(raw_text: str, replace_: set = None, remove_: set = None, sep: str = '_') -> str:
    """
    Sanitise text with a set of operations, simplify text for easier comparisons.

    :param raw_text: Input string to be sanitised, should be a str
    :param replace_: Substrings to be replaced by sep, should be a set[str]
    :param remove_: Substrings to be removed, should be a set[str]
    :param sep: Value to replace the substrings and act as known seperator, should be a str
    :return:
    """
    fmt_text = str(raw_text)
    if replace_:
        fmt_text = stripText(fmt_text, replace_with=sep, default=replace_)
    if remove_:
        fmt_text = stripText(fmt_text, replace_with='', default=remove_)
    return stripText(fmt_text, replace_with=sep, default=set())  # Remove excess seps


def sanitiseLabel(raw_label: str) -> str:
    """Sanitise label with a set of operations, simplify text for easier comparisons."""
    if not raw_label:
        return raw_label or ''
    return sanitiseText(raw_label, set(' -|;'), set('\'`~!@#$%^&*()=+[{]}:,<.>/?\\'))