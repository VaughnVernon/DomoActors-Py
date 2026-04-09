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
BoundedMailbox - Capacity-limited FIFO mailbox with overflow policies.
"""

import asyncio
from collections import deque
from typing import Deque
from domo_actors.actors.mailbox import Mailbox, OverflowPolicy
from domo_actors.actors.message import Message, EmptyMessage


class BoundedMailbox(Mailbox):
    """Bounded FIFO mailbox with configurable overflow handling."""

    def __init__(self, capacity: int, overflow_policy: OverflowPolicy = OverflowPolicy.DROP_OLDEST) -> None:
        """
        Initialize a bounded mailbox.

        Args:
            capacity: Maximum number of messages the mailbox can hold
            overflow_policy: Policy for handling overflow (default: DROP_OLDEST)
        """
        self._queue: Deque[Message] = deque()
        self._capacity = capacity
        self._overflow_policy = overflow_policy
        self._closed: bool = False
        self._suspended: bool = False
        self._dropped_message_count: int = 0

    def send(self, message: Message) -> None:
        """
        Send a message to the mailbox with overflow handling.

        Args:
            message: The message to enqueue
        """
        if self._closed:
            # Mailbox is closed - send to dead letters
            from domo_actors.actors.dead_letters import DeadLetter

            dead_letter = DeadLetter(message.to(), message.representation())
            message.to().stage().dead_letters().failed_delivery(dead_letter)
            message.deferred().resolve(None)  # Resolve to indicate actor stopped
            return

        # Check if mailbox is full
        if len(self._queue) >= self._capacity:
            self._handle_overflow(message)
        else:
            self._queue.append(message)

            # Trigger dispatch if not suspended
            # Note: We don't check _dispatching here because the recursive dispatch
            # will handle processing queued messages, even during self-sends
            if not self._suspended:
                asyncio.create_task(self.dispatch())

    def _handle_overflow(self, new_message: Message) -> None:
        """
        Handle mailbox overflow according to the configured policy.

        Args:
            new_message: The new message attempting to be added
        """
        if self._overflow_policy == OverflowPolicy.DROP_OLDEST:
            # Remove oldest message and add new one
            if self._queue:
                dropped = self._queue.popleft()
                self._notify_dropped(dropped)
                self._queue.append(new_message)
            else:
                # Queue is somehow empty, just add the message
                self._queue.append(new_message)

        elif self._overflow_policy == OverflowPolicy.DROP_NEWEST:
            # Reject the incoming message
            self._notify_dropped(new_message)

        elif self._overflow_policy == OverflowPolicy.REJECT:
            # Send to dead letters
            from domo_actors.actors.dead_letters import DeadLetter

            dead_letter = DeadLetter(new_message.to(), new_message.representation())
            new_message.to().stage().dead_letters().failed_delivery(dead_letter)
            new_message.deferred().resolve(None)  # Resolve to indicate mailbox full
            self._dropped_message_count += 1

    def _notify_dropped(self, message: Message) -> None:
        """
        Notify that a message was dropped.

        Args:
            message: The dropped message
        """
        self._dropped_message_count += 1
        # Resolve the promise to indicate the message was dropped
        message.deferred().resolve(None)

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
        """Close the mailbox."""
        self._closed = True

    def is_suspended(self) -> bool:
        """Check if the mailbox is suspended."""
        return self._suspended

    def is_closed(self) -> bool:
        """Check if the mailbox is closed."""
        return self._closed

    def is_receivable(self) -> bool:
        """Check if there are messages available."""
        return len(self._queue) > 0

    def is_full(self) -> bool:
        """
        Check if the mailbox is at capacity.

        Returns:
            True if mailbox is full
        """
        return len(self._queue) >= self._capacity

    def size(self) -> int:
        """
        Get the current queue size.

        Returns:
            Number of messages in the queue
        """
        return len(self._queue)

    def capacity(self) -> int:
        """
        Get the mailbox capacity.

        Returns:
            Maximum capacity
        """
        return self._capacity

    def dropped_message_count(self) -> int:
        """
        Get the count of dropped messages.

        Returns:
            Total number of messages dropped due to overflow
        """
        return self._dropped_message_count

    def __str__(self) -> str:
        """String representation."""
        return (f"BoundedMailbox(size={len(self._queue)}, capacity={self._capacity}, "
                f"policy={self._overflow_policy.value}, dropped={self._dropped_message_count})")
