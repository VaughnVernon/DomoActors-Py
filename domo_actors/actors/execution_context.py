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
Execution Context - Request-scoped context for message processing.

Provides key-value storage that propagates across collaborating actors.
"""

from typing import TypeVar, Generic, Dict, Any, Optional

T = TypeVar('T')


class ExecutionContext:
    """Request-scoped context that can be copied and propagated."""

    def __init__(self, values: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the execution context.

        Args:
            values: Optional dictionary of initial values
        """
        self._values: Dict[str, Any] = values.copy() if values else {}

    def set_value(self, key: str, value: Any) -> 'ExecutionContext':
        """
        Set a value in the context.

        Args:
            key: The key to set
            value: The value to store

        Returns:
            Self for method chaining
        """
        self._values[key] = value
        return self

    def get_value(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """
        Get a value from the context.

        Args:
            key: The key to retrieve
            default: Default value if key not found

        Returns:
            The value or default
        """
        return self._values.get(key, default)

    def has_value(self, key: str) -> bool:
        """
        Check if a key exists in the context.

        Args:
            key: The key to check

        Returns:
            True if the key exists
        """
        return key in self._values

    def copy(self) -> 'ExecutionContext':
        """
        Create a copy of this context.

        Returns:
            A new ExecutionContext with copied values
        """
        return ExecutionContext(self._values)

    def propagate(self) -> None:
        """Propagate context to collaborators (hook for extensions)."""
        pass

    def clear(self) -> None:
        """Clear all values from the context."""
        self._values.clear()

    def __str__(self) -> str:
        """
        String representation.

        Returns:
            String showing the context values
        """
        return f"ExecutionContext({self._values})"


# Singleton empty context
EmptyExecutionContext = ExecutionContext()
