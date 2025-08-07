"""
Decorator functions for utility purposes.
"""

from collections.abc import Callable


def virtual(func: Callable) -> Callable:
    """
    Decorator to mark a function as virtual (can be overridden).
    """
    func._virtual = True  # type: ignore
    return func