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

    if not args.no_sounds:
        threading.Thread(
            target=sounds.main,
            name="SoundscapeThread",
            daemon=True,
        ).start()

    if not args.no_lighting:
        threading.Thread(
            target=lighting.skaven_flicker_breathe,
            name="LightingThread",
            daemon=True,
        ).start()

    try:
        if not args.no_video:
            video_loop.main()
        else:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
