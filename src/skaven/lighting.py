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
    _has_d18 = False
from skaven.neopixel import NeoPixel  # Removed unused GRB import

# Module logger
logger = logging.getLogger(__name__)


# --- Setup ---
# LED_COUNT = 30  # Number of LEDs - Moved to config
# LED_PIN = D18  # GPIO18 (Pin 12) - Moved to config
# BRIGHTNESS = 0.4 - Moved to config
# ORDER = GRB  # LED color order - Moved to config

if _has_d18:
    if D18 == config.LED_PIN_BCM:
        led_pin_to_use = D18
    else:
        logger.warning(
            "board.D18 does not match config.LED_PIN_BCM, using config value."
        )
        led_pin_to_use = config.LED_PIN_BCM
else:
    logger.warning("board.D18 not found, using config.LED_PIN_BCM.")
    led_pin_to_use = config.LED_PIN_BCM

pixels = NeoPixel(
    led_pin_to_use,  # Use determined pin
    config.LED_COUNT,
    brightness=config.LED_BRIGHTNESS,
    auto_write=False,
    pixel_order=config.LED_ORDER,  # Use config string directly
)


# --- Flicker + Breathing effect ---
def skaven_flicker_breathe(
    stop_event: Optional[threading.Event] = None,
) -> None:
    """Run the skaven flicker/breathe LED effect until stop_event is set."""
    t_start = time.time()
    # use stop_event to allow graceful shutdown
    event = stop_event or threading.Event()
    try:
        while not event.wait(
            timeout=config.LIGHTING_UPDATE_INTERVAL
        ):  # Use config interval and wait
            # Calculate breathing brightness (sinusoidal)
            elapsed = time.time() - t_start

            # Oscillates between 0 and 1
            breathe_raw = (
                math.sin(elapsed * config.LIGHTING_BREATHE_FREQUENCY) + 1
            ) / 2
            # Scale to min/max range
            breathe = (
                config.LIGHTING_BREATHE_MIN_BRIGHTNESS
                + breathe_raw * config.LIGHTING_BREATHE_RANGE
            )

            for i in range(config.LED_COUNT):
                # Use config probability
                if random.random() < config.LIGHTING_FLICKER_PROBABILITY:
                    # Use config color ranges
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
                    # Use config base green
                    r = 0
                    g = int(config.LIGHTING_BASE_G * breathe)
                    b = 0
                    pixels[i] = (r, g, b)

            pixels.show()
            # time.sleep(0.05) # Replaced by event.wait() timeout
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
