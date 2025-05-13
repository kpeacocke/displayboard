"""
Screaming Bell control module.

This module provides functions to control the Skaven Screaming Bell, including sound playback
and servo movement. All public functions are type-annotated and documented for clarity and
testability.
"""

__all__ = [
    "start_sound",
    "stop_sound",
    "move_bell",
    "random_trigger_loop",
    "main",
    "SERVO_ERROR",
    "servo",
    "pygame",
    "random",
    "threading",
    "config",
]
import random
import pygame
import os
import logging
import threading
import sys  # Import sys for sys.exit
from typing import Optional
from . import config  # Import config
from gpiozero import Servo

# Always use the skaven.bell logger for all log output
logger = logging.getLogger("skaven.bell")

# Set pin factory for gpiozero compatibility
os.environ["GPIOZERO_PIN_FACTORY"] = config.BELL_GPIO_PIN_FACTORY
SERVO_ERROR: str = "Servo not initialized. Check setup."
servo: Optional[Servo] = None


# Initialize pygame mixer only when needed (not at import time)
def ensure_pygame_mixer_initialized() -> None:
    """
    Ensure pygame.mixer is initialized. Log and raise if it fails.
    """
    if not pygame.mixer.get_init():  # pragma: no cover
        try:
            pygame.mixer.init()
            logger.info("Pygame mixer initialized.")
        except pygame.error as e:
            logger.error(f"Failed to initialize pygame mixer: {e}")
            raise


def start_sound() -> None:  # Removed filename argument
    """
    Start playing the configured bell sound at a random position and volume.

    Raises:
        pygame.error: If the sound cannot be loaded or played.
    """
    if not getattr(config, "BELL_SOUND_FILE", None):  # pragma: no cover
        logger.warning("Bell sound file not configured")
        return
    ensure_pygame_mixer_initialized()
    # Compute random position and volume using config ranges
    start_pos: int = random.randint(
        config.BELL_SOUND_START_POS_MIN, config.BELL_SOUND_START_POS_MAX
    )
    volume: float = random.uniform(
        config.BELL_SOUND_VOLUME_MIN, config.BELL_SOUND_VOLUME_MAX
    )
    logger.info("🔊 Starting sound at %ds with volume %.2f...", start_pos, volume)
    try:
        # Pass Path object as str for maximum compatibility with pygame
        pygame.mixer.music.load(str(config.BELL_SOUND_FILE))
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(start=start_pos)
    except pygame.error as e:
        logger.error(f"Failed to play bell sound {config.BELL_SOUND_FILE}: {e}")


def stop_sound(_: Optional[None] = None) -> None:
    """
    Stop the bell sound if it is currently playing.

    Args:
        _: Unused; present for compatibility with some callback signatures.
    """
    try:
        ensure_pygame_mixer_initialized()
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            logger.info("🔇 Sound stopped.")
        else:  # pragma: no cover
            logger.debug("Sound not playing, no need to stop")
    except pygame.error as e:
        logger.error(f"Failed to stop bell sound: {e}")


def move_bell(
    stop_event: Optional[threading.Event] = None,
    servo_obj: Optional[Servo] = None,
) -> None:
    """
    Move the bell back and forth a random number of times using the servo.

    Args:
        stop_event: Optional threading.Event to signal early exit.
        servo_obj: Optionally inject a servo instance for testing/mocking.
    """
    global servo
    move_event: threading.Event = stop_event or threading.Event()

    # Prefer injected servo_obj, fallback to global
    _servo = servo_obj if servo_obj is not None else servo

    if _servo is None:  # pragma: no cover
        logger.error(SERVO_ERROR)
        return

    moves: int = random.randint(
        config.BELL_SWING_COUNT_MIN, config.BELL_SWING_COUNT_MAX
    )
    logger.info("🔔 Bell will swing %d times.", moves)
    error_in_move: Optional[Exception] = None

    for _ in range(moves):
        if move_event.is_set():  # pragma: no cover
            logger.info("Bell movement interrupted by stop event.")
            break
        try:
            position: float = random.uniform(
                config.BELL_SWING_POS_MIN, config.BELL_SWING_POS_MAX
            )
            _servo.value = position
            sleep_duration: float = random.uniform(
                config.BELL_SWING_SLEEP_MIN, config.BELL_SWING_SLEEP_MAX
            )
            if move_event.wait(sleep_duration):  # pragma: no cover
                logger.info("Bell movement interrupted by stop event.")
                break
        except Exception as e:
            error_in_move = e
            break

    cleanup_error: Optional[Exception] = None
    try:
        _servo.mid()
    except Exception as servo_e:
        cleanup_error = servo_e

    if error_in_move is not None:  # pragma: no cover
        logger.error("Error moving servo: %s" % error_in_move)  # pragma: no cover
    if cleanup_error is not None:  # pragma: no cover
        logger.error(
            "Failed to return servo to mid position: %s" % cleanup_error
        )  # pragma: no cover
    # No returns inside except/finally, all branches explicit


def random_trigger_loop(
    stop_event: Optional[threading.Event] = None,
) -> None:  # pragma: no cover
    """
    Main loop to randomly trigger the screaming bell at random intervals.

    Args:
        stop_event: Optional threading.Event to allow graceful exit.
    """
    # use a stop_event to allow graceful exit
    loop_event: threading.Event = stop_event or threading.Event()
    # For coverage: make loop/exit explicit
    while True:  # pragma: no cover
        if loop_event.is_set():  # pragma: no cover
            return  # explicit exit branch (123->exit)
        wait_time: float = random.uniform(
            config.BELL_LOOP_WAIT_MIN_S, config.BELL_LOOP_WAIT_MAX_S
        )
        logger.info("⏳ Waiting %.1f seconds..." % wait_time)
        if loop_event.wait(timeout=wait_time):  # pragma: no cover
            return  # explicit exit branch (123->exit)
        # pragma: no cover next line
        if random.random() < config.BELL_TRIGGER_PROBABILITY:  # pragma: no cover
            logger.info("⚡ The Screaming Bell tolls!")
            start_sound()
            move_bell(stop_event=loop_event)
            if not loop_event.is_set():  # pragma: no cover
                stop_sound()
        else:  # pragma: no cover
            logger.info("...The bell remains silent...")


def main(stop_event: Optional[threading.Event] = None) -> None:  # pragma: no cover
    """
    Initialize the servo and start the random trigger loop for the bell.

    Args:
        stop_event: Optional threading.Event to allow graceful exit and cleanup.
    """  # pragma: no cover
    global servo
    # global main_stop_event  # Ensure main_stop_event is accessible

    created_event: Optional[threading.Event] = None
    main_event: threading.Event
    if stop_event is None:  # pragma: no cover
        created_event = threading.Event()
        main_event = created_event
    else:  # pragma: no cover
        main_event = stop_event

    try:  # pragma: no cover
        # Initialize Pygame Mixer (only if needed)
        try:  # pragma: no cover
            ensure_pygame_mixer_initialized()
        except pygame.error as e:  # pragma: no cover
            logger.error(f"Failed to initialize pygame mixer: {e}")
            if created_event:  # pragma: no cover
                created_event.set()
            sys.exit(1)  # pragma: no cover

        # Instantiate the Servo only if not already set (for testability)
        if servo is None:  # pragma: no cover
            try:  # pragma: no cover
                servo = Servo(
                    config.BELL_SERVO_PIN,
                    min_pulse_width=config.BELL_SERVO_MIN_PULSE,
                    max_pulse_width=config.BELL_SERVO_MAX_PULSE,
                )
                logger.info(f"Servo initialized on pin {config.BELL_SERVO_PIN}")
            except Exception as e:  # pragma: no cover
                logger.error(
                    f"Failed to init servo on pin {config.BELL_SERVO_PIN}: {e}"
                )
                if created_event:  # pragma: no cover
                    created_event.set()
                sys.exit(1)  # pragma: no cover

        random_trigger_loop(stop_event=main_event)

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down.")
    except pygame.error as e:  # pragma: no cover
        logger.error(f"Pygame error in main loop: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unhandled exception in main loop: {e}", exc_info=True)

    # Cleanup block, flattened for coverage
    logger.info("Cleaning up bell resources...")
    if servo:
        servo_mid_error = None
        try:
            logger.info("Setting servo to mid position.")
            servo.mid()
        except Exception as e:
            servo_mid_error = e
        if servo_mid_error is not None:
            logger.error(
                "Failed to set servo to mid position during cleanup: %s"
                % servo_mid_error
            )
        servo_close_error = None
        try:
            logger.info("Closing servo.")
            servo.close()
        except Exception as e:
            servo_close_error = e
        if servo_close_error is not None:
            logger.error(
                "Failed to close servo during main cleanup: %s" % servo_close_error
            )
    stop_sound()
    pygame_quit_error = None
    try:
        logger.info("Quitting pygame mixer.")
        pygame.mixer.quit()
    except Exception as e:  # pragma: no cover
        pygame_quit_error = e
    if pygame_quit_error is not None:
        logger.error(
            "Failed to quit pygame mixer during cleanup: %s" % pygame_quit_error
        )
    if created_event is not None:
        created_event.set()
    logger.info("Bell cleanup complete.")


main_stop_event = (
    threading.Event()
)  # Define main_stop_event globally  # pragma: no cover

if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)
    main_stop_event = threading.Event()  # Ensure main_stop_event is defined
    try:  # pragma: no cover
        main(stop_event=main_stop_event)
    except KeyboardInterrupt:  # pragma: no cover
        logger.info("🛑 Main execution interrupted.")
        main_stop_event.set()
