"""
Stub module for NeoPixel functionality for diorama projects.

This module provides a stub NeoPixel class and color order constant for non-Pi environments.
All public methods are type-annotated and documented for clarity and testability.
"""

__all__ = ["NeoPixel", "GRB"]

from typing import Any, Tuple

# LED color order placeholder
GRB: Any = None


class NeoPixel:
    def __init__(
        self,
        pin: Any,
        count: int,
        brightness: float,
        auto_write: bool,
        pixel_order: Any,
    ) -> None:
        # Stub initializer for non-Pi environments
        pass

    def show(self) -> None:
        # Stub show method
        pass

    def fill(self, color: Tuple[int, int, int]) -> None:
        # Stub fill method
        pass

    def __setitem__(
        self,
        index: int,
        color: Tuple[int, int, int],
    ) -> None:
        # Allow index assignment in stub
        pass
