import time
import logging
import random
import math
from skaven.board import D18
from skaven.neopixel import NeoPixel, GRB

# Module logger
logger = logging.getLogger(__name__)

# --- Setup ---
LED_COUNT = 30  # Number of LEDs
LED_PIN = D18  # GPIO18 (Pin 12)
BRIGHTNESS = 0.4
ORDER = GRB  # LED color order

pixels = NeoPixel(
    LED_PIN,
    LED_COUNT,
    brightness=BRIGHTNESS,
    auto_write=False,
    pixel_order=ORDER,
)


# --- Flicker + Breathing effect ---
def skaven_flicker_breathe_v2(iterations: int = 10) -> None:
    def calculate_breathe(elapsed: float) -> float:
        breathe = (math.sin(elapsed * 0.5) + 1) / 2
        return 0.2 + breathe * 0.8

    def update_pixels(breathe: float) -> None:
        for i in range(LED_COUNT):
            if random.random() < 0.2:
                r = int(random.randint(0, 30) * breathe)
                g = int(random.randint(50, 255) * breathe)
                b = int(random.randint(0, 20) * breathe)
                pixels[i] = (r, g, b)
            else:
                r = 0
                g = int(50 * breathe)
                b = 0
                pixels[i] = (r, g, b)
        pixels.show()

    t_start = time.time()
    try:
        count = 0
        while iterations == 0 or count < iterations:
            elapsed = time.time() - t_start
            breathe = calculate_breathe(elapsed)
            update_pixels(breathe)
            time.sleep(0.05)
            count += 1 if iterations != 0 else 0
    finally:
        pixels.fill((0, 0, 0))
        pixels.show()


if __name__ == "__main__":
    try:
        skaven_flicker_breathe_v2(iterations=0)
    except KeyboardInterrupt:
        logger.info("🛑 Lighting effect stopped by user.")
# Local board pin constants and NeoPixel stubs


# --- Setup ---
LED_COUNT = 30  # Number of LEDs
LED_PIN = D18  # GPIO18 (Pin 12)
BRIGHTNESS = 0.4
ORDER = GRB  # LED color order

pixels = NeoPixel(
    LED_PIN,
    LED_COUNT,
    brightness=BRIGHTNESS,
    auto_write=False,
    pixel_order=ORDER,
)


# --- Flicker + Breathing effect ---
def skaven_flicker_breathe() -> None:
    t_start = time.time()
    try:
        while True:  # Run forever
            # Calculate breathing brightness (sinusoidal)
            elapsed = time.time() - t_start

            # Oscillates between 0 and 1
            breathe = (math.sin(elapsed * 0.5) + 1) / 2
            breathe = 0.2 + breathe * 0.8  # Keep minimum brightness at 20%

            for i in range(LED_COUNT):
                if random.random() < 0.2:  # 20% chance to flicker randomly
                    r = int(random.randint(0, 30) * breathe)
                    g = int(random.randint(50, 255) * breathe)
                    b = int(random.randint(0, 20) * breathe)
                    pixels[i] = (r, g, b)
                else:
                    r = 0
                    g = int(50 * breathe)
                    b = 0
                    pixels[i] = (r, g, b)

            pixels.show()
            time.sleep(0.05)  # Faster update for smooth breathing
    finally:
        # Cleanup on exit or exception
        pixels.fill((0, 0, 0))
        pixels.show()
