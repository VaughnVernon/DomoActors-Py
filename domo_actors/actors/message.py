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
Message - Represents a deferred execution unit in the actor system.
"""

from abc import ABC, abstractmethod
from typing import Callable, Any, TYPE_CHECKING
from domo_actors.actors.deferred_promise import DeferredPromise
from domo_actors.actors.execution_context import ExecutionContext, EmptyExecutionContext

if TYPE_CHECKING:
    from domo_actors.actors.actor import Actor


class Message(ABC):
    """Abstract base class for messages."""

    @abstractmethod
    async def deliver(self) -> 'Message':
        """
        Deliver the message to the target actor.

        Returns:
            EmptyMessage if successfully delivered
        """
        pass

    @abstractmethod
    def to(self) -> 'Actor':
        """
        Get the target actor.

        Returns:
            The actor this message is addressed to
        """
        pass

    @abstractmethod
    def function(self) -> Callable[['Actor'], Any]:
        """
        Get the function to execute.

        Returns:
            The lambda function to execute on the actor
        """
        pass

    @abstractmethod
    def deferred(self) -> DeferredPromise:
        """
        Get the deferred promise.

        Returns:
            The promise to resolve/reject
        """
        pass

    @abstractmethod
    def representation(self) -> str:
        """
        Get a string representation of the message.

        Returns:
            Debug string for the message
        """
        pass

    @abstractmethod
    def execution_context(self) -> ExecutionContext:
        """
        Get the execution context for this message.

        Returns:
            The execution context
        """
        pass

    @abstractmethod
    def is_deliverable(self) -> bool:
        """
        Check if the message can be delivered.

        Returns:
            True if deliverable, False if it's EmptyMessage
        """
        pass


class LocalMessage(Message):
    """Concrete message implementation for local actor communication."""

    def __init__(
        self,
        actor: 'Actor',
        func: Callable[['Actor'], Any],
        deferred_promise: DeferredPromise,
        representation: str,
        exec_context: ExecutionContext | None = None
    ) -> None:
        """
        Initialize a local message.

        Args:
            actor: Target actor
            func: Lambda function to execute on the actor
            deferred_promise: Promise to resolve/reject with result
            representation: Debug string representation
            exec_context: Optional execution context (defaults to empty)
        """
        self._to = actor
        self._function = func
        self._deferred = deferred_promise
        self._representation = representation
        self._execution_context = exec_context if exec_context is not None else EmptyExecutionContext.copy()

    async def deliver(self) -> Message:
        """
        Deliver the message by executing the function on the target actor.

        Returns:
            EmptyMessage if successful

        Handles errors by:
        1. Rejecting the deferred promise
        2. Suspending the actor's mailbox
        3. Routing to the supervision system
        """
        from domo_actors.actors.actor import Actor
        from domo_actors.actors.dead_letters import DeadLetter

        actor = self._to

        # Check if actor is stopped
        if actor.life_cycle().is_stopped():
            dead_letter = DeadLetter(actor, self._representation)
            actor.dead_letters().failed_delivery(dead_letter)
            return EmptyMessage

        # Set execution context for message processing
        environment = actor.life_cycle().environment()
        environment.set_current_message_execution_context(self._execution_context)
        self._execution_context.propagate()

        try:
            # Execute the message function
            result = self._function(actor)

            # If result is a coroutine, await it
            if hasattr(result, '__await__'):
                result = await result

            # Resolve the promise with the result
            self._deferred.resolve(result)
            return EmptyMessage

        except Exception as error:
            # Log the error
            actor.logger().error(f"Message processing failed: {str(error)}", error)

            # Reject the caller's promise
            self._deferred.reject(error)

            # Suspend mailbox to stop further message processing
            environment.mailbox().suspend()

            # Route to supervision system
            from domo_actors.actors.stage_internal import StageInternal
            stage = actor.stage()
            if isinstance(stage, StageInternal):
                from domo_actors.actors.supervised import StageSupervisedActor
                supervised = StageSupervisedActor(self._to, actor.actor(), error)
                await stage.handle_failure_of(supervised)

            return EmptyMessage

        finally:
            # Clear execution context
            environment.set_current_message_execution_context(EmptyExecutionContext)

    def to(self) -> 'Actor':
        """Get the target actor."""
        return self._to

    def function(self) -> Callable[['Actor'], Any]:
        """Get the function to execute."""
        return self._function

    def deferred(self) -> DeferredPromise:
        """Get the deferred promise."""
        return self._deferred

    def representation(self) -> str:
        """Get the string representation."""
        return self._representation

    def execution_context(self) -> ExecutionContext:
        """Get the execution context."""
        return self._execution_context

    def is_deliverable(self) -> bool:
        """Check if deliverable (always True for LocalMessage)."""
        return True


class _EmptyMessage(Message):
    """Sentinel message indicating no message is available."""

    def __init__(self) -> None:
        """Initialize the empty message."""
        pass

    async def deliver(self) -> Message:
        """Empty message cannot be delivered."""
        return self

    def to(self) -> 'Actor':
        """Empty message has no target."""
        raise RuntimeError("EmptyMessage has no target")

    def function(self) -> Callable[['Actor'], Any]:
        """Empty message has no function."""
        raise RuntimeError("EmptyMessage has no function")

    def deferred(self) -> DeferredPromise:
        """Empty message has no deferred promise."""
        raise RuntimeError("EmptyMessage has no deferred promise")

    def representation(self) -> str:
        """String representation."""
        return "EmptyMessage"

    def execution_context(self) -> ExecutionContext:
        """Empty message has empty execution context."""
        return EmptyExecutionContext

    def is_deliverable(self) -> bool:
        """Empty message is not deliverable."""
        return False


# Singleton empty message
EmptyMessage: Message = _EmptyMessage()
