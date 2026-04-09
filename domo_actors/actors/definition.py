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
Definition - Metadata bundle for actor instantiation.
"""

from typing import Any, Tuple
from domo_actors.actors.address import Address


class Definition:
    """Encapsulates actor type, address, and constructor parameters."""

    def __init__(self, actor_type: str, address: Address, parameters: Tuple[Any, ...] = ()) -> None:
        """
        Initialize an actor definition.

        Args:
            actor_type: String identifier for the actor type
            address: Unique address for the actor
            parameters: Tuple of constructor parameters
        """
        self._type = actor_type
        self._address = address
        self._parameters = parameters

    def type(self) -> str:
        """
        Get the actor type.

        Returns:
            The actor type string
        """
        return self._type

    def address(self) -> Address:
        """
        Get the actor address.

        Returns:
            The actor's address
        """
        return self._address

    def parameters(self) -> Tuple[Any, ...]:
        """
        Get the constructor parameters.

        Returns:
            Tuple of parameters
        """
        return self._parameters

    def __str__(self) -> str:
        """
        String representation.

        Returns:
            String describing the definition
        """
        return f"Definition(type={self._type}, address={self._address}, parameters={len(self._parameters)})"
