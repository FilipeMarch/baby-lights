"""
Navigation Component

Manages navigation between a finite set of destinations with:
- Active destination tracking
- LIFO back history
- Deterministic fallback mapping
- Push/replace navigation modes
- Jump-back behavior for destinations in history
- Safe back navigation with fallback support
"""

from typing import Dict, List, Optional, Set


class Navigator:
    """
    Navigation component that manages a finite set of destinations
    with history and fallback support.
    """

    def __init__(
        self,
        destinations: List[str],
        fallbacks: Optional[Dict[str, str]] = None,
        initial_destination: Optional[str] = None,
    ):
        """
        Initialize the navigator.

        Args:
            destinations: List of valid destination strings
            fallbacks: Optional mapping of destination -> fallback destination
            initial_destination: Optional starting destination (defaults to first in list)

        Raises:
            ValueError: If destinations is empty, initial destination is invalid,
                       or fallback mappings reference unknown destinations
        """
        if not destinations:
            raise ValueError('Destinations must be a non-empty list')

        self._destinations: Set[str] = set(destinations)
        self._fallbacks: Dict[str, str] = fallbacks or {}
        self._active: str = initial_destination or destinations[0]
        self._history: List[str] = []

        # Validate initial destination
        if self._active not in self._destinations:
            raise ValueError(
                f"Initial destination '{self._active}' not in destinations"
            )

        # Validate fallbacks
        for from_dest, to_dest in self._fallbacks.items():
            if from_dest not in self._destinations:
                raise ValueError(f"Fallback source '{from_dest}' not in destinations")
            if to_dest not in self._destinations:
                raise ValueError(f"Fallback target '{to_dest}' not in destinations")

    def navigate(self, destination: str, mode: str = 'push') -> None:
        """
        Navigate to a destination.

        Args:
            destination: Target destination
            mode: 'push' (default) or 'replace'

        Raises:
            ValueError: If destination is unknown or mode is invalid
        """
        if destination not in self._destinations:
            raise ValueError(f'Unknown destination: {destination}')

        if mode not in {'push', 'replace'}:
            raise ValueError(f"Invalid mode: {mode}. Must be 'push' or 'replace'")

        # No-op if navigating to current destination
        if destination == self._active:
            return

        # Check if destination is in history (jump-back behavior)
        if destination in self._history:
            history_index = self._history.index(destination)
            # Remove the target and everything newer
            self._history = self._history[:history_index]
            self._active = destination
            return

        # Normal navigation
        if mode == 'push':
            # Add current destination to history before switching
            self._add_to_history(self._active)
        # For 'replace' mode, don't add to history

        self._active = destination

    def back(self) -> bool:
        """
        Navigate back through history or use fallback.

        Returns:
            True if navigation occurred, False if no back option available
        """
        if self._history:
            # Pop from history
            self._active = self._history.pop()
            return True
        elif self._active in self._fallbacks:
            # Use fallback mapping
            self._active = self._fallbacks[self._active]
            return True

        # No back option available
        return False

    def current(self) -> str:
        """
        Get current destination.

        Returns:
            Current active destination
        """
        return self._active

    def can_go_back(self) -> bool:
        """
        Check if back navigation is possible.

        Returns:
            True if back is possible
        """
        return len(self._history) > 0 or self._active in self._fallbacks

    def replace_history(
        self, new_history: List[str], max_depth: Optional[int] = None
    ) -> None:
        """
        Replace the entire history.

        Args:
            new_history: New history list
            max_depth: Optional maximum depth to enforce

        Raises:
            ValueError: If history contains unknown destinations
        """
        if not isinstance(new_history, list):
            raise ValueError('History must be a list')

        # Validate all entries are known destinations
        for dest in new_history:
            if dest not in self._destinations:
                raise ValueError(f'Unknown destination in history: {dest}')

        # Remove duplicates and undefined values, maintain order
        cleaned: list = []
        for dest in new_history:
            if (
                dest is not None
                and dest != self._active
                and (not cleaned or cleaned[-1] != dest)
            ):
                cleaned.append(dest)

        # Apply depth limit if specified
        if max_depth is not None:
            cleaned = cleaned[-max_depth:]

        self._history = cleaned

    def get_history(self) -> List[str]:
        """
        Get a copy of the current history.

        Returns:
            Copy of history list
        """
        return self._history.copy()

    def _add_to_history(self, destination: str) -> None:
        """
        Add destination to history, avoiding duplicates and None values.

        Args:
            destination: Destination to add
        """
        if destination is not None and (
            not self._history or self._history[-1] != destination
        ):
            self._history.append(destination)
