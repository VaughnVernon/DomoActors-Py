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
Dead Letters - Central facility for handling undeliverable messages.
"""

from typing import List, TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from domo_actors.actors.actor import Actor


class DeadLettersListener(Protocol):
    """Listener interface for dead letter events."""

    def handle(self, dead_letter: 'DeadLetter') -> None:
        """
        Handle a dead letter.

        Args:
            dead_letter: The undeliverable message information
        """
        pass


class DeadLetter:
    """Represents an undeliverable message."""

    def __init__(self, actor_protocol: 'Actor', representation: str) -> None:
        """
        Initialize a dead letter.

        Args:
            actor_protocol: The target actor that couldn't receive the message
            representation: String representation of the message
        """
        self._actor_protocol = actor_protocol
        self._representation = representation

    def actor_protocol(self) -> 'Actor':
        """Get the target actor."""
        return self._actor_protocol

    def representation(self) -> str:
        """Get the message representation."""
        return self._representation

    def __str__(self) -> str:
        """String representation."""
        address = self._actor_protocol.address() if hasattr(self._actor_protocol, 'address') else 'unknown'
        return f"DeadLetter: {self._representation} to {address}"


class DeadLetters:
    """Central dead letters facility for the actor system."""

    def __init__(self) -> None:
        """Initialize the dead letters facility."""
        self._listeners: List[DeadLettersListener] = []

    def failed_delivery(self, dead_letter: DeadLetter) -> None:
        """
        Handle a failed message delivery.

        Args:
            dead_letter: The dead letter to process
        """
        # Log the dead letter
        logger = dead_letter.actor_protocol().logger()
        logger.error(str(dead_letter))

        # Notify all listeners with error protection
        for listener in self._listeners:
            try:
                listener.handle(dead_letter)
            except Exception as error:
                logger.error(f"DeadLetter: Listener crashed: {str(error)}", error)

    def register_listener(self, listener: DeadLettersListener) -> None:
        """
        Register a dead letters listener.

        Args:
            listener: The listener to register
        """
        if listener not in self._listeners:
            self._listeners.append(listener)

    def unregister_listener(self, listener: DeadLettersListener) -> None:
        """
        Unregister a dead letters listener.

        Args:
            listener: The listener to unregister
        """
        if listener in self._listeners:
            self._listeners.remove(listener)

    def __str__(self) -> str:
        """String representation."""
        return f"DeadLetters(listeners={len(self._listeners)})"
