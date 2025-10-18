"""
Lighting effects for diorama projects.

This module provides a generic flicker/breathe LED effect for NeoPixel strips.
All public functions are type-annotated and documented for clarity and testability.
"""

import time
import threading
import logging
import random
from typing import Optional
import math
from .neopixel import NeoPixel
from . import config

# Module logger
logger = logging.getLogger(__name__)

# Thread safety lock for NeoPixel operations
_pixel_lock = threading.Lock()

# Lighting now always uses config.LED_PIN_BCM (default: 21). Pin 18 is reserved for bell.
led_pin_to_use = config.LED_PIN_BCM
logger.info(
    f"Initializing NeoPixel on pin {led_pin_to_use} with {config.LED_COUNT} LEDs"
)
pixels = NeoPixel(
    led_pin_to_use,  # Use determined pin
    config.LED_COUNT,
    brightness=config.LED_BRIGHTNESS,
    auto_write=False,
    pixel_order=config.LED_ORDER,  # Use config string directly
)
logger.info("Lighting module initialized")
__all__ = [
    "flicker_breathe",
    "pixels",
    "logger",
    "config",
]


# --- Flicker + Breathing effect ---
def flicker_breathe(stop_event: Optional[threading.Event] = None) -> None:
    """
    Run the generic flicker/breathe LED effect until stop_event is set.

    Args:
        stop_event: Optional threading.Event to allow graceful shutdown.
    """
    logger.info("Starting flicker/breathe lighting effect")
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
            # Use lock to prevent concurrent hardware access
            with _pixel_lock:
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
        with _pixel_lock:
            pixels.fill((0, 0, 0))
            pixels.show()


if __name__ == "__main__":
    print("Lighting module main block running")
    stop_event = threading.Event()
    timer = threading.Timer(10, stop_event.set)
    timer.start()
    try:
        flicker_breathe(stop_event)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        stop_event.set()
    finally:
        pixels.fill((0, 0, 0))
        pixels.show()
        print("Lighting test complete and LEDs turned off.")
