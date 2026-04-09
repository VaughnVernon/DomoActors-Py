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
StageInternal - Internal stage interface with failure handling.
"""

from abc import ABC, abstractmethod
from domo_actors.actors.stage import Stage
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domo_actors.actors.directory import Directory
    from domo_actors.actors.supervised import Supervised


class StageInternal(Stage, ABC):
    """Internal stage interface with additional methods for actor system internals."""

    @abstractmethod
    def directory(self) -> 'Directory':
        """
        Get the actor directory.

        Returns:
            The directory for actor lookup
        """
        pass

    @abstractmethod
    async def handle_failure_of(self, supervised: 'Supervised') -> None:
        """
        Handle a failed actor.

        Args:
            supervised: The supervised actor that failed
        """
        pass
