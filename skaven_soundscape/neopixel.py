"""
Stub module for NeoPixel functionality
"""

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
