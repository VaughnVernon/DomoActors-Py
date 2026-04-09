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
Supervision - Fault tolerance strategies and supervision directives.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any

# Import Actor for DefaultSupervisor inheritance
from domo_actors.actors.actor import Actor

if TYPE_CHECKING:
    pass  # Actor now imported above


class SupervisionDirective(Enum):
    """Directives for handling actor failures."""

    RESTART = "RESTART"  # Restart the failed actor
    RESUME = "RESUME"    # Resume message processing
    STOP = "STOP"        # Stop the actor
    ESCALATE = "ESCALATE"  # Pass failure to parent supervisor


class SupervisionScope(Enum):
    """Scope of supervision action."""

    ONE = "ONE"  # Only the failed actor
    ALL = "ALL"  # Failed actor and all siblings


class SupervisionStrategy(ABC):
    """Abstract supervision strategy defining failure handling policy."""

    @abstractmethod
    def intensity(self) -> int:
        """
        Get restart intensity limit.

        Returns:
            Maximum number of restarts allowed (-1 for unlimited, 0+ for limit)
        """
        pass

    @abstractmethod
    def period(self) -> int:
        """
        Get the time window for intensity checking.

        Returns:
            Period in milliseconds
        """
        pass

    @abstractmethod
    def scope(self) -> SupervisionScope:
        """
        Get the supervision scope.

        Returns:
            Scope (ONE or ALL)
        """
        pass


class DefaultSupervisionStrategy(SupervisionStrategy):
    """Default supervision strategy: 1 restart per 5 seconds, scope ONE."""

    def intensity(self) -> int:
        """Get restart intensity (1 restart allowed)."""
        return 1

    def period(self) -> int:
        """Get period (5000ms = 5 seconds)."""
        return 5000

    def scope(self) -> SupervisionScope:
        """Get scope (ONE - only failed actor)."""
        return SupervisionScope.ONE


class Supervised(ABC):
    """Interface for supervised actors."""

    @abstractmethod
    def actor(self) -> 'Actor':
        """Get the raw actor instance."""
        pass

    @abstractmethod
    async def restart_within(self, period: int, intensity: int) -> None:
        """
        Restart the actor within intensity limits.

        Args:
            period: Time window in milliseconds
            intensity: Maximum restarts allowed
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the actor."""
        pass

    @abstractmethod
    async def escalate(self) -> None:
        """Escalate the failure to parent supervisor."""
        pass


class Supervisor(ABC):
    """Abstract supervisor interface for fault tolerance."""

    @abstractmethod
    async def inform(self, error: Exception, supervised: Supervised) -> None:
        """
        Inform the supervisor of an actor failure.

        Args:
            error: The exception that caused the failure
            supervised: The supervised actor that failed
        """
        pass

    @abstractmethod
    async def supervision_strategy(self) -> SupervisionStrategy:
        """
        Get the supervision strategy.

        Returns:
            The supervision strategy to apply
        """
        pass


class DefaultSupervisor(Actor, Supervisor, ABC):
    """
    Abstract base class for supervisor actors.

    Implements the supervision protocol with configurable strategies.
    Supervisors are actors that handle failures of other actors.
    """

    async def inform(self, error: Exception, supervised: Supervised) -> None:
        """
        Handle actor failure by applying supervision strategy.

        Args:
            error: The exception that caused the failure
            supervised: The failed actor
        """
        strategy = await self.supervision_strategy()
        directive = self.decide_directive(error, supervised, strategy)

        if directive == SupervisionDirective.RESTART:
            await supervised.restart_within(strategy.period(), strategy.intensity())

        elif directive == SupervisionDirective.RESUME:
            supervised.actor().life_cycle().environment().mailbox().resume()

        elif directive == SupervisionDirective.STOP:
            await supervised.stop()

        elif directive == SupervisionDirective.ESCALATE:
            await supervised.escalate()

    def decide_directive(
        self,
        error: Exception,
        supervised: Supervised,
        strategy: SupervisionStrategy
    ) -> SupervisionDirective:
        """
        Decide which supervision directive to apply.

        Override this method to customize failure handling.

        Args:
            error: The exception that caused the failure
            supervised: The failed actor
            strategy: The supervision strategy

        Returns:
            The directive to apply
        """
        # Default behavior: restart on any error
        return SupervisionDirective.RESTART

    async def supervision_strategy(self) -> SupervisionStrategy:
        """
        Get the supervision strategy.

        Override this method to provide custom strategies.

        Returns:
            The supervision strategy
        """
        return DefaultSupervisionStrategy()
