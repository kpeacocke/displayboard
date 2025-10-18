"""
Video loop system for diorama projects.

This module provides functions for checking MPV installation, playing video loops, and handling
video process errors. All public functions are type-annotated and documented for clarity and
testability.
"""

__all__ = [
    "check_mpv_installed",
    "is_headless_environment",
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
import os
from typing import Optional
import platform
import logging
from . import config

logger = logging.getLogger(__name__)


def is_headless_environment() -> bool:
    """Check if running in a headless environment without display."""
    # Check for DISPLAY environment variable (Linux/Unix)
    has_display = bool(os.environ.get("DISPLAY"))
    # Check for Wayland (alternative to X11)
    has_wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
    # Check if explicitly disabled
    explicitly_disabled = config.VIDEO_DISABLED

    is_headless = not (has_display or has_wayland)

    if explicitly_disabled:
        logger.info(
            "Video explicitly disabled via VIDEO_DISABLED environment variable."
        )
    elif is_headless:
        logger.info(
            "Headless environment detected (no DISPLAY or WAYLAND_DISPLAY). "
            "Video will be disabled."
        )
    else:
        logger.debug(
            "Display environment detected: DISPLAY=%s, WAYLAND_DISPLAY=%s",
            os.environ.get("DISPLAY", "(not set)"),
            os.environ.get("WAYLAND_DISPLAY", "(not set)"),
        )

    return is_headless or explicitly_disabled


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
    # Check if we're in a headless environment before attempting video
    if is_headless_environment():
        logger.info("Skipping video loop in headless/disabled environment.")
        return None

    process: Optional[subprocess.Popen[bytes]] = None
    last_proc: Optional[subprocess.Popen[bytes]] = None
    while not event.wait(timeout=config.LOOP_WAIT_TIMEOUT):
        process = handle_video_process(process)  # pragma: no cover
        if process is None:
            # Video failed to start or was intentionally disabled; exit the loop
            logger.info("Video loop disabled due to initialization failure.")
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
            logger.debug("Launching mpv with command: %s", " ".join(cmd))
            try:
                new_process = subprocess.Popen(cmd)
                # Give mpv a moment to initialize and check if it crashes immediately
                time.sleep(0.1)
                if new_process.poll() is not None:
                    # Process died immediately, likely display/hardware issue
                    logger.error(
                        "mpv process died immediately after starting (exit code: %s). "
                        "This may indicate display unavailable or video hardware issues.",
                        new_process.returncode,
                    )
                    logger.warning("Video playback will be disabled.")
                    logger.info(
                        "Hint: Set VIDEO_DISABLED=1 environment variable to suppress this error."
                    )
                    return None
                logger.debug(
                    "mpv process started successfully (PID: %s)", new_process.pid
                )
                return new_process
            except OSError as e:
                # Catch OSError which includes permission errors, display errors, etc.
                logger.error(
                    "Failed to start mpv process: %s. Video playback will be disabled.",
                    e,
                )
                logger.info(
                    "Hint: Set VIDEO_DISABLED=1 environment variable to suppress this error."
                )
                return None
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
