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
Protocol - Factory interface for actor instantiation.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domo_actors.actors.actor import Actor
    from domo_actors.actors.definition import Definition


class ProtocolInstantiator(ABC):
    """Factory interface for creating actor instances."""

    @abstractmethod
    def instantiate(self, definition: 'Definition') -> 'Actor':
        """
        Create an actor instance from a definition.

        Args:
            definition: The actor definition with parameters

        Returns:
            A new actor instance
        """
        pass


class Protocol(ABC):
    """Protocol interface defining actor type and instantiation."""

    @abstractmethod
    def type(self) -> str:
        """
        Get the protocol type name.

        Returns:
            String identifier for the protocol
        """
        pass

    @abstractmethod
    def instantiator(self) -> ProtocolInstantiator:
        """
        Get the protocol instantiator.

        Returns:
            A ProtocolInstantiator for creating actors
        """
        pass
