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
Supervised - Implementation of supervised actor wrapper for stage integration.
"""

from typing import TYPE_CHECKING
import time
from domo_actors.actors.supervisor import Supervised

if TYPE_CHECKING:
    from domo_actors.actors.actor import Actor


class StageSupervisedActor(Supervised):
    """
    Supervised actor wrapper for stage supervision integration.

    Tracks restart history and enforces restart intensity limits.
    """

    def __init__(self, proxy: 'Actor', raw_actor: 'Actor', error: Exception) -> None:
        """
        Initialize supervised actor.

        Args:
            proxy: The actor proxy
            raw_actor: The raw actor instance
            error: The error that caused supervision
        """
        self._proxy = proxy
        self._raw_actor = raw_actor
        self._error = error
        self._restart_times: list[float] = []

    def actor(self) -> 'Actor':
        """
        Get the raw actor instance.

        Returns:
            The raw actor
        """
        return self._raw_actor

    def proxy(self) -> 'Actor':
        """
        Get the actor proxy.

        Returns:
            The proxy
        """
        return self._proxy

    def error(self) -> Exception:
        """
        Get the error that caused supervision.

        Returns:
            The exception
        """
        return self._error

    async def restart_within(self, period: int, intensity: int) -> None:
        """
        Restart the actor within intensity limits.

        Args:
            period: Time window in milliseconds
            intensity: Maximum restarts allowed (-1 for unlimited)

        Raises:
            Exception: If restart intensity exceeded
        """
        current_time = time.time() * 1000  # Convert to milliseconds

        # Add current restart time
        self._restart_times.append(current_time)

        # Check intensity limits (if not unlimited)
        if intensity >= 0:
            # Filter restarts within the period window
            window_start = current_time - period
            recent_restarts = [t for t in self._restart_times if t >= window_start]
            self._restart_times = recent_restarts  # Keep only recent restarts

            if len(recent_restarts) > intensity:
                # Exceeded intensity limit - escalate or stop
                self._raw_actor.logger().error(
                    f"Restart intensity exceeded: {len(recent_restarts)} restarts "
                    f"in {period}ms (limit: {intensity})"
                )
                await self.stop()
                return

        # Perform restart
        await self._raw_actor.restart(self._error)

        # Resume mailbox after restart
        self._raw_actor.life_cycle().environment().mailbox().resume()

    async def stop(self) -> None:
        """Stop the actor."""
        await self._raw_actor.stop()

    async def escalate(self) -> None:
        """Escalate the failure to parent supervisor."""
        parent = self._raw_actor.parent()
        if parent:
            # Create supervised wrapper for parent
            parent_supervised = StageSupervisedActor(parent, parent.actor(), self._error)

            # Get parent's supervisor and inform
            parent_env = parent.life_cycle().environment()
            supervisor = parent_env.supervisor()

            if supervisor:
                await supervisor.inform(self._error, parent_supervised)
            else:
                # No supervisor - log and stop
                self._raw_actor.logger().error(
                    f"No supervisor for parent actor, stopping: {self._error}",
                    self._error
                )
                await parent_supervised.stop()
        else:
            # No parent - this is a root actor, just log the error
            self._raw_actor.logger().error(
                f"Root actor failure escalated: {self._error}",
                self._error
            )
