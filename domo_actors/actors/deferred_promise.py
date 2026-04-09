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
Deferred Promise - A promise that can be resolved or rejected externally.

This bridges the synchronous proxy call with asynchronous message delivery.
"""

import asyncio
from typing import TypeVar, Generic

T = TypeVar('T')


class DeferredPromise(Generic[T]):
    """A promise that can be resolved or rejected from outside the async context."""

    def __init__(self) -> None:
        """Initialize the deferred promise with a new Future."""
        self._future: asyncio.Future[T] = asyncio.Future()

    def resolve(self, value: T) -> None:
        """
        Resolve the promise with a value.

        Args:
            value: The value to resolve with
        """
        if not self._future.done():
            self._future.set_result(value)

    def reject(self, error: Exception) -> None:
        """
        Reject the promise with an error.

        Args:
            error: The exception to reject with
        """
        if not self._future.done():
            self._future.set_exception(error)

    @property
    def future(self) -> asyncio.Future[T]:
        """
        Get the underlying Future object.

        Returns:
            The asyncio Future
        """
        return self._future

    def __await__(self):
        """Make the DeferredPromise awaitable."""
        return self._future.__await__()
