"""String cleaning utilities for metadata normalization."""

import re
from typing import Any, Optional, Union


def clean_string(to_clean: Optional[str]) -> Union[str, None]:
    """Returns a lowercase string with only alphanumeric
    characters and underscores.

    Args:
        to_clean: String to clean
    Returns:
        str or None: Clean string
    """
    if to_clean is None:
        return None

    if isinstance(to_clean, bool):
        return str(to_clean).lower()

    try:
        # This might be used with numbers
        if is_number(to_clean):
            return str(to_clean)

        # Removes all whitespace
        cleaner = re.sub(r"\s+", "", to_clean, flags=re.UNICODE).lower()
        # Removes non-alphanumeric characters but keep underscores
        cleanest = re.sub(r"[^\w-]+", "", cleaner)
    except TypeError:
        return to_clean

    return cleanest


def is_number(s: Any) -> bool:
    """Is it a number?

    Args:
        s: String which may be a number
    Returns:
        bool
    """
    if isinstance(s, bool):
        return False

    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False
