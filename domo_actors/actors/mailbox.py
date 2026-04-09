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
Mailbox - FIFO message queue interface for actors.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domo_actors.actors.message import Message


class OverflowPolicy(Enum):
    """Policy for handling mailbox overflow in bounded mailboxes."""

    DROP_OLDEST = "DROP_OLDEST"  # Remove oldest message when full
    DROP_NEWEST = "DROP_NEWEST"  # Reject newest message when full
    REJECT = "REJECT"  # Send to dead letters when full


class Mailbox(ABC):
    """Abstract mailbox interface for message queuing and delivery."""

    @abstractmethod
    def send(self, message: 'Message') -> None:
        """
        Send a message to the mailbox.

        Args:
            message: The message to enqueue
        """
        pass

    @abstractmethod
    def receive(self) -> 'Message':
        """
        Receive the next message from the queue.

        Returns:
            The next message or EmptyMessage if queue is empty
        """
        pass

    @abstractmethod
    async def dispatch(self) -> None:
        """Dispatch messages from the queue asynchronously."""
        pass

    @abstractmethod
    def suspend(self) -> None:
        """Suspend message processing (queue still accepts messages)."""
        pass

    @abstractmethod
    def resume(self) -> None:
        """Resume message processing."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the mailbox (no further message delivery)."""
        pass

    @abstractmethod
    def is_suspended(self) -> bool:
        """Check if the mailbox is suspended."""
        pass

    @abstractmethod
    def is_closed(self) -> bool:
        """Check if the mailbox is closed."""
        pass

    @abstractmethod
    def is_receivable(self) -> bool:
        """Check if there are messages available to receive."""
        pass
