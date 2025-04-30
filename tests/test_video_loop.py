import pytest
import subprocess
from unittest.mock import patch
from skaven.video_loop import (
    check_omxplayer_installed,
    play_video_loop,
    main,
)


def test_check_omxplayer_installed_installed() -> None:
    with patch("shutil.which", return_value="/usr/bin/omxplayer"):
        try:
            check_omxplayer_installed()
        except SystemExit as e:
            pytest.fail(
                "check_omxplayer_installed() exited unexpectedly "
                "when omxplayer is installed."
            )
            raise e


def test_check_omxplayer_installed_not_installed() -> None:
    with patch("shutil.which", return_value=None):
        with patch("sys.exit") as mock_exit:
            with patch("builtins.print") as mock_print:
                check_omxplayer_installed()
                mock_exit.assert_called_once_with(1)
                mock_print.assert_any_call("❌ Error: omxplayer is not installed.")
                mock_print.assert_any_call(
                    "👉 Install it with: sudo apt install omxplayer"
                )


def test_play_video_loop_keyboard_interrupt() -> None:
    with patch("subprocess.run", side_effect=KeyboardInterrupt):
        with patch("builtins.print") as mock_print:
            play_video_loop()
            mock_print.assert_called_with("\n👋 Exiting...")


def test_play_video_loop_called_process_error() -> None:
    # Error occurs first, followed by a KeyboardInterrupt
    # to exit the loop.
    error = subprocess.CalledProcessError(1, "omxplayer")
    with patch(
        "subprocess.run",
        side_effect=[error, KeyboardInterrupt()],
    ):
        with patch("time.sleep"):
            with patch("builtins.print") as mock_print:
                play_video_loop()
    # Verify error was logged
    mock_print.assert_any_call(f"🔴 Error playing video: {error}")


def test_main_runs_both_checks() -> None:
    with patch("skaven.video_loop.check_omxplayer_installed") as mock_check:
        with patch("skaven.video_loop.play_video_loop") as mock_loop:
            main()
    mock_check.assert_called_once()
    mock_loop.assert_called_once()
