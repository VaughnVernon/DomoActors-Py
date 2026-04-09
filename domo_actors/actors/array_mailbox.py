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
ArrayMailbox - Unbounded FIFO mailbox implementation.
"""

import asyncio
from collections import deque
from typing import Deque
from domo_actors.actors.mailbox import Mailbox
from domo_actors.actors.message import Message, EmptyMessage


class ArrayMailbox(Mailbox):
    """Unbounded FIFO mailbox using a deque for message storage."""

    def __init__(self) -> None:
        """Initialize an empty mailbox."""
        self._queue: Deque[Message] = deque()
        self._closed: bool = False
        self._suspended: bool = False

    def send(self, message: Message) -> None:
        """
        Send a message to the mailbox.

        Args:
            message: The message to enqueue
        """
        if not self._closed:
            self._queue.append(message)

            # Trigger dispatch if not suspended
            # Note: We don't check _dispatching here because the while loop
            # in dispatch() will handle processing queued messages, even during self-sends
            if not self._suspended:
                asyncio.create_task(self.dispatch())
        else:
            # Mailbox is closed - send to dead letters
            from domo_actors.actors.dead_letters import DeadLetter

            dead_letter = DeadLetter(message.to(), message.representation())
            message.to().stage().dead_letters().failed_delivery(dead_letter)
            message.deferred().resolve(None)  # Resolve with None to indicate actor stopped

    def receive(self) -> Message:
        """
        Receive the next message from the queue.

        Returns:
            The next message or EmptyMessage if queue is empty
        """
        if self._queue:
            return self._queue.popleft()
        return EmptyMessage

    async def dispatch(self) -> None:
        """
        Dispatch messages from the queue using self-draining recursion.

        This algorithm prevents message starvation when concurrent send() calls
        occur during message processing. Uses recursion instead of a loop to
        allow self-sends to be processed correctly.
        """
        # Check if we should stop dispatching
        if self._suspended or self._closed:
            return

        # Receive next message
        message = self.receive()

        # If no message available, exit
        if not message.is_deliverable():
            return

        # Deliver the message
        await message.deliver()

        # Check if there are more messages to process and recursively dispatch
        if self.is_receivable():
            await self.dispatch()

    def suspend(self) -> None:
        """Suspend message processing."""
        self._suspended = True

    def resume(self) -> None:
        """Resume message processing and trigger dispatch."""
        self._suspended = False

        # Trigger dispatch if there are pending messages
        if self.is_receivable():
            asyncio.create_task(self.dispatch())

    def close(self) -> None:
        """Close the mailbox - no further message delivery."""
        self._closed = True

    def is_suspended(self) -> bool:
        """
        Check if the mailbox is suspended.

        Returns:
            True if suspended
        """
        return self._suspended

    def is_closed(self) -> bool:
        """
        Check if the mailbox is closed.

        Returns:
            True if closed
        """
        return self._closed

    def is_receivable(self) -> bool:
        """
        Check if there are messages available to receive.

        Returns:
            True if queue has messages
        """
        return len(self._queue) > 0

    def size(self) -> int:
        """
        Get the current queue size.

        Returns:
            Number of messages in the queue
        """
        return len(self._queue)

    def __str__(self) -> str:
        """String representation."""
        return f"ArrayMailbox(size={len(self._queue)}, suspended={self._suspended}, closed={self._closed})"
