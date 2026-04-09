# Copyright © 2012-2026 Vaughn Vernon. All rights reserved.
# Copyright © 2012-2026 Kalele, Inc. All rights reserved.
#
# See: LICENSE.md in repository root directory
#
# This file is part of DomoActors-Py.
#
# DomoActors-Py is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# DomoActors-Py is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DomoActors-Py. If not, see <https://www.gnu.org/licenses/>.

"""
Actor Address - Unique identity for actors in the system.
"""

from abc import ABC, abstractmethod
from typing import Any
import uuid
from datetime import datetime


class Address(ABC):
    """Abstract base class for actor addresses."""

    @abstractmethod
    def value_as_string(self) -> str:
        """
        Get the address as a string representation.

        Returns:
            String representation of the address
        """
        pass

    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        """Check equality with another address."""
        pass

    @abstractmethod
    def __hash__(self) -> int:
        """Get hash code for the address."""
        pass

    @abstractmethod
    def __str__(self) -> str:
        """String representation of the address."""
        pass


class Uuid7Address(Address):
    """
    UUIDv7-based address implementation.

    Uses time-sortable UUIDs for globally unique, distributed actor addressing.
    """

    def __init__(self, uuid_value: uuid.UUID | None = None) -> None:
        """
        Initialize with a UUID value or generate a new one.

        Args:
            uuid_value: Optional UUID to use, otherwise generates a new UUIDv7
        """
        if uuid_value is None:
            # Generate UUIDv7 (time-sortable)
            # Python's uuid7() is available in Python 3.12+, fallback to uuid4 for older versions
            try:
                self._value = uuid.uuid7()
            except AttributeError:
                # Fallback for Python < 3.12 - use uuid1 for time-based
                self._value = uuid.uuid1()
        else:
            self._value = uuid_value

    def value_as_string(self) -> str:
        """
        Get the UUID as a string.

        Returns:
            String representation of the UUID
        """
        return str(self._value)

    @property
    def value(self) -> uuid.UUID:
        """
        Get the UUID value.

        Returns:
            The UUID object
        """
        return self._value

    def __eq__(self, other: Any) -> bool:
        """
        Check equality with another Uuid7Address.

        Args:
            other: Object to compare with

        Returns:
            True if addresses are equal
        """
        if not isinstance(other, Uuid7Address):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        """
        Get hash code for the address.

        Returns:
            Hash of the UUID
        """
        return hash(self._value)

    def __str__(self) -> str:
        """
        String representation.

        Returns:
            String form of the UUID
        """
        return self.value_as_string()


class NumericAddress(Address):
    """
    Numeric sequence-based address implementation.

    Simple sequential numeric IDs for single-node deployments.
    """

    _next_id: int = 1
    _lock = None  # Will be initialized with threading.Lock() if needed

    def __init__(self, id_value: int | None = None) -> None:
        """
        Initialize with a numeric ID or generate the next sequential one.

        Args:
            id_value: Optional ID to use, otherwise uses next sequential ID
        """
        if id_value is None:
            # Thread-safe ID generation
            import threading
            if NumericAddress._lock is None:
                NumericAddress._lock = threading.Lock()

            with NumericAddress._lock:
                self._value = NumericAddress._next_id
                NumericAddress._next_id += 1
        else:
            self._value = id_value

    def value_as_string(self) -> str:
        """
        Get the numeric ID as a string.

        Returns:
            String representation of the numeric ID
        """
        return str(self._value)

    @property
    def value(self) -> int:
        """
        Get the numeric value.

        Returns:
            The numeric ID
        """
        return self._value

    def __eq__(self, other: Any) -> bool:
        """
        Check equality with another NumericAddress.

        Args:
            other: Object to compare with

        Returns:
            True if addresses are equal
        """
        if not isinstance(other, NumericAddress):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        """
        Get hash code for the address.

        Returns:
            Hash of the numeric value
        """
        return hash(self._value)

    def __str__(self) -> str:
        """
        String representation.

        Returns:
            String form of the numeric ID
        """
        return self.value_as_string()
