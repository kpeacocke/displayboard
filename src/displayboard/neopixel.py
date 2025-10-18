"""
NeoPixel wrapper module for diorama projects.

This module provides a NeoPixel class that uses real hardware on Linux/Raspberry Pi
and provides a stub for non-Pi environments (development/testing).
All public methods are type-annotated and documented for clarity and testability.
"""

__all__ = ["NeoPixel", "GRB"]

import sys
import logging
from typing import Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import real NeoPixel libraries on Linux
if sys.platform == "linux":
    try:
        import board
        import neopixel as real_neopixel

        HAS_NEOPIXEL = True
        logger.info("NeoPixel hardware support loaded")
    except (ImportError, NotImplementedError) as e:
        HAS_NEOPIXEL = False
        board = None
        real_neopixel = None
        logger.warning(f"NeoPixel hardware not available: {e}")
else:
    HAS_NEOPIXEL = False
    board = None
    real_neopixel = None
    logger.info("Running on non-Linux platform, using NeoPixel stub")

# LED color order
GRB = "GRB"


class NeoPixel:
    """NeoPixel wrapper that uses hardware on Linux or stub elsewhere."""

    def __init__(
        self,
        pin: Any,
        count: int,
        brightness: float = 1.0,
        auto_write: bool = True,
        pixel_order: Any = GRB,
    ) -> None:
        """
        Initialize NeoPixel strip.

        Args:
            pin: GPIO pin number (BCM numbering)
            count: Number of LEDs in the strip
            brightness: Brightness level (0.0 to 1.0)
            auto_write: Whether to auto-update on changes
            pixel_order: Color order (e.g., "GRB")
        """
        self.count = count
        self.brightness = brightness
        self.auto_write = auto_write
        self._pixels: Optional[Any] = None

        if HAS_NEOPIXEL and board is not None and real_neopixel is not None:
            try:
                # Map BCM pin numbers to board pins
                pin_map = {
                    18: board.D18,
                    21: board.D21,
                    12: board.D12,
                    10: board.D10,
                }

                board_pin = pin_map.get(pin)
                if board_pin is None:
                    supported = list(pin_map.keys())
                    logger.error(f"Pin {pin} not in pin map. Supported: {supported}")
                    return

                # Initialize real NeoPixel strip
                self._pixels = real_neopixel.NeoPixel(
                    board_pin,
                    count,
                    brightness=brightness,
                    auto_write=auto_write,
                    pixel_order=pixel_order,
                )
                msg = f"NeoPixel strip initialized on pin {pin} with {count} LEDs"
                logger.info(msg)
            except Exception as e:
                logger.error(f"Failed to initialize NeoPixel hardware: {e}")
                self._pixels = None
        else:
            logger.debug(f"NeoPixel stub initialized (pin={pin}, count={count})")

    def show(self) -> None:
        """Update the LED strip to show current pixel values."""
        if self._pixels is not None:
            try:
                self._pixels.show()
            except Exception as e:
                logger.error(f"Failed to update NeoPixel display: {e}")

    def fill(self, color: Tuple[int, int, int]) -> None:
        """
        Fill all pixels with the same color.

        Args:
            color: RGB color tuple (r, g, b) with values 0-255
        """
        if self._pixels is not None:
            try:
                self._pixels.fill(color)
                if self.auto_write:
                    self._pixels.show()
            except Exception as e:
                logger.error(f"Failed to fill NeoPixel strip: {e}")

    def __setitem__(self, index: int, color: Tuple[int, int, int]) -> None:
        """
        Set the color of a specific pixel.

        Args:
            index: Pixel index (0 to count-1)
            color: RGB color tuple (r, g, b) with values 0-255
        """
        if self._pixels is not None:
            try:
                self._pixels[index] = color
                if self.auto_write:
                    self._pixels.show()
            except Exception as e:
                logger.error(f"Failed to set pixel {index}: {e}")
