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
Scheduler - Task scheduling interface for the actor system.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Callable, Any, Dict, Generic, TypeVar, Optional
from datetime import timedelta

T = TypeVar('T')


class Cancellable(ABC):
    """Interface for cancellable scheduled tasks."""

    @abstractmethod
    def cancel(self) -> bool:
        """
        Cancel the scheduled task.

        Returns:
            True if cancelled successfully
        """
        pass


class Scheduled(ABC, Generic[T]):
    """Interface for scheduled task results."""

    @abstractmethod
    def cancel(self) -> bool:
        """Cancel the scheduled task."""
        pass

    @abstractmethod
    async def result(self) -> T:
        """
        Get the result of the scheduled task.

        Returns:
            The task result
        """
        pass


class Scheduler(ABC):
    """Abstract scheduler interface for task scheduling."""

    @abstractmethod
    def schedule_once(
        self,
        delay: timedelta,
        action: Callable[[], Any]
    ) -> Cancellable:
        """
        Schedule an action to run once after a delay.

        Args:
            delay: Delay before execution
            action: Function to execute

        Returns:
            Cancellable handle
        """
        pass

    @abstractmethod
    def schedule_repeat(
        self,
        initial_delay: timedelta,
        interval: timedelta,
        action: Callable[[], Any]
    ) -> Cancellable:
        """
        Schedule an action to run repeatedly.

        Args:
            initial_delay: Initial delay before first execution
            interval: Interval between executions
            action: Function to execute

        Returns:
            Cancellable handle
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the scheduler and cancel all tasks."""
        pass


class DefaultScheduler(Scheduler):
    """Default scheduler implementation using asyncio."""

    def __init__(self) -> None:
        """Initialize the scheduler."""
        self._tasks: Dict[int, asyncio.Task] = {}
        self._next_id: int = 0

    def schedule_once(
        self,
        delay: timedelta,
        action: Callable[[], Any]
    ) -> Cancellable:
        """
        Schedule an action to run once after a delay.

        Args:
            delay: Delay before execution
            action: Function to execute

        Returns:
            Cancellable handle
        """
        task_id = self._next_id
        self._next_id += 1

        async def run_once():
            try:
                await asyncio.sleep(delay.total_seconds())
                result = action()
                if hasattr(result, '__await__'):
                    await result
            finally:
                # Clean up task from registry
                if task_id in self._tasks:
                    del self._tasks[task_id]

        task = asyncio.create_task(run_once())
        self._tasks[task_id] = task

        return TaskCancellable(task)

    def schedule_repeat(
        self,
        initial_delay: timedelta,
        interval: timedelta,
        action: Callable[[], Any]
    ) -> Cancellable:
        """
        Schedule an action to run repeatedly.

        Args:
            initial_delay: Initial delay before first execution
            interval: Interval between executions
            action: Function to execute

        Returns:
            Cancellable handle
        """
        task_id = self._next_id
        self._next_id += 1

        async def run_repeatedly():
            try:
                # Initial delay
                await asyncio.sleep(initial_delay.total_seconds())

                # Repeat until cancelled
                while True:
                    result = action()
                    if hasattr(result, '__await__'):
                        await result

                    await asyncio.sleep(interval.total_seconds())
            except asyncio.CancelledError:
                # Task was cancelled, exit gracefully
                pass
            finally:
                # Clean up task from registry
                if task_id in self._tasks:
                    del self._tasks[task_id]

        task = asyncio.create_task(run_repeatedly())
        self._tasks[task_id] = task

        return TaskCancellable(task)

    def close(self) -> None:
        """Cancel all scheduled tasks."""
        for task in self._tasks.values():
            if not task.done():
                task.cancel()
        self._tasks.clear()


class TaskCancellable(Cancellable):
    """Cancellable wrapper for asyncio tasks."""

    def __init__(self, task: asyncio.Task) -> None:
        """
        Initialize the cancellable.

        Args:
            task: The asyncio task to wrap
        """
        self._task = task

    def cancel(self) -> bool:
        """
        Cancel the task.

        Returns:
            True if cancelled
        """
        if not self._task.done():
            self._task.cancel()
            return True
        return False


class TaskScheduled(Scheduled[T]):
    """Scheduled wrapper for asyncio tasks."""

    def __init__(self, task: asyncio.Task) -> None:
        """
        Initialize the scheduled task.

        Args:
            task: The asyncio task to wrap
        """
        self._task = task

    def cancel(self) -> bool:
        """Cancel the task."""
        if not self._task.done():
            self._task.cancel()
            return True
        return False

    async def result(self) -> T:
        """Get the task result."""
        return await self._task
