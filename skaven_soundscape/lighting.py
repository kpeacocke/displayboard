import time
import random
import math

# Local board pin constants and NeoPixel stubs
from .board import D18
from .neopixel import NeoPixel, GRB


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
        for _ in range(10):  # Run for 10 iterations
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
