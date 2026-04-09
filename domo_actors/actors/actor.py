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
Actor - Abstract base class for all actors.

Provides lifecycle management, child actor creation, and self-messaging capabilities.
"""

from abc import ABC
from typing import TypeVar, Any, Optional, TYPE_CHECKING
from domo_actors.actors.life_cycle import LifeCycle
from domo_actors.actors.actor_protocol import ActorProtocol

if TYPE_CHECKING:
    from domo_actors.actors.address import Address
    from domo_actors.actors.definition import Definition
    from domo_actors.actors.environment import Environment
    from domo_actors.actors.logger import Logger
    from domo_actors.actors.stage import Stage
    from domo_actors.actors.protocol import Protocol
    from domo_actors.actors.execution_context import ExecutionContext
    from domo_actors.actors.dead_letters import DeadLetters

T = TypeVar('T')


class Actor(LifeCycle, ActorProtocol, ABC):
    """
    Abstract base class for all actors.

    Actors are the fundamental unit of computation in the actor model.
    They process messages sequentially through their mailbox, maintain
    private state, and can create child actors.
    """

    def __init__(self) -> None:
        """
        Initialize the actor.

        The environment is injected via set_environment() after construction.
        """
        self._environment: Optional['Environment'] = None
        self._stopped: bool = False

    def set_environment(self, environment: 'Environment') -> None:
        """
        Set the actor's environment.

        Args:
            environment: The runtime environment
        """
        self._environment = environment

    # LifeCycle implementation

    def environment(self) -> 'Environment':
        """
        Get the actor's environment.

        Returns:
            The environment

        Raises:
            RuntimeError: If environment not yet set
        """
        if self._environment is None:
            raise RuntimeError("Actor environment not initialized")
        return self._environment

    async def before_start(self) -> None:
        """
        Hook called before the actor starts.

        Override this method to perform initialization.
        """
        pass

    async def start(self) -> None:
        """
        Start the actor.

        Called by the stage after instantiation.
        """
        await self.before_start()

    async def before_restart(self, reason: Exception) -> None:
        """
        Hook called before the actor restarts.

        Override this method to perform cleanup before restart.

        Args:
            reason: The exception that caused the restart
        """
        pass

    async def after_restart(self) -> None:
        """
        Hook called after the actor restarts.

        Override this method to re-initialize state.
        """
        pass

    async def before_resume(self) -> None:
        """
        Hook called before the actor resumes after suspension.

        Override this method to handle resume logic.
        """
        pass

    async def before_stop(self) -> None:
        """
        Hook called before the actor stops.

        Override this method to perform cleanup.
        """
        pass

    async def after_stop(self) -> None:
        """
        Hook called after the actor stops.

        Override this method to perform final cleanup.
        """
        pass

    async def restart(self, reason: Exception) -> None:
        """
        Restart the actor due to a failure.

        Args:
            reason: The exception that caused the restart
        """
        await self.before_restart(reason)
        # Actual restart is handled by supervision system
        await self.after_restart()

    async def stop(self) -> None:
        """Stop the actor."""
        if not self._stopped:
            await self.before_stop()
            self._stopped = True
            self._environment.mailbox().close()
            await self.after_stop()

    def is_stopped(self) -> bool:
        """
        Check if the actor is stopped.

        Returns:
            True if stopped
        """
        return self._stopped

    # ActorProtocol implementation

    def address(self) -> 'Address':
        """
        Get the actor's address.

        Returns:
            The actor's unique address
        """
        return self.environment().address()

    def definition(self) -> 'Definition':
        """
        Get the actor's definition.

        Returns:
            The actor's definition metadata
        """
        return self.environment().definition()

    def type(self) -> str:
        """
        Get the actor type.

        Returns:
            The actor type string
        """
        return self.environment().definition().type()

    def logger(self) -> 'Logger':
        """
        Get the actor's logger.

        Returns:
            The logger instance
        """
        return self.environment().logger()

    def stage(self) -> 'Stage':
        """
        Get the actor stage.

        Returns:
            The actor system stage
        """
        return self.environment().stage()

    def life_cycle(self) -> LifeCycle:
        """
        Get the actor's lifecycle.

        Returns:
            Self as LifeCycle
        """
        return self

    def execution_context(self) -> 'ExecutionContext':
        """
        Get the current execution context.

        Returns:
            The current message execution context
        """
        return self.environment().current_message_execution_context()

    def dead_letters(self) -> 'DeadLetters':
        """
        Get the dead letters facility.

        Returns:
            The dead letters handler
        """
        return self.environment().dead_letters()

    def parent(self) -> Optional['Actor']:
        """
        Get the parent actor.

        Returns:
            The parent actor or None for root actors
        """
        return self.environment().parent()

    def actor(self) -> 'Actor':
        """
        Get the raw actor instance (for internal use).

        Returns:
            Self
        """
        return self

    # Child actor creation

    def child_actor_for(
        self,
        protocol: 'Protocol',
        definition: 'Definition',
        supervisor_name: Optional[str] = None
    ) -> T:
        """
        Create a child actor.

        Args:
            protocol: The protocol for the child actor
            definition: The definition for the child actor
            supervisor_name: Optional supervisor name

        Returns:
            Proxy for the child actor
        """
        from domo_actors.actors.stage_internal import StageInternal

        # Get self as a proxy from the directory
        stage_internal = self.stage()
        if isinstance(stage_internal, StageInternal):
            parent_proxy = stage_internal.directory().get(self.address())
        else:
            parent_proxy = None

        # Create child via stage with parent relationship
        return self.stage().actor_for(
            protocol=protocol,
            definition=definition,
            parent=parent_proxy,
            supervisor_name=supervisor_name
        )

    # Self-messaging

    def self_as(self) -> T:
        """
        Get a proxy to self for self-messaging.

        Returns:
            Proxy that routes messages through the mailbox
        """
        from domo_actors.actors.actor_proxy import create_actor_proxy

        mailbox = self.environment().mailbox()
        return create_actor_proxy(self, mailbox)

    # State snapshot support

    def state_snapshot(self, snapshot: Optional[Any] = None) -> Optional[Any]:
        """
        Store or retrieve a state snapshot.

        This method supports both getter and setter patterns:
        - Call with no arguments to get the current snapshot
        - Call with a snapshot argument to store it

        Override this method to implement state snapshotting.
        Default implementation returns None (no snapshot).

        Args:
            snapshot: Optional snapshot to store

        Returns:
            The current snapshot (when called as getter), or None (when called as setter)

        Example:
            # Subclass implementation:
            def state_snapshot(self, snapshot=None):
                if snapshot is not None:
                    self._my_snapshot = snapshot
                    return None
                return self._my_snapshot
        """
        return None

    # Equality and hashing

    def __eq__(self, other: Any) -> bool:
        """
        Check equality based on address.

        Args:
            other: Object to compare with

        Returns:
            True if addresses are equal
        """
        if not isinstance(other, Actor):
            return False
        try:
            return self.address() == other.address()
        except Exception:
            return False

    def __hash__(self) -> int:
        """
        Get hash based on address.

        Returns:
            Hash of the address
        """
        try:
            return hash(self.address())
        except Exception:
            return id(self)

    def __str__(self) -> str:
        """
        String representation.

        Returns:
            String showing type and address
        """
        try:
            return f"{self.type()}({self.address()})"
        except Exception:
            return f"Actor({id(self)})"

    def __repr__(self) -> str:
        """
        Detailed string representation.

        Returns:
            Detailed string
        """
        return self.__str__()
