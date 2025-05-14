"""
Lighting effects for Skaven project.

This module provides the Skaven flicker/breathe LED effect for NeoPixel strips.
All public functions are type-annotated and documented for clarity and testability.
"""

__all__ = [
    "skaven_flicker_breathe",
    "pixels",
    "logger",
    "config",
]
import time
import threading
import logging
import random
from typing import Optional
import math

from . import config  # Import config moved to top

try:
    from skaven.board import D18

    _has_d18 = True
except ImportError:
    D18 = 18  # fallback to default value, but mark as not available
    _has_d18 = False
from skaven.neopixel import NeoPixel  # Removed unused GRB import

# Module logger
logger = logging.getLogger(__name__)


# Lighting now always uses config.LED_PIN_BCM (default: 21). Pin 18 is reserved for bell.
led_pin_to_use = config.LED_PIN_BCM

pixels = NeoPixel(
    led_pin_to_use,  # Use determined pin
    config.LED_COUNT,
    brightness=config.LED_BRIGHTNESS,
    auto_write=False,
    pixel_order=config.LED_ORDER,  # Use config string directly
)


# --- Flicker + Breathing effect ---


def skaven_flicker_breathe(stop_event: Optional[threading.Event] = None) -> None:
    """
    Run the Skaven flicker/breathe LED effect until stop_event is set.

    Args:
        stop_event: Optional threading.Event to allow graceful shutdown.
    """
    t_start: float = time.time()
    event: threading.Event = stop_event or threading.Event()
    try:
        while not event.wait(timeout=config.LIGHTING_UPDATE_INTERVAL):
            # Calculate breathing brightness (sinusoidal)
            elapsed: float = time.time() - t_start
            breathe_raw: float = (
                math.sin(elapsed * config.LIGHTING_BREATHE_FREQUENCY) + 1
            ) / 2
            breathe: float = (
                config.LIGHTING_BREATHE_MIN_BRIGHTNESS
                + breathe_raw * config.LIGHTING_BREATHE_RANGE
            )
            for i in range(config.LED_COUNT):
                if random.random() < config.LIGHTING_FLICKER_PROBABILITY:
                    r = int(
                        random.randint(
                            config.LIGHTING_FLICKER_R_MIN,
                            config.LIGHTING_FLICKER_R_MAX,
                        )
                        * breathe
                    )
                    g = int(
                        random.randint(
                            config.LIGHTING_FLICKER_G_MIN,
                            config.LIGHTING_FLICKER_G_MAX,
                        )
                        * breathe
                    )
                    b = int(
                        random.randint(
                            config.LIGHTING_FLICKER_B_MIN,
                            config.LIGHTING_FLICKER_B_MAX,
                        )
                        * breathe
                    )
                    pixels[i] = (r, g, b)
                else:
                    r = 0
                    g = int(config.LIGHTING_BASE_G * breathe)
                    b = 0
                    pixels[i] = (r, g, b)
            pixels.show()
    finally:
        # Cleanup on exit or exception
        pixels.fill((0, 0, 0))
        pixels.show()


# Remove if __name__ == "__main__": block if this module is not meant
# to be run directly
# if __name__ == "__main__":
#     try:
#         skaven_flicker_breathe(iterations=0) # iterations not used anymore
#     except KeyboardInterrupt:
#         logger.info("🛑 Lighting effect stopped by user.")
