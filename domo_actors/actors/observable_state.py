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
Observable State pattern for testing actors.

Provides a way for actors to expose internal state for testing
without violating encapsulation in production code.
"""

from typing import Any, Dict, List, TypeVar, Generic, Protocol, Optional

T = TypeVar('T')


class ObservableState:
    """
    Container for observable actor state during testing.

    Allows actors to expose snapshots of internal state for verification
    without breaking encapsulation or providing mutable access.
    """

    def __init__(self) -> None:
        self._values: Dict[str, Any] = {}

    def put_value(self, key: str, value: Any) -> 'ObservableState':
        """
        Store a value in the observable state.

        Args:
            key: The key for the value
            value: The value to store

        Returns:
            Self for fluent chaining
        """
        self._values[key] = value
        return self

    def value_of(self, key: str) -> Any:
        """
        Get a value from the observable state.

        Args:
            key: The key to look up

        Returns:
            The value, or None if not found
        """
        return self._values.get(key)

    def value_of_or_default(self, key: str, default: Any) -> Any:
        """
        Get a value with a default fallback.

        Args:
            key: The key to look up
            default: Default value if key not found

        Returns:
            The value or default
        """
        return self._values.get(key, default)

    def has_value(self, key: str) -> bool:
        """
        Check if a value exists.

        Args:
            key: The key to check

        Returns:
            True if the key exists
        """
        return key in self._values

    def size(self) -> int:
        """
        Get the number of stored values.

        Returns:
            Number of values
        """
        return len(self._values)

    def keys(self) -> List[str]:
        """
        Get all keys.

        Returns:
            List of all keys
        """
        return list(self._values.keys())

    def snapshot(self) -> Dict[str, Any]:
        """
        Get a snapshot of all values.

        Returns:
            Dictionary copy of all values
        """
        return dict(self._values)

    def clear(self) -> None:
        """Clear all values."""
        self._values.clear()


class ObservableStateProvider(Protocol):
    """
    Protocol for actors that expose observable state.

    Actors can implement this protocol to provide test-friendly
    state inspection without breaking encapsulation.
    """

    async def observable_state(self) -> ObservableState:
        """
        Get a snapshot of the actor's internal state.

        Returns:
            ObservableState containing state values

        Important: Implementations must return snapshots, not mutable
        references to internal state!
        """
        ...
