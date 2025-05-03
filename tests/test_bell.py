import itertools
import importlib
import pygame
import pytest
from pytest import MonkeyPatch, CaptureFixture
from typing import Any
from unittest.mock import patch, MagicMock

import skaven.bell as bell
from skaven.bell import (
    start_sound,
    stop_sound,
    move_bell,
    random_trigger_loop,
)


@patch("skaven.bell.pygame.mixer.music.play")
@patch("skaven.bell.pygame.mixer.music.set_volume")
@patch("skaven.bell.pygame.mixer.music.load")
@patch("skaven.bell.random.randint")
@patch("skaven.bell.random.uniform")
def test_start_sound(
    mock_uniform: MagicMock,
    mock_randint: MagicMock,
    mock_load: MagicMock,
    mock_set_volume: MagicMock,
    mock_play: MagicMock,
) -> None:
    mock_randint.return_value = 45
    mock_uniform.return_value = 0.75

    start_sound()

    mock_randint.assert_called_once_with(0, 90)
    mock_uniform.assert_called_once_with(0.3, 1.0)
    # Should load the configured sound file
    mock_load.assert_called_once_with(bell.sound_file)
    mock_set_volume.assert_called_once_with(0.75)
    mock_play.assert_called_once_with(start=45)


@patch("skaven.bell.pygame.mixer.music.stop")
def test_stop_sound(
    mock_stop: MagicMock,
    capsys: CaptureFixture[str],
) -> None:
    # Act: stop the sound
    stop_sound()

    # Assert music stopped and message printed
    mock_stop.assert_called_once()
    captured = capsys.readouterr()
    assert "🔇 Sound stopped." in captured.out


@patch("skaven.bell.servo")
@patch("skaven.bell.random.uniform")
@patch("skaven.bell.random.randint")
@patch("skaven.bell.sleep")
def test_move_bell(
    mock_sleep: MagicMock,
    mock_randint: MagicMock,
    mock_uniform: MagicMock,
    mock_servo: MagicMock,
) -> None:
    mock_randint.return_value = 3
    mock_uniform.side_effect = [-0.5, 0.5, -1.0, 0.3, 0.7, -0.2]

    move_bell()

    assert mock_randint.called
    assert mock_servo.mid.called
    assert mock_sleep.call_count == 3


@patch("skaven.bell.servo")
@patch("skaven.bell.random.randint")
@patch("builtins.print")
def test_move_bell_print(
    mock_print: MagicMock, mock_randint: MagicMock, mock_servo: MagicMock
) -> None:
    mock_randint.return_value = 3
    move_bell()
    mock_print.assert_any_call("🔔 Bell will swing 3 times.")


@patch("skaven.bell.start_sound")
@patch("skaven.bell.move_bell")
@patch("skaven.bell.stop_sound")
@patch("skaven.bell.random.uniform")
@patch("skaven.bell.random.random")
@patch("skaven.bell.sleep")
def test_random_trigger_loop(
    mock_sleep: MagicMock,
    mock_random: MagicMock,
    mock_uniform: MagicMock,
    mock_stop_sound: MagicMock,
    mock_move_bell: MagicMock,
    mock_start_sound: MagicMock,
) -> None:
    mock_uniform.side_effect = [15, 25, 35]
    mock_random.side_effect = itertools.cycle([0.7, 0.9])
    mock_sleep.side_effect = [None, KeyboardInterrupt()]

    with patch("builtins.print"):
        with pytest.raises(KeyboardInterrupt):
            random_trigger_loop()

    mock_start_sound.assert_called_once()
    mock_move_bell.assert_called_once()
    mock_stop_sound.assert_called_once()


@patch("skaven.bell.random.uniform")
@patch("builtins.print")
def test_random_trigger_loop_print(
    mock_print: MagicMock, mock_uniform: MagicMock
) -> None:
    mock_uniform.return_value = 15
    with patch("skaven.bell.sleep", side_effect=KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            random_trigger_loop()
    mock_print.assert_any_call("⏳ Waiting 15.0 seconds...")


@patch("skaven.bell.start_sound")
@patch("skaven.bell.move_bell")
@patch("skaven.bell.stop_sound")
@patch("skaven.bell.random.uniform")
@patch("skaven.bell.random.random")
@patch("skaven.bell.sleep")
def test_random_not_trigger_loop(
    mock_sleep: MagicMock,
    mock_random: MagicMock,
    mock_uniform: MagicMock,
    mock_stop_sound: MagicMock,
    mock_move_bell: MagicMock,
    mock_start_sound: MagicMock,
) -> None:
    mock_uniform.return_value = 12
    mock_random.return_value = 0.9
    mock_sleep.side_effect = [None, KeyboardInterrupt()]

    with patch("builtins.print") as mock_print:
        with pytest.raises(KeyboardInterrupt):
            random_trigger_loop()

    mock_start_sound.assert_not_called()
    mock_move_bell.assert_not_called()
    mock_stop_sound.assert_not_called()
    mock_print.assert_any_call("...The bell remains silent...")


def test_main_keyboard_interrupt(
    monkeypatch: MonkeyPatch,
    capfd: CaptureFixture[str],
) -> None:
    # Mock gpiozero pin factory to avoid hardware dependency
    monkeypatch.setattr("gpiozero.devices.Device.pin_factory", MagicMock())

    def raise_interrupt() -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(bell, "random_trigger_loop", raise_interrupt)

    servo_mock = MagicMock()
    monkeypatch.setattr(bell, "servo", servo_mock)

    bell.main()

    servo_mock.mid.assert_called_once()
    captured = capfd.readouterr()
    assert "🛑 Exiting... setting bell to neutral." in captured.out


@patch("skaven.bell.servo")
@patch("skaven.bell.stop_sound")
@patch("skaven.bell.random_trigger_loop", side_effect=KeyboardInterrupt)
def test_main_exception_handling(
    mock_random_trigger_loop: MagicMock,
    mock_stop_sound: MagicMock,
    mock_servo: MagicMock,
) -> None:
    mock_servo.mid.side_effect = Exception("Servo error")
    with patch("builtins.print") as mock_print:
        bell.main()
    mock_stop_sound.assert_called_once()
    mock_print.assert_any_call("🛑 Exiting... setting bell to neutral.")


def test_mixer_init_success(monkeypatch: pytest.MonkeyPatch) -> None:
    # Simulate successful mixer init and reload module
    called: list[bool] = []

    def fake_init() -> None:
        called.append(True)

    monkeypatch.setattr(pygame.mixer, "init", fake_init)
    # Reload bell module to trigger init
    import skaven.bell as bell_mod

    importlib.reload(bell_mod)
    assert called, "pygame.mixer.init was not called on reload"


def test_mixer_init_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    # Simulate mixer.init raising pygame.error to hit exception handler
    def raise_error() -> None:
        raise pygame.error("init failed")

    monkeypatch.setattr(pygame.mixer, "init", raise_error)
    # Reload module to execute init block
    bell_mod = importlib.reload(bell)
    # Ensure module loaded and sound_file still available
    assert hasattr(bell_mod, "sound_file")


# Stub pygame mixer and music methods for all tests
@pytest.fixture(autouse=True)
def dummy_mixer_init(monkeypatch: MonkeyPatch) -> None:
    def _noop(*args: Any, **kwargs: Any) -> None:
        """No-op stub for pygame mixer methods."""
        pass

    # Stub mixer init and music methods
    monkeypatch.setattr(pygame.mixer, "init", _noop)
    monkeypatch.setattr(pygame.mixer.music, "stop", _noop)
    monkeypatch.setattr(pygame.mixer.music, "load", _noop)
    monkeypatch.setattr(pygame.mixer.music, "set_volume", _noop)
    monkeypatch.setattr(pygame.mixer.music, "play", _noop)


@patch("skaven.bell.servo", None)
def test_move_bell_runtime_error() -> None:
    with pytest.raises(RuntimeError, match="Servo not initialized. Check setup."):
        move_bell()


# Test that main initializes servo when None and exits on KeyboardInterrupt.
def test_main_initializes_servo_and_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    import skaven.bell as bell_module

    # Ensure servo is None
    monkeypatch.setattr(bell_module, "servo", None)
    # Mock Servo constructor to return MagicMock
    mock_servo = MagicMock()
    monkeypatch.setattr(bell_module, "Servo", lambda *a, **k: mock_servo)
    # Patch random_trigger_loop to immediately raise KeyboardInterrupt
    monkeypatch.setattr(
        bell_module,
        "random_trigger_loop",
        lambda: (_ for _ in ()).throw(KeyboardInterrupt()),
    )
    # Capture prints
    with patch("builtins.print") as mock_print:
        bell_module.main()
    # Servo should be set and mid called
    assert bell_module.servo is mock_servo
    mock_servo.mid.assert_called_once()
    mock_print.assert_any_call("🛑 Exiting... setting bell to neutral.")


def test_wait_print_direct(capsys: CaptureFixture[str]) -> None:
    """
    Direct test of random_trigger_loop prints waiting time and then exits.
    """
    import random

    def mock_uniform(a: float, b: float) -> float:
        return 12.3

    def mock_sleep(t: float) -> None:
        raise KeyboardInterrupt

    random.uniform = mock_uniform
    with patch("skaven.bell.sleep", mock_sleep):
        with pytest.raises(KeyboardInterrupt):
            random_trigger_loop()

    captured = capsys.readouterr()
    assert "⏳ Waiting 12.3 seconds..." in captured.out


@patch("skaven.bell.random.uniform")
@patch("builtins.print")
def test_random_trigger_loop_wait_time(
    mock_print: MagicMock, mock_uniform: MagicMock
) -> None:
    mock_uniform.return_value = 15
    with patch("skaven.bell.sleep", side_effect=KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            random_trigger_loop()
    mock_print.assert_any_call("⏳ Waiting 15.0 seconds...")


def test_random_wait_time_in_output(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Ensure the waiting time print in random_trigger_loop appears in stdout.
    """
    # Force a specific wait_time
    monkeypatch.setattr("skaven.bell.random.uniform", lambda a, b: 20.4)

    # Stop after first sleep
    def stop_sleep(t: float) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr("skaven.bell.sleep", stop_sleep)
    with pytest.raises(KeyboardInterrupt):
        random_trigger_loop()

    captured = capsys.readouterr()
    assert "⏳ Waiting 20.4 seconds..." in captured.out


def test_script_entry_point(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test running bell.py as a script with KeyboardInterrupt.
    """
    # Mock gpiozero pin factory to avoid hardware dependency
    monkeypatch.setattr("gpiozero.devices.Device.pin_factory", MagicMock())
    # Use mock pin factory to avoid gpiozero trying to connect to pigpio
    monkeypatch.setenv("GPIOZERO_PIN_FACTORY", "mock")
    # Mock Servo constructor to return a MagicMock
    mock_servo = MagicMock()
    mock_servo._value = 0.0  # Simulate the `value` attribute

    def get_value(self: MagicMock) -> float:
        return float(self._value)

    def set_value(self: MagicMock, val: float) -> None:
        if val is not None and not (-1 <= val <= 1):
            raise ValueError("Servo value must be between -1 and 1, or None")
        self._value = val

    type(mock_servo).value = property(get_value, set_value)
    monkeypatch.setattr("skaven.bell.Servo", lambda *args, **kwargs: mock_servo)

    # Mock random_trigger_loop to immediately raise KeyboardInterrupt
    def mock_random_trigger_loop() -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr("skaven.bell.random_trigger_loop", mock_random_trigger_loop)

    # Call main() to trigger our patched random_trigger_loop and handle exit
    with patch("builtins.print") as mock_print:
        bell.main()
    # After completion, servo.mid() should be called and exit printed
    mock_servo.mid.assert_called_once()
    mock_print.assert_any_call("🛑 Exiting... setting bell to neutral.")
