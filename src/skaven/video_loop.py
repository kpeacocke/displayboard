import subprocess
import shutil
import sys
import time
import platform

VIDEO_PATH = "src/assets/video/skaven_loop.mp4"


def check_mpv_installed() -> None:
    # Skip MPV requirement on non-Linux platforms (e.g. macOS)
    if platform.system() != "Linux":
        return
    if shutil.which("mpv") is None:
        print("❌ Error: MPV not installed.")
        print("👉 Install it with: sudo apt install mpv")
        sys.exit(1)


def play_video_loop() -> None:
    while True:
        try:
            subprocess.run(
                [
                    "mpv",
                    "--fullscreen",
                    "--loop",
                    "--no-terminal",
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
    check_mpv_installed()
    play_video_loop()
