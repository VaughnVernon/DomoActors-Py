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
ActorProtocol - Core protocol interface that all actor proxies implement.
"""

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from domo_actors.actors.address import Address
    from domo_actors.actors.definition import Definition
    from domo_actors.actors.logger import Logger
    from domo_actors.actors.stage import Stage
    from domo_actors.actors.life_cycle import LifeCycle
    from domo_actors.actors.execution_context import ExecutionContext
    from domo_actors.actors.dead_letters import DeadLetters


class ActorProtocol(ABC):
    """
    Core protocol interface for all actor proxies.

    Defines operational and lifecycle methods that every actor must support.
    """

    @abstractmethod
    def address(self) -> 'Address':
        """
        Get the actor's unique address.

        Returns:
            The actor's address
        """
        pass

    @abstractmethod
    def definition(self) -> 'Definition':
        """
        Get the actor's definition.

        Returns:
            The actor's definition metadata
        """
        pass

    @abstractmethod
    def type(self) -> str:
        """
        Get the actor type name.

        Returns:
            String identifier for the actor type
        """
        pass

    @abstractmethod
    def logger(self) -> 'Logger':
        """
        Get the actor's logger.

        Returns:
            The logger instance
        """
        pass

    @abstractmethod
    def stage(self) -> 'Stage':
        """
        Get the actor system stage.

        Returns:
            The actor stage
        """
        pass

    @abstractmethod
    def life_cycle(self) -> 'LifeCycle':
        """
        Get the actor's lifecycle.

        Returns:
            The lifecycle interface
        """
        pass

    @abstractmethod
    def execution_context(self) -> 'ExecutionContext':
        """
        Get the current execution context.

        Returns:
            The execution context
        """
        pass

    @abstractmethod
    def is_stopped(self) -> bool:
        """
        Check if the actor is stopped.

        Returns:
            True if the actor is stopped
        """
        pass

    @abstractmethod
    def dead_letters(self) -> 'DeadLetters':
        """
        Get the dead letters facility.

        Returns:
            The dead letters handler
        """
        pass

    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        """Check equality with another actor."""
        pass

    @abstractmethod
    def __hash__(self) -> int:
        """Get hash code for the actor."""
        pass

    @abstractmethod
    def __str__(self) -> str:
        """String representation of the actor."""
        pass
