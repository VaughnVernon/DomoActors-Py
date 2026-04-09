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
Test dead letters listener for collecting undeliverable messages in tests.
"""

from typing import List
from domo_actors.actors.dead_letters import DeadLetter, DeadLettersListener


class TestDeadLettersListener:
    """
    Dead letters listener implementation for testing.

    Collects dead letters for test assertions.
    """

    def __init__(self) -> None:
        """Initialize the test listener."""
        self._dead_letters: List[DeadLetter] = []

    def handle(self, dead_letter: DeadLetter) -> None:
        """
        Handle a dead letter by collecting it.

        Args:
            dead_letter: The dead letter to collect
        """
        self._dead_letters.append(dead_letter)

    def dead_letters(self) -> List[DeadLetter]:
        """
        Get collected dead letters.

        Returns:
            List of collected dead letters
        """
        return self._dead_letters

    def count(self) -> int:
        """
        Get count of collected dead letters.

        Returns:
            Number of dead letters
        """
        return len(self._dead_letters)

    def clear(self) -> None:
        """Clear collected dead letters."""
        self._dead_letters.clear()
