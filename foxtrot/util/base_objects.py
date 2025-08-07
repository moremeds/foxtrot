"""
Base data structures for trading platform.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .constants import Status

# Constants
INFO: int = 20
ACTIVE_STATUSES = {Status.SUBMITTING, Status.NOTTRADED, Status.PARTTRADED}


@dataclass
class BaseData:
    """
    Any data object needs a adapter_name as source
    and should inherit base data.
    """

    adapter_name: str

    extra: dict[str, Any] | None = field(default=None, init=False)