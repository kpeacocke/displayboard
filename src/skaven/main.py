"""
Main entry point for Skaven soundscape, video, and lighting system.

This module parses CLI arguments, configures logging, and starts the sound, video, and lighting
subsystems. All public functions are type-annotated and documented for clarity and testability.
"""

__all__ = [
    "parse_args",
    "start_threads",
    "main",
    "configure_logging",
    "handle_video_playback",
    "handle_shutdown",
    "_join_threads",
]
import argparse
import threading
import logging
import time  # Added for sleep in video-disabled loop

from skaven import sounds, video_loop, lighting
from . import config  # Import config

__all__ = ["sounds", "video_loop", "lighting", "parse_args", "main"]


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for the Skaven soundscape system.

    Returns:
        argparse.Namespace with parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog="skaven",
        description="Skaven soundscape + video + lighting controller",
    )
    parser.add_argument(
        "--no-sounds",
        action="store_true",
        help="Disable soundscape loops",
    )
    parser.add_argument(
        "--no-video",
        action="store_true",
        help="Disable video playback",
    )
    parser.add_argument(
        "--no-lighting",
        action="store_true",
        help="Disable lighting effects",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose (INFO) logging",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug (DEBUG) logging",
    )
    parser.add_argument(
        "--test-exit",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def start_threads(
    args: argparse.Namespace, stop_event: threading.Event
) -> list[threading.Thread]:
    """
    Start threads for soundscape and lighting based on CLI arguments.

    Args:
        args: Parsed command-line arguments.
        stop_event: Event to signal shutdown to all threads.

    Returns:
        List of started threading.Thread objects.
    """
    threads: list[threading.Thread] = []
    if not args.no_sounds:
        t = threading.Thread(
            target=sounds.main,
            name="SoundscapeThread",
            daemon=False,
            args=(stop_event,),
        )
        threads.append(t)
        t.start()

    if not args.no_lighting:
        t = threading.Thread(
            target=lighting.skaven_flicker_breathe,
            name="LightingThread",
            daemon=False,
            args=(stop_event,),
        )
        threads.append(t)
        t.start()

    return threads


def main() -> None:
    """
    Parse CLI flags and start configured subsystems.
    """
    args = parse_args()
    if getattr(args, "test_exit", False):
        return
    logger = configure_logging(args)

    # create a shutdown event for graceful exit
    stop_event = threading.Event()

    # Start threads based on arguments
    threads = start_threads(args, stop_event)

    try:
        handle_video_playback(args, stop_event)
    except KeyboardInterrupt:
        handle_shutdown(threads, stop_event, logger, args)


def configure_logging(args: argparse.Namespace) -> logging.Logger:
    """
    Configure logging based on CLI flags.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Configured logger instance.
    """
    level = config.LOG_LEVEL_WARNING  # Use config default
    if args.debug:
        level = config.LOG_LEVEL_VERBOSE  # Use config debug level
    elif args.verbose:
        level = config.LOG_LEVEL_DEFAULT  # Use config info level
    logging.basicConfig(
        level=level,
        format=config.LOG_FORMAT,  # Use config format
    )
    logger = logging.getLogger(__name__)
    logger.debug("Starting main with args: %s", args)
    return logger


def handle_video_playback(
    args: argparse.Namespace, stop_event: threading.Event
) -> None:
    """
    Handle video playback or wait for shutdown signal.

    Args:
        args: Parsed command-line arguments.
        stop_event: Event to signal shutdown.
    """
    if not args.no_video:
        # Pass stop_event to video_loop.main and handle KeyboardInterrupt gracefully
        try:
            video_loop.main(stop_event=stop_event)
        except KeyboardInterrupt:
            return
    else:
        # If video is disabled, wait using time.sleep so tests can patch sleep
        while not stop_event.is_set():
            try:
                time.sleep(config.MAIN_LOOP_SLEEP_S)
            except KeyboardInterrupt:
                break


def handle_shutdown(
    threads: list[threading.Thread],
    stop_event: threading.Event,
    logger: logging.Logger,
    args: argparse.Namespace,
) -> None:
    """
    Handle shutdown logic and join threads.

    Args:
        threads: List of running threads to join.
        stop_event: Event to signal shutdown.
        logger: Logger instance for logging shutdown progress.
        args: Parsed command-line arguments.
    """
    try:
        if not args.no_video:
            # Pass stop_event to video_loop.main
            video_loop.main(stop_event=stop_event)
        else:
            # If video is disabled, just wait for KeyboardInterrupt
            while not stop_event.is_set():
                # Use config sleep interval
                stop_event.wait(config.MAIN_LOOP_SLEEP_S)
    except KeyboardInterrupt:
        pass
    logger.info("🛑 Shutdown signal received. Stopping threads...")
    stop_event.set()
    _join_threads(threads, logger)
    logger.info("All threads stopped. Exiting.")


def _join_threads(threads: list[threading.Thread], logger: logging.Logger) -> None:
    """
    Helper function to join threads and handle exceptions.

    Args:
        threads: List of threads to join.
        logger: Logger instance for logging join progress.
    """
    logger.debug("Waiting for threads to join...")
    for t in threads:
        logger.debug(f"Joining thread: {t.name}")
        try:
            t.join()
            logger.debug(f"Thread {t.name} joined.")
        except AttributeError:
            logger.warning(f"Could not join thread {t.name} (AttributeError).")
        except RuntimeError as e:
            # Split long line
            err_msg = f"Could not join thread {t.name}"
            logger.warning(f"{err_msg} (RuntimeError: {e}).")


if __name__ == "__main__":
    main()  # noqa: F821
