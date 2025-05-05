import argparse
import time
import threading
import logging

from skaven import sounds, video_loop, lighting

__all__ = ["sounds", "video_loop", "lighting", "main", "parse_args"]


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


def main() -> None:
    """
    Parse CLI flags and start configured subsystems.
    """
    args = parse_args()
    # Configure logging based on CLI flags
    level = logging.WARNING
    if args.debug:
        level = logging.DEBUG
    elif args.verbose:
        level = logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.debug("Starting main with args: %s", args)

    # create a shutdown event for graceful exit
    stop_event = threading.Event()
    threads: list[threading.Thread] = []
    if not args.no_sounds:
        # Start soundscape in a thread
        t = threading.Thread(
            target=sounds.main,
            name="SoundscapeThread",
            daemon=False,
        )
        threads.append(t)
        t.start()

    if not args.no_lighting:
        # Start lighting effect in a thread
        t = threading.Thread(
            target=lighting.skaven_flicker_breathe,
            name="LightingThread",
            daemon=False,
        )
        threads.append(t)
        t.start()

    try:
        if not args.no_video:
            video_loop.main()
        else:
            while not stop_event.is_set():
                time.sleep(1)
    except KeyboardInterrupt:
        # signal all loops to stop and wait for threads
        stop_event.set()
        for t in threads:
            # attempt to join threads, skip if not supported
            try:
                t.join()
            except AttributeError:
                pass


if __name__ == "__main__":
    main()
