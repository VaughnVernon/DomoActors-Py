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
LifeCycle - Actor lifecycle management interface and base class.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domo_actors.actors.environment import Environment


class LifeCycle(ABC):
    """Abstract lifecycle interface for actors."""

    @abstractmethod
    async def before_start(self) -> None:
        """Hook called before the actor starts."""
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start the actor."""
        pass

    @abstractmethod
    async def before_restart(self, reason: Exception) -> None:
        """Hook called before the actor restarts."""
        pass

    @abstractmethod
    async def after_restart(self) -> None:
        """Hook called after the actor restarts."""
        pass

    @abstractmethod
    async def before_resume(self) -> None:
        """Hook called before the actor resumes after suspension."""
        pass

    @abstractmethod
    async def before_stop(self) -> None:
        """Hook called before the actor stops."""
        pass

    @abstractmethod
    async def after_stop(self) -> None:
        """Hook called after the actor stops."""
        pass

    @abstractmethod
    async def restart(self, reason: Exception) -> None:
        """Restart the actor due to a failure."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the actor."""
        pass

    @abstractmethod
    def is_stopped(self) -> bool:
        """Check if the actor is stopped."""
        pass

    @abstractmethod
    def environment(self) -> 'Environment':
        """Get the actor's environment."""
        pass
