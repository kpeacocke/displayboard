import argparse
import time
import threading

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
    return parser.parse_args()


def main() -> None:
    """
    Parse CLI flags and start configured subsystems.
    """
    args = parse_args()

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
