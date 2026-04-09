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
Logger - Logging interface and implementations for the actor system.
"""

from abc import ABC, abstractmethod
from typing import Optional
import sys
from datetime import datetime


class Logger(ABC):
    """Abstract logger interface with fluent API."""

    @abstractmethod
    def debug(self, message: str, error: Optional[Exception] = None) -> None:
        """Log a debug message."""
        pass

    @abstractmethod
    def info(self, message: str, error: Optional[Exception] = None) -> None:
        """Log an info message."""
        pass

    @abstractmethod
    def warn(self, message: str, error: Optional[Exception] = None) -> None:
        """Log a warning message."""
        pass

    @abstractmethod
    def error(self, message: str, error: Optional[Exception] = None) -> None:
        """Log an error message."""
        pass


class ConsoleLogger(Logger):
    """Default logger implementation using console output."""

    def __init__(self, name: str = "DomoActors") -> None:
        """
        Initialize the console logger.

        Args:
            name: Name prefix for log messages
        """
        self._name = name

    def _format_message(self, level: str, message: str, error: Optional[Exception] = None) -> str:
        """
        Format a log message.

        Args:
            level: Log level (DEBUG, INFO, WARN, ERROR)
            message: The message to log
            error: Optional exception

        Returns:
            Formatted log message
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted = f"[{timestamp}] [{level}] [{self._name}] {message}"

        if error:
            import traceback
            tb = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            formatted += f"\n{tb}"

        return formatted

    def debug(self, message: str, error: Optional[Exception] = None) -> None:
        """
        Log a debug message.

        Args:
            message: The message to log
            error: Optional exception
        """
        print(self._format_message("DEBUG", message, error), file=sys.stdout)

    def info(self, message: str, error: Optional[Exception] = None) -> None:
        """
        Log an info message.

        Args:
            message: The message to log
            error: Optional exception
        """
        print(self._format_message("INFO", message, error), file=sys.stdout)

    def warn(self, message: str, error: Optional[Exception] = None) -> None:
        """
        Log a warning message.

        Args:
            message: The message to log
            error: Optional exception
        """
        print(self._format_message("WARN", message, error), file=sys.stderr)

    def error(self, message: str, error: Optional[Exception] = None) -> None:
        """
        Log an error message.

        Args:
            message: The message to log
            error: Optional exception
        """
        print(self._format_message("ERROR", message, error), file=sys.stderr)


# Default logger instance
DefaultLogger = ConsoleLogger()
