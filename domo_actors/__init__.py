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
DomoActors - A Production-Ready Actor Model Toolkit for Python
"""

from domo_actors.actors.actor import Actor
from domo_actors.actors.actor_protocol import ActorProtocol
from domo_actors.actors.address import Address
from domo_actors.actors.definition import Definition
from domo_actors.actors.protocol import Protocol
from domo_actors.actors.stage import Stage, stage
from domo_actors.actors.local_stage import LocalStage
from domo_actors.actors.supervisor import Supervisor, SupervisionDirective, SupervisionScope
from domo_actors.actors.logger import Logger, ConsoleLogger
from domo_actors.actors.mailbox import Mailbox, OverflowPolicy
from domo_actors.actors.array_mailbox import ArrayMailbox
from domo_actors.actors.bounded_mailbox import BoundedMailbox

__version__ = "1.0.0"
__author__ = "Vaughn Vernon"
__license__ = "RPL-1.5"

__all__ = [
    "Actor",
    "ActorProtocol",
    "Address",
    "ArrayMailbox",
    "BoundedMailbox",
    "ConsoleLogger",
    "Definition",
    "LocalStage",
    "Logger",
    "Mailbox",
    "OverflowPolicy",
    "Protocol",
    "Stage",
    "stage",
    "Supervisor",
    "SupervisionDirective",
    "SupervisionScope",
]
