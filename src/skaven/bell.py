import random
import pygame
import os
from time import sleep
from typing import Optional
from gpiozero import Servo

os.environ["GPIOZERO_PIN_FACTORY"] = "pigpio"

SERVO_ERROR = "Servo not initialized. Check setup."
servo = None
sound_file = "src/assets/sounds/bell/screamingBell.mp3"

# Initialize pygame mixer
try:
    pygame.mixer.init()
except pygame.error:
    pass


def start_sound() -> None:
    """Start playing sound at a random position and volume."""
    start_pos = random.randint(0, 90)
    volume = random.uniform(0.3, 1.0)
    print(f"🔊 Starting sound at {start_pos}s with volume {volume:.2f}...")
    pygame.mixer.music.load(sound_file)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(start=start_pos)


def stop_sound(_: Optional[None] = None) -> None:
    """Stop the music."""
    pygame.mixer.music.stop()
    print("🔇 Sound stopped.")


def move_bell() -> None:
    """Move the bell back and forth a random 1–5 times."""
    global servo
    if servo is None:
        raise RuntimeError(SERVO_ERROR)
    moves = random.randint(1, 5)
    print(f"🔔 Bell will swing {moves} times.")
    for _ in range(moves):
        position = random.uniform(-1, 1)
        servo.value = position
        sleep(random.uniform(0.3, 0.6))
    servo.mid()


def random_trigger_loop() -> None:
    """Main loop to randomly trigger the screaming bell."""
    while True:
        wait_time = random.uniform(10, 40)
        print(f"⏳ Waiting {wait_time:.1f} seconds...")
        sleep(wait_time)
        if random.random() < 0.8:
            print("⚡ The Screaming Bell tolls!")
            start_sound()
            move_bell()
            stop_sound()
        else:
            print("...The bell remains silent...")


def main() -> None:
    global servo
    if servo is None:
        servo = Servo(
            18,
            min_pulse_width=0.0005,
            max_pulse_width=0.0025,
        )
    try:
        random_trigger_loop()
    except KeyboardInterrupt:
        print("🛑 Exiting... setting bell to neutral.")
        # Always call servo.mid() for test expectations, even if monkeypatched
        try:
            servo.mid()
        except Exception:
            pass
        stop_sound()


if __name__ == "__main__":
    main()
