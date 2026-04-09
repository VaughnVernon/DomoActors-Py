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
Directory - Sharded actor registry for O(1) lookup at scale.
"""

from typing import Dict, Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from domo_actors.actors.address import Address
    from domo_actors.actors.actor import Actor


@dataclass
class DirectoryConfig:
    """Configuration for directory sharding."""

    buckets: int
    capacity: int


class DirectoryConfigs:
    """Pre-defined directory configurations."""

    # Default: 32 buckets × 32 capacity = ~1,000 actors
    DEFAULT = DirectoryConfig(buckets=32, capacity=32)

    # High capacity: 128 buckets × 16,384 capacity = ~2,000,000 actors
    HIGH_CAPACITY = DirectoryConfig(buckets=128, capacity=16384)

    # Small: 16 buckets × 16 capacity = ~256 actors
    SMALL = DirectoryConfig(buckets=16, capacity=16)


class Directory:
    """
    Sharded actor registry using multiple map buckets for O(1) lookup.

    The directory uses hash-based sharding to distribute actors across
    multiple buckets for efficient lookup at scale.
    """

    def __init__(self, config: DirectoryConfig = DirectoryConfigs.DEFAULT) -> None:
        """
        Initialize the directory with a configuration.

        Args:
            config: Directory configuration (default: DEFAULT)
        """
        self._config = config
        self._buckets: list[Dict['Address', 'Actor']] = [
            {} for _ in range(config.buckets)
        ]

    def register(self, address: 'Address', actor: 'Actor') -> None:
        """
        Register an actor in the directory.

        Args:
            address: The actor's address
            actor: The actor proxy
        """
        bucket_index = self._bucket_index_for(address)
        self._buckets[bucket_index][address] = actor

    def unregister(self, address: 'Address') -> None:
        """
        Unregister an actor from the directory.

        Args:
            address: The actor's address
        """
        bucket_index = self._bucket_index_for(address)
        if address in self._buckets[bucket_index]:
            del self._buckets[bucket_index][address]

    def get(self, address: 'Address') -> Optional['Actor']:
        """
        Get an actor by address.

        Args:
            address: The actor's address

        Returns:
            The actor proxy or None if not found
        """
        bucket_index = self._bucket_index_for(address)
        return self._buckets[bucket_index].get(address)

    def has(self, address: 'Address') -> bool:
        """
        Check if an actor is registered.

        Args:
            address: The actor's address

        Returns:
            True if the actor is registered
        """
        bucket_index = self._bucket_index_for(address)
        return address in self._buckets[bucket_index]

    def size(self) -> int:
        """
        Get the total number of registered actors.

        Returns:
            Total actor count
        """
        return sum(len(bucket) for bucket in self._buckets)

    def _bucket_index_for(self, address: 'Address') -> int:
        """
        Calculate the bucket index for an address.

        Args:
            address: The address to hash

        Returns:
            Bucket index
        """
        return hash(address) % self._config.buckets

    def __str__(self) -> str:
        """String representation."""
        return f"Directory(buckets={self._config.buckets}, actors={self.size()})"
