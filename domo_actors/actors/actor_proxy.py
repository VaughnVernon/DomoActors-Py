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
Actor Proxy - Dynamic proxy for type-safe actor communication.

This module implements a dynamic proxy pattern using Python's __getattr__ magic method
to convert protocol method calls into asynchronous messages, similar to the TypeScript
implementation using ES6 Proxy API.
"""

from typing import TypeVar, Any, Callable, Set
import inspect
from domo_actors.actors.deferred_promise import DeferredPromise
from domo_actors.actors.message import LocalMessage
from domo_actors.actors.execution_context import EmptyExecutionContext

# Symbol for internal access to the actor's environment
INTERNAL_ENVIRONMENT_ACCESS = "__internal_environment_access__"

# Synchronous methods that should be executed directly without message queueing
SYNCHRONOUS_ACTOR_METHODS: Set[str] = {
    "address",
    "definition",
    "type",
    "logger",
    "stage",
    "life_cycle",
    "execution_context",
    "is_stopped",
    "equals",
    "__eq__",
    "__hash__",
    "__str__",
    "__repr__",
}

T = TypeVar('T')


class ActorProxy:
    """
    Dynamic proxy that intercepts method calls and converts them to messages.

    This class uses Python's __getattr__ to intercept attribute access and
    create message-based method calls for actor communication.
    """

    def __init__(self, actor: Any, mailbox: Any) -> None:
        """
        Initialize the actor proxy.

        Args:
            actor: The target actor instance
            mailbox: The mailbox for message delivery
        """
        # Use object.__setattr__ to avoid triggering __setattr__ override
        object.__setattr__(self, '_actor', actor)
        object.__setattr__(self, '_mailbox', mailbox)

    def __getattr__(self, name: str) -> Any:
        """
        Intercept attribute access to implement dynamic proxy behavior.

        Args:
            name: The attribute/method name being accessed

        Returns:
            Either the attribute value (for synchronous methods) or a message-wrapped
            callable (for asynchronous methods)
        """
        actor = object.__getattribute__(self, '_actor')
        mailbox = object.__getattribute__(self, '_mailbox')

        # Handle internal environment access
        if name == INTERNAL_ENVIRONMENT_ACCESS:
            return actor.life_cycle().environment()

        # Ignore special Python attributes and private attributes
        if name.startswith('_') or name.startswith('__'):
            # For special methods like __await__, return None to prevent
            # the proxy from being mistaken for a coroutine or thenable
            return None

        # Handle synchronous fast-path methods
        if name in SYNCHRONOUS_ACTOR_METHODS:
            attr = getattr(actor, name, None)
            if callable(attr):
                # Return bound method
                return attr
            else:
                # Return attribute value
                return attr

        # Check if the attribute exists and is callable
        attr = getattr(actor, name, None)

        if attr is None:
            raise AttributeError(f"'{type(actor).__name__}' object has no attribute '{name}'")

        if not callable(attr):
            # For non-callable attributes, return them directly
            return attr

        # For all other methods, create an asynchronous message-based wrapper
        def message_wrapper(*args, **kwargs) -> DeferredPromise:
            """
            Wrapper function that creates a message for the method call.

            Args:
                *args: Positional arguments for the method
                **kwargs: Keyword arguments for the method

            Returns:
                A DeferredPromise that will be resolved when the message is processed
            """
            # Create a deferred promise immediately
            deferred = DeferredPromise()

            # Get current execution context or use empty one
            try:
                current_context = actor.execution_context()
            except Exception:
                current_context = EmptyExecutionContext

            # Copy execution context for message isolation
            message_context = current_context.copy()

            # Create lambda function that will execute on the actor
            def execute_on_actor(actor_instance: Any) -> Any:
                """Execute the method on the actor instance."""
                method = getattr(actor_instance, name)
                return method(*args, **kwargs)

            # Create string representation for debugging
            args_repr = ', '.join([repr(arg) for arg in args])
            if kwargs:
                kwargs_repr = ', '.join([f"{k}={repr(v)}" for k, v in kwargs.items()])
                if args_repr:
                    full_repr = f"{name}({args_repr}, {kwargs_repr})"
                else:
                    full_repr = f"{name}({kwargs_repr})"
            else:
                full_repr = f"{name}({args_repr})"

            # Create the message
            message = LocalMessage(
                actor=actor,
                func=execute_on_actor,
                deferred_promise=deferred,
                representation=full_repr,
                exec_context=message_context
            )

            # Send message to mailbox (non-blocking)
            mailbox.send(message)

            # Return the promise immediately (caller can await it)
            return deferred

        return message_wrapper

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Prevent attribute setting on the proxy.

        Args:
            name: Attribute name
            value: Value to set

        Raises:
            AttributeError: Always, as proxies are immutable
        """
        if name in ('_actor', '_mailbox'):
            object.__setattr__(self, name, value)
        else:
            raise AttributeError(f"Cannot set attribute '{name}' on ActorProxy")

    def __repr__(self) -> str:
        """
        String representation of the proxy.

        Returns:
            String representation
        """
        actor = object.__getattribute__(self, '_actor')
        return f"ActorProxy({actor})"


def create_actor_proxy(actor: Any, mailbox: Any) -> Any:
    """
    Create a dynamic proxy for an actor.

    Args:
        actor: The actor instance to proxy
        mailbox: The mailbox for message delivery

    Returns:
        An ActorProxy instance that can be used as the protocol interface
    """
    return ActorProxy(actor, mailbox)
