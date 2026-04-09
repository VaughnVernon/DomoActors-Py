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
Root Actors - System infrastructure actors for the actor hierarchy.
"""

from domo_actors.actors.actor import Actor


class PrivateRootActor(Actor):
    """
    System root actor - supervises PublicRootActor.

    This is the top of the actor hierarchy and handles system-level supervision.
    """

    async def before_start(self) -> None:
        """Initialize the private root actor."""
        self.logger().debug("PrivateRootActor starting")

    async def before_stop(self) -> None:
        """Cleanup before stopping."""
        self.logger().debug("PrivateRootActor stopping")


class PublicRootActor(Actor):
    """
    Default parent for user-created actors.

    This actor serves as the default parent when no explicit parent is specified.
    It is supervised by PrivateRootActor.
    """

    async def before_start(self) -> None:
        """Initialize the public root actor."""
        self.logger().debug("PublicRootActor starting")

    async def before_stop(self) -> None:
        """Cleanup before stopping."""
        self.logger().debug("PublicRootActor stopping")
