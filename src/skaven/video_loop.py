# skaven_soundscape/video_loop.py

import subprocess
import shutil
import sys
import time
import platform

VIDEO_PATH = "assets/video/skaven_loop.mp4"


def check_omxplayer_installed() -> None:
    # Skip omxplayer requirement on non-Linux platforms (e.g. macOS)
    if platform.system() != "Linux":
        return
    if shutil.which("omxplayer") is None:
        print("❌ Error: omxplayer not installed.")
        print("👉 Install it with: sudo apt install omxplayer")
        sys.exit(1)


def play_video_loop() -> None:
    while True:
        try:
            subprocess.run(
                [
                    "omxplayer",
                    "--no-osd",
                    "--loop",
                    "--aspect-mode",
                    "fill",
                    "--display",
                    "0",
                    VIDEO_PATH,
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"🔴 Error playing video: {e}")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break


def main() -> None:
    check_omxplayer_installed()
    play_video_loop()
