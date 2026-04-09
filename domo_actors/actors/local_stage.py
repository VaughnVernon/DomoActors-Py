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
LocalStage - Default implementation of the actor system stage.
"""

import asyncio
from typing import TypeVar, Optional, Dict, Set, TYPE_CHECKING
from domo_actors.actors.stage_internal import StageInternal
from domo_actors.actors.directory import Directory, DirectoryConfigs
from domo_actors.actors.logger import Logger, DefaultLogger
from domo_actors.actors.scheduler import Scheduler, DefaultScheduler
from domo_actors.actors.dead_letters import DeadLetters
from domo_actors.actors.environment import Environment
from domo_actors.actors.array_mailbox import ArrayMailbox
from domo_actors.actors.actor_proxy import create_actor_proxy

if TYPE_CHECKING:
    from domo_actors.actors.protocol import Protocol
    from domo_actors.actors.definition import Definition
    from domo_actors.actors.actor import Actor
    from domo_actors.actors.supervisor import Supervisor
    from domo_actors.actors.mailbox import Mailbox
    from domo_actors.actors.supervised import Supervised

T = TypeVar('T')


class LocalStage(StageInternal):
    """
    Default stage implementation for local actor systems.

    Manages actor lifecycle, supervision, and provides the runtime environment.
    """

    def __init__(
        self,
        logger: Logger = DefaultLogger,
        directory_config: 'DirectoryConfigs' = DirectoryConfigs.DEFAULT
    ) -> None:
        """
        Initialize the local stage.

        Args:
            logger: Logger instance (default: DefaultLogger)
            directory_config: Directory configuration (default: DEFAULT)
        """
        self._dead_letters = DeadLetters()
        self._logger = logger
        self._scheduler = DefaultScheduler()
        self._supervisors: Dict[str, 'Supervisor'] = {}
        self._directory = Directory(directory_config)
        self._private_root_actor: Optional['Actor'] = None
        self._public_root_actor: Optional['Actor'] = None
        self._application_parents: Set['Actor'] = set()

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
        # Ensure root actors are initialized
        self._ensure_root_actors()

        # Use PublicRootActor as default parent if none specified
        if parent is None:
            parent = self._public_root_actor

        # Create mailbox
        mailbox = ArrayMailbox()

        # Get supervisor
        supervisor = self.get_supervisor(supervisor_name)

        # Create environment
        environment = Environment(
            address=definition.address(),
            definition=definition,
            mailbox=mailbox,
            parent=parent,
            stage=self,
            logger=self._logger,
            supervisor=supervisor
        )

        # Instantiate actor
        instantiator = protocol.instantiator()
        actor = instantiator.instantiate(definition)

        # Inject environment
        actor.set_environment(environment)

        # Create proxy
        proxy = create_actor_proxy(actor, mailbox)

        # Register in directory
        self._directory.register(definition.address(), proxy)

        # Track application parents (actors without a parent, except root actors)
        if parent == self._public_root_actor and actor not in (self._private_root_actor, self._public_root_actor):
            self._application_parents.add(proxy)

        # Start the actor
        asyncio.create_task(actor.start())

        return proxy

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
        return create_actor_proxy(actor, mailbox)

    def register_supervisor(self, name: str, supervisor: 'Supervisor') -> None:
        """
        Register a supervisor.

        Args:
            name: Supervisor name
            supervisor: The supervisor instance
        """
        self._supervisors[name] = supervisor

    def get_supervisor(self, name: Optional[str]) -> Optional['Supervisor']:
        """
        Get a supervisor by name.

        Args:
            name: Supervisor name

        Returns:
            The supervisor or None
        """
        if name is None:
            return None
        return self._supervisors.get(name)

    def logger(self) -> Logger:
        """Get the stage logger."""
        return self._logger

    def scheduler(self) -> Scheduler:
        """Get the scheduler."""
        return self._scheduler

    def dead_letters(self) -> DeadLetters:
        """Get the dead letters facility."""
        return self._dead_letters

    def directory(self) -> Directory:
        """Get the actor directory."""
        return self._directory

    async def handle_failure_of(self, supervised: 'Supervised') -> None:
        """
        Handle a failed actor by routing to its supervisor.

        Args:
            supervised: The supervised actor that failed
        """
        actor = supervised.actor()
        environment = actor.life_cycle().environment()
        supervisor = environment.supervisor()

        if supervisor:
            # Send message to supervisor actor instead of calling directly
            await supervisor.inform(supervised.error(), supervised)
        else:
            # No supervisor - log and stop the actor
            self._logger.error(
                f"No supervisor for actor {actor.address()}, stopping",
                supervised.error()
            )
            await supervised.stop()

    async def close(self) -> None:
        """
        Close the stage and stop all actors hierarchically.
        """
        # Stop application-created parent actors (which stops their children)
        for parent in self._application_parents:
            try:
                await parent.stop()
            except Exception as e:
                self._logger.error(f"Error stopping parent actor: {e}", e)

        # Stop supervisor actors
        for supervisor in self._supervisors.values():
            if hasattr(supervisor, 'stop'):
                try:
                    await supervisor.stop()
                except Exception as e:
                    self._logger.error(f"Error stopping supervisor: {e}", e)

        # Stop root actors
        if self._public_root_actor:
            try:
                await self._public_root_actor.stop()
            except Exception as e:
                self._logger.error(f"Error stopping PublicRootActor: {e}", e)

        if self._private_root_actor:
            try:
                await self._private_root_actor.stop()
            except Exception as e:
                self._logger.error(f"Error stopping PrivateRootActor: {e}", e)

        # Close scheduler
        self._scheduler.close()

    def _ensure_root_actors(self) -> None:
        """Ensure root actors are initialized (lazy initialization)."""
        if self._private_root_actor is None:
            self._init_root_actors()

    def _init_root_actors(self) -> None:
        """Initialize the root actor hierarchy."""
        from domo_actors.actors.root_actors import PrivateRootActor, PublicRootActor
        from domo_actors.actors.address import Uuid7Address
        from domo_actors.actors.definition import Definition

        # Create PrivateRootActor (system root)
        private_address = Uuid7Address()
        private_definition = Definition("PrivateRootActor", private_address, ())
        private_mailbox = ArrayMailbox()
        private_environment = Environment(
            address=private_address,
            definition=private_definition,
            mailbox=private_mailbox,
            parent=None,
            stage=self,
            logger=self._logger,
            supervisor=None
        )

        private_actor = PrivateRootActor()
        private_actor.set_environment(private_environment)
        self._private_root_actor = create_actor_proxy(private_actor, private_mailbox)
        self._directory.register(private_address, self._private_root_actor)
        asyncio.create_task(private_actor.start())

        # Create PublicRootActor (default parent for user actors)
        public_address = Uuid7Address()
        public_definition = Definition("PublicRootActor", public_address, ())
        public_mailbox = ArrayMailbox()
        public_environment = Environment(
            address=public_address,
            definition=public_definition,
            mailbox=public_mailbox,
            parent=self._private_root_actor,
            stage=self,
            logger=self._logger,
            supervisor=None
        )

        public_actor = PublicRootActor()
        public_actor.set_environment(public_environment)
        self._public_root_actor = create_actor_proxy(public_actor, public_mailbox)
        self._directory.register(public_address, self._public_root_actor)
        asyncio.create_task(public_actor.start())

    def __str__(self) -> str:
        """String representation."""
        return f"LocalStage(actors={self._directory.size()})"
