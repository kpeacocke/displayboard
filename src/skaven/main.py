import argparse
import threading
import logging
import time  # Added for sleep in video-disabled loop

from skaven import sounds, video_loop, lighting
from . import config  # Import config

__all__ = ["sounds", "video_loop", "lighting", "parse_args", "main"]


def parse_args() -> argparse.Namespace:
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
    return parser.parse_args()


def start_threads(
    args: argparse.Namespace, stop_event: threading.Event
) -> list[threading.Thread]:
    """
    Start threads for soundscape and lighting based on CLI arguments.
    """
    threads = []
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
    """Configure logging based on CLI flags."""
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
    """Handle video playback or wait for shutdown signal."""
    if not args.no_video:
        # Pass stop_event to video_loop.main
        video_loop.main(stop_event=stop_event)
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
    """Handle shutdown logic and join threads."""
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
    """Helper function to join threads and handle exceptions."""
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
