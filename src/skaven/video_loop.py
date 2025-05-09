import subprocess
import shutil
import sys
import time
import threading
from typing import Optional
import platform
import logging

from . import config

logger = logging.getLogger(__name__)


def check_mpv_installed() -> None:
    # Skip MPV requirement on non-Linux platforms (e.g. macOS)
    if platform.system() != "Linux":
        return
    if shutil.which("mpv") is None:
        print("❌ Error: MPV not installed.")
        logger.error("❌ Error: MPV not installed.")
        print("👉 Install it with: sudo apt install mpv")
        logger.error("👉 Install it with: sudo apt install mpv")
        sys.exit(1)


def play_video_loop(stop_event: Optional[threading.Event] = None) -> None:
    """Play video in a loop until stop_event is set or KeyboardInterrupt."""
    event = stop_event or threading.Event()
    process = run_video_loop(event)
    cleanup_process(process)


def run_video_loop(
    event: threading.Event,
) -> Optional[subprocess.Popen[bytes]]:
    """Run the video loop, handling process management."""
    process: Optional[subprocess.Popen[bytes]] = None
    last_proc: Optional[subprocess.Popen[bytes]] = None
    while not event.wait(timeout=config.LOOP_WAIT_TIMEOUT):
        process = handle_video_process(process)
        if process is None:
            break
        last_proc = process
    return last_proc


def handle_video_process(
    process: Optional[subprocess.Popen[bytes]],
) -> Optional[subprocess.Popen[bytes]]:
    """Handle starting or restarting the video process."""
    try:
        if process is None or process.poll() is not None:
            logger.info("Starting mpv video loop...")
            cmd = [
                "mpv",
                "--fullscreen",
                "--loop",
                "--no-terminal",
                str(config.VIDEO_FILE),
            ]
            return subprocess.Popen(cmd)
    except FileNotFoundError:
        logger.error(
            "mpv command not found. Please ensure it is installed and in PATH."
        )
        return None
    except subprocess.CalledProcessError as e:
        handle_process_error(process, e)
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
        return None
    except Exception as e:
        handle_unexpected_error(process, e)
    return process


def handle_process_error(
    process: Optional[subprocess.Popen[bytes]], error: Exception
) -> None:
    """Handle errors during video playback."""
    print(f"🔴 Error playing video: {error}")
    logger.error("🔴 Error during video playback: %s", error)
    if process:
        process.terminate()
        process.wait()
    time.sleep(config.PROCESS_WAIT_TIMEOUT)  # Use config value


def handle_keyboard_interrupt() -> None:
    """Handle keyboard interrupt."""
    print("\n👋 Exiting...")
    logger.info("👋 KeyboardInterrupt received, stopping video loop...")


def handle_unexpected_error(
    process: Optional[subprocess.Popen[bytes]], error: Exception
) -> None:
    """Handle unexpected errors during video playback."""
    logger.error("An unexpected error occurred with video process: %s", error)
    if process:
        process.terminate()
        process.wait()
    time.sleep(config.PROCESS_WAIT_TIMEOUT)  # Use config value


def cleanup_process(process: Optional[subprocess.Popen[bytes]]) -> None:
    """Clean up the video process after the loop ends."""
    if process and process.poll() is None:
        logger.info("Stopping video loop process...")
        process.terminate()
        try:
            process.wait(timeout=config.PROCESS_WAIT_TIMEOUT)
        except subprocess.TimeoutExpired:
            logger.warning("mpv did not terminate gracefully, killing.")
            process.kill()
        logger.info("Video loop process stopped.")


def main(stop_event: Optional[threading.Event] = None) -> None:
    """Check MPV installation and play video loop with an optional
    shutdown event."""
    event = stop_event or threading.Event()
    check_mpv_installed()
    play_video_loop(event)
