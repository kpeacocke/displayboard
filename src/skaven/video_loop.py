"""
Video loop system for Skaven project.

This module provides functions for checking MPV installation, playing video loops, and handling
video process errors. All public functions are type-annotated and documented for clarity and
testability.
"""

__all__ = [
    "check_mpv_installed",
    "play_video_loop",
    "run_video_loop",
    "handle_video_process",
    "handle_process_error",
    "handle_keyboard_interrupt",
    "handle_unexpected_error",
    "cleanup_process",
    "main",
    "logger",
    "config",
]
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
    system = platform.system()
    if system == "Linux":
        if shutil.which("mpv") is None:
            print("❌ Error: MPV not installed.")
            logger.error("❌ Error: MPV not installed.")
            print("👉 Install it with: sudo apt install mpv")
            logger.error("👉 Install it with: sudo apt install mpv")
            sys.exit(1)
    elif system == "Darwin":
        if shutil.which("mpv") is None:
            print("❌ Error: MPV not installed.")
            logger.error("❌ Error: MPV not installed.")
            print("👉 Install it with: brew install mpv")
            logger.error("👉 Install it with: brew install mpv")
            sys.exit(1)
    # On other systems, skip check


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
        process = handle_video_process(process)  # pragma: no cover
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
                str(config.VIDEO_FILE),  # Always use str for subprocess
            ]
            return subprocess.Popen(cmd)
    except FileNotFoundError as e:
        logger.error(
            "mpv command not found. Please ensure it is installed and in PATH. Exception: %s",
            e,
        )
        return None
    except subprocess.CalledProcessError as e:
        logger.error(
            "mpv process returned a non-zero exit status: %s",
            e,
        )
        handle_process_error(process, e)
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
        return None
    except Exception as e:
        logger.error(
            "Unexpected error in handle_video_process: %s",
            e,
            exc_info=True,
        )
        handle_unexpected_error(process, e)
    return process


def handle_process_error(
    process: Optional[subprocess.Popen[bytes]], error: Exception
) -> None:
    """Handle errors during video playback."""
    print(f"🔴 Error playing video: {error}")
    logger.error("🔴 Error during video playback: %s", error)
    if process:  # pragma: no cover
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
    if process:  # pragma: no cover
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
