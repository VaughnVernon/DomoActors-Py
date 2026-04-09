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
Stage - Main interface for the actor system.

Get the stage instance via the stage() factory function:
```python
my_stage = stage()
actor = my_stage.actor_for(protocol, definition)
```

The stage is the "world" in which actors live, providing all
necessary infrastructure for actor-based applications.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from domo_actors.actors.protocol import Protocol
    from domo_actors.actors.definition import Definition
    from domo_actors.actors.actor import Actor
    from domo_actors.actors.logger import Logger
    from domo_actors.actors.scheduler import Scheduler
    from domo_actors.actors.dead_letters import DeadLetters
    from domo_actors.actors.supervisor import Supervisor
    from domo_actors.actors.address import Address
    from domo_actors.actors.mailbox import Mailbox

T = TypeVar('T')

# Singleton stage instance (initialized on first call to stage())
_stage_instance: Optional['Stage'] = None


class Stage(ABC):
    """Main interface for the actor system."""

    @abstractmethod
    def actor_for(
        self,
        protocol: 'Protocol',
        definition: 'Definition',
        parent: Optional['Actor'] = None,
        supervisor_name: Optional[str] = None
    ) -> T:
        """
        Create an actor and return its proxy.

        Args:
            protocol: The protocol for actor instantiation
            definition: The definition with constructor parameters
            parent: Optional parent actor (defaults to PublicRootActor)
            supervisor_name: Optional supervisor name

        Returns:
            Proxy implementing the protocol interface
        """
        pass

    @abstractmethod
    def actor_proxy_for(
        self,
        protocol: 'Protocol',
        actor: 'Actor',
        mailbox: 'Mailbox'
    ) -> T:
        """
        Create a proxy for an existing actor.

        Args:
            protocol: The protocol interface
            actor: The actor instance
            mailbox: The actor's mailbox

        Returns:
            Proxy implementing the protocol interface
        """
        pass

    @abstractmethod
    def register_supervisor(self, name: str, supervisor: 'Supervisor') -> None:
        """
        Register a supervisor.

        Args:
            name: Supervisor name
            supervisor: The supervisor instance
        """
        pass

    @abstractmethod
    def get_supervisor(self, name: Optional[str]) -> Optional['Supervisor']:
        """
        Get a supervisor by name.

        Args:
            name: Supervisor name

        Returns:
            The supervisor or None
        """
        pass

    @abstractmethod
    def logger(self) -> 'Logger':
        """
        Get the stage logger.

        Returns:
            The logger instance
        """
        pass

    @abstractmethod
    def scheduler(self) -> 'Scheduler':
        """
        Get the scheduler.

        Returns:
            The scheduler instance
        """
        pass

    @abstractmethod
    def dead_letters(self) -> 'DeadLetters':
        """
        Get the dead letters facility.

        Returns:
            The dead letters handler
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close the stage and stop all actors.

        This stops all actors hierarchically and cleans up resources.
        """
        pass


def stage() -> Stage:
    """
    Returns the default stage instance.

    This is the primary way to access the stage in your application:
    ```python
    my_stage = stage()
    actor = my_stage.actor_for(protocol, definition)
    ```

    The stage and its root actors are fully initialized when this function
    is first called. Subsequent calls return the same singleton instance.

    Returns:
        The default stage instance
    """
    global _stage_instance
    if _stage_instance is None:
        from domo_actors.actors.local_stage import LocalStage
        _stage_instance = LocalStage()
    return _stage_instance
