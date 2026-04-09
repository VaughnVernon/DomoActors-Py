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
Test await utilities for polling async assertions.

Provides helpers for waiting on actor state changes in tests.
"""

import asyncio
from typing import Callable, Any, TypeVar, Awaitable, Optional, Dict

T = TypeVar('T')


async def await_assert(
    assertion: Callable[[], Awaitable[None]],
    timeout: float = 2.0,
    interval: float = 0.05
) -> None:
    """
    Retry an async assertion until it passes or timeout.

    Args:
        assertion: Async function that performs assertions
        timeout: Maximum time to wait in seconds
        interval: Polling interval in seconds

    Raises:
        AssertionError: If assertion fails after timeout
        asyncio.TimeoutError: If timeout is reached
    """
    start_time = asyncio.get_event_loop().time()
    last_error = None

    while True:
        try:
            await assertion()
            return  # Assertion passed
        except AssertionError as e:
            last_error = e

        # Check timeout
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed >= timeout:
            if last_error:
                raise last_error
            raise asyncio.TimeoutError(f"Assertion did not pass within {timeout}s")

        # Wait before retrying
        await asyncio.sleep(interval)


async def await_observable_state(
    actor: Any,
    condition: Callable[[Any], bool],
    options: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Wait for an observable state condition to be satisfied.

    Args:
        actor: The actor to monitor (must have observable_state method)
        condition: Function that checks state and returns True when satisfied
        options: Options dict with 'timeout' (default 2.0) and 'interval' (default 0.05)

    Returns:
        The ObservableState when condition is satisfied

    Raises:
        asyncio.TimeoutError: If condition not satisfied within timeout
        AttributeError: If actor doesn't have observable_state method
    """
    if options is None:
        options = {}

    timeout = options.get('timeout', 2.0)
    interval = options.get('interval', 0.05)

    if not hasattr(actor, 'observable_state'):
        raise AttributeError(f"Actor does not have observable_state method")

    start_time = asyncio.get_event_loop().time()
    last_state = None

    while True:
        state = await actor.observable_state()
        last_state = state

        if condition(state):
            return state

        # Check timeout
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed >= timeout:
            raise asyncio.TimeoutError(
                f"State condition not satisfied within {int(timeout * 1000)}ms"
            )

        # Wait before retrying
        await asyncio.sleep(interval)


async def await_state_value(
    actor: Any,
    state_key: str,
    expected_value: Any,
    options: Optional[Dict[str, Any]] = None
) -> None:
    """
    Wait for an actor's state value to equal an expected value.

    Args:
        actor: The actor to monitor
        state_key: The state key to check
        expected_value: The expected value
        options: Options dict with 'timeout' (default 2.0) and 'interval' (default 0.05)

    Raises:
        asyncio.TimeoutError: If value doesn't match within timeout
    """
    if options is None:
        options = {}

    timeout = options.get('timeout', 2.0)
    interval = options.get('interval', 0.05)

    async def check_value():
        if hasattr(actor, 'observable_state'):
            state = await actor.observable_state()
            actual = state.value_of(state_key)
        else:
            # Try to get value directly
            actual = getattr(actor, state_key, None)

        assert actual == expected_value, f"Expected {state_key}={expected_value}, got {actual}"

    await await_assert(check_value, timeout=timeout, interval=interval)
