import pytest
import subprocess
import time
import threading
from unittest.mock import patch, MagicMock
from skaven.video_loop import (
    check_mpv_installed,
    play_video_loop,
    main,
)


def test_check_mpv_installed_installed() -> None:
    # force Linux so exit logic runs
    with patch("platform.system", return_value="Linux"):
        with patch("shutil.which", return_value="/usr/bin/mpv"):
            try:
                check_mpv_installed()
            except SystemExit as e:
                pytest.fail(
                    "check_mpv_installed() exited unexpectedly "
                    "when MPV is installed."
                )
                raise e


def test_check_mpv_installed_not_installed() -> None:
    # force Linux so exit logic runs
    with patch("platform.system", return_value="Linux"):
        with patch("shutil.which", return_value=None):
            with patch("sys.exit") as mock_exit:
                with patch("builtins.print") as mock_print:
                    check_mpv_installed()
                    mock_exit.assert_called_once_with(1)
                    mock_print.assert_any_call("❌ Error: MPV not installed.")
                    mock_print.assert_any_call(
                        "👉 Install it with: sudo apt install mpv"
                    )


def test_play_video_loop_keyboard_interrupt() -> None:
    """Test play_video_loop handles KeyboardInterrupt during run_video_loop."""
    stop_event = threading.Event()
    # Simulate KeyboardInterrupt occurring within run_video_loop
    with patch("skaven.video_loop.run_video_loop", side_effect=KeyboardInterrupt):
        with patch("skaven.video_loop.cleanup_process") as mock_cleanup:
            # play_video_loop should catch the interrupt from run_video_loop
            # and call cleanup_process with None because run_video_loop didn't
            # return a process.
            play_video_loop(stop_event)
            mock_cleanup.assert_called_once_with(None)


def test_play_video_loop_stops_on_event() -> None:
    """Test that play_video_loop stops when the stop_event is set."""
    stop_event = threading.Event()
    mock_process = MagicMock(spec=subprocess.Popen)

    # Mock run_video_loop to return a mock process
    with patch(
        "skaven.video_loop.run_video_loop", return_value=mock_process
    ) as mock_run:
        # Mock cleanup_process to check it's called correctly
        with patch("skaven.video_loop.cleanup_process") as mock_cleanup:
            # Run play_video_loop in a separate thread so we can set the event
            thread = threading.Thread(target=play_video_loop, args=(stop_event,))
            thread.start()

            # Give the loop time to start and call run_video_loop
            time.sleep(0.2)
            mock_run.assert_called_once_with(stop_event)

            # Set the event to signal shutdown
            stop_event.set()
            thread.join(timeout=1)  # Wait for the thread to finish

            assert not thread.is_alive(), "Thread did not terminate after event was set"
            # Check that cleanup was called with the process
            # returned by run_video_loop
            mock_cleanup.assert_called_once_with(mock_process)


def test_play_video_loop_called_process_error() -> None:
    """
    Test play_video_loop when run_video_loop encounters an error
    internally.
    """
    stop_event = threading.Event()
    error = subprocess.CalledProcessError(1, "cmd")
    # We mock run_video_loop itself. Let's say it tries to start, fails,
    # handles it, and then returns None because it couldn't proceed.
    with patch("skaven.video_loop.run_video_loop", side_effect=error) as mock_run:
        with patch("skaven.video_loop.cleanup_process") as mock_cleanup:
            # play_video_loop should catch the error from run_video_loop
            # and call cleanup_process with None.
            # We also expect the error to be logged or printed by the handler
            # inside run_video_loop, but we aren't testing the internals of
            # run_video_loop here directly.
            # We might need a separate test for run_video_loop's error
            # handling.
            play_video_loop(stop_event)

            mock_run.assert_called_once_with(stop_event)
            # Since run_video_loop raised an exception, play_video_loop
            # calls cleanup with None
            mock_cleanup.assert_called_once_with(None)


def test_main_runs_play_loop_with_event() -> None:
    """Test that main creates an event and passes it to play_video_loop."""
    with patch("skaven.video_loop.check_mpv_installed") as mock_check:
        with patch("skaven.video_loop.play_video_loop") as mock_loop:
            # We need to mock threading.Event to check it's passed
            mock_event = MagicMock(spec=threading.Event)
            with patch(
                "threading.Event", return_value=mock_event
            ) as mock_event_constructor:
                main()

    mock_check.assert_called_once()
    mock_event_constructor.assert_called_once()  # Check event was created
    mock_loop.assert_called_once_with(mock_event)  # Check event was passed


def test_check_mpv_installed_skips_on_non_linux() -> None:
    # On non-Linux platforms, no exit or print should occur
    with patch("platform.system", return_value="Darwin"):
        with patch("shutil.which", return_value=None):
            with patch("sys.exit") as mock_exit:
                with patch("builtins.print") as mock_print:
                    check_mpv_installed()
                    mock_exit.assert_not_called()
                    mock_print.assert_not_called()
