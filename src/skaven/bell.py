import random
import pygame
import os
import logging
import threading
import sys  # Import sys for sys.exit
from typing import Optional
from gpiozero import Servo


from . import config  # Import config

# Set pin factory from config
os.environ["GPIOZERO_PIN_FACTORY"] = config.BELL_GPIO_PIN_FACTORY

SERVO_ERROR = "Servo not initialized. Check setup."
servo = None

# Initialize pygame mixer
try:
    pygame.mixer.init()
except pygame.error as e:
    logging.getLogger(__name__).error(f"Failed to initialize pygame mixer: {e}")
    # Consider disabling sound if mixer fails


def start_sound() -> None:  # Removed filename argument
    """Start playing sound at a random position and volume."""
    if not getattr(config, "BELL_SOUND_FILE", None):
        logging.getLogger(__name__).warning("Bell sound file not configured")
        return
    # compute random position and volume using config ranges
    start_pos = random.randint(
        config.BELL_SOUND_START_POS_MIN, config.BELL_SOUND_START_POS_MAX
    )
    volume = random.uniform(config.BELL_SOUND_VOLUME_MIN, config.BELL_SOUND_VOLUME_MAX)
    logging.getLogger(__name__).info(
        "🔊 Starting sound at %ds with volume %.2f...", start_pos, volume
    )
    try:
        # Convert Path object to string for pygame
        pygame.mixer.music.load(str(config.BELL_SOUND_FILE))
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(start=start_pos)
    except pygame.error as e:
        logging.getLogger(__name__).error(
            f"Failed to play bell sound {config.BELL_SOUND_FILE}: {e}"
        )


def stop_sound(_: Optional[None] = None) -> None:
    """Stop the music."""
    try:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            logging.getLogger(__name__).info("🔇 Sound stopped.")
        else:
            logging.getLogger(__name__).debug("Sound not playing, no need to stop")
    except pygame.error as e:
        logging.getLogger(__name__).error(f"Failed to stop bell sound: {e}")


def move_bell(stop_event: Optional[threading.Event] = None) -> None:
    """Move the bell back and forth a random number of times."""
    global servo
    event = stop_event or threading.Event()

    if servo is None:
        logging.getLogger(__name__).error(SERVO_ERROR)
        return

    moves = random.randint(config.BELL_SWING_COUNT_MIN, config.BELL_SWING_COUNT_MAX)
    logging.getLogger(__name__).info("🔔 Bell will swing %d times.", moves)
    error_in_move = None

    for _ in range(moves):
        if event.is_set():
            logging.getLogger(__name__).info("Bell movement interrupted by stop event.")
            break
        try:
            position = random.uniform(
                config.BELL_SWING_POS_MIN, config.BELL_SWING_POS_MAX
            )
            servo.value = position
            sleep_duration = random.uniform(
                config.BELL_SWING_SLEEP_MIN, config.BELL_SWING_SLEEP_MAX
            )
            if event.wait(sleep_duration):
                logging.getLogger(__name__).info(
                    "Bell movement interrupted by stop event."
                )
                break
        except Exception as e:
            error_in_move = e
            break

    cleanup_error = None
    try:
        servo.mid()
    except Exception as servo_e:
        cleanup_error = servo_e

    if error_in_move is not None:
        logging.getLogger(__name__).error("Error moving servo: %s" % error_in_move)
    if cleanup_error is not None:
        logging.getLogger(__name__).error(
            "Failed to return servo to mid position: %s" % cleanup_error
        )
    # No returns inside except/finally, all branches explicit


def random_trigger_loop(stop_event: Optional[threading.Event] = None) -> None:
    """Main loop to randomly trigger the screaming bell."""
    # use a stop_event to allow graceful exit
    event = stop_event or threading.Event()
    # For coverage: make loop/exit explicit
    while True:
        if event.is_set():
            return  # explicit exit branch (123->exit)
        wait_time = random.uniform(
            config.BELL_LOOP_WAIT_MIN_S, config.BELL_LOOP_WAIT_MAX_S
        )
        logging.getLogger(__name__).info("⏳ Waiting %.1f seconds..." % wait_time)
        if event.wait(timeout=wait_time):
            return  # explicit exit branch (123->exit)
        if random.random() < config.BELL_TRIGGER_PROBABILITY:
            logging.getLogger(__name__).info("⚡ The Screaming Bell tolls!")
            start_sound()
            move_bell(stop_event=event)
            if not event.is_set():
                stop_sound()
        else:
            logging.getLogger(__name__).info("...The bell remains silent...")


def main(stop_event: Optional[threading.Event] = None) -> None:
    """Initialize servo and start the random trigger loop."""
    global servo
    # global main_stop_event  # Ensure main_stop_event is accessible

    created_event = None
    if stop_event is None:
        created_event = threading.Event()
        event = created_event
    else:
        event = stop_event

    try:
        # Initialize Pygame Mixer
        try:
            pygame.mixer.init()
            logging.getLogger(__name__).info("Pygame mixer initialized.")
        except pygame.error as e:
            logging.getLogger(__name__).error(f"Failed to initialize pygame mixer: {e}")
            if created_event:
                created_event.set()
            sys.exit(1)

        # Initialize Servo
        try:
            servo = Servo(
                config.BELL_SERVO_PIN,
                min_pulse_width=config.BELL_SERVO_MIN_PULSE,
                max_pulse_width=config.BELL_SERVO_MAX_PULSE,
            )
            logging.getLogger(__name__).info(
                f"Servo initialized on pin {config.BELL_SERVO_PIN}"
            )
        except Exception as e:
            logging.getLogger(__name__).error(
                f"Failed to init servo on pin {config.BELL_SERVO_PIN}: {e}"
            )
            if created_event:
                created_event.set()
            sys.exit(1)

        random_trigger_loop(stop_event=event)

    except KeyboardInterrupt:
        logging.getLogger(__name__).info("KeyboardInterrupt received, shutting down.")
    except pygame.error as e:
        logging.getLogger(__name__).error(
            f"Pygame error in main loop: {e}", exc_info=True
        )
    except Exception as e:
        logging.getLogger(__name__).error(
            f"Unhandled exception in main loop: {e}", exc_info=True
        )

    # Cleanup block, flattened for coverage
    logging.getLogger(__name__).info("Cleaning up bell resources...")
    if servo:
        servo_mid_error = None
        try:
            logging.getLogger(__name__).info("Setting servo to mid position.")
            servo.mid()
        except Exception as e:
            servo_mid_error = e
        if servo_mid_error is not None:
            logging.getLogger(__name__).error(
                "Failed to set servo to mid position during cleanup: %s"
                % servo_mid_error
            )
        servo_close_error = None
        try:
            logging.getLogger(__name__).info("Closing servo.")
            servo.close()
        except Exception as e:
            servo_close_error = e
        if servo_close_error is not None:
            logging.getLogger(__name__).error(
                "Failed to close servo during main cleanup: %s" % servo_close_error
            )
    stop_sound()
    pygame_quit_error = None
    try:
        logging.getLogger(__name__).info("Quitting pygame mixer.")
        pygame.mixer.quit()
    except Exception as e:
        pygame_quit_error = e
    if pygame_quit_error is not None:
        logging.getLogger(__name__).error(
            "Failed to quit pygame mixer during cleanup: %s" % pygame_quit_error
        )
    if created_event:
        created_event.set()
    logging.getLogger(__name__).info("Bell cleanup complete.")


main_stop_event = threading.Event()  # Define main_stop_event globally

if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)
    main_stop_event = threading.Event()  # Ensure main_stop_event is defined
    try:
        main(stop_event=main_stop_event)
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("🛑 Main execution interrupted.")
        main_stop_event.set()
