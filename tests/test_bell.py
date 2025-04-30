import itertools
import importlib
import pygame
import pytest
from pytest import MonkeyPatch, CaptureFixture
from typing import Any
from unittest.mock import patch, MagicMock

import skaven_soundscape.bell as bell
from skaven_soundscape.bell import (
    start_sound,
    stop_sound,
    move_bell,
    random_trigger_loop,
)


@patch("skaven_soundscape.bell.pygame.mixer.music.play")
@patch("skaven_soundscape.bell.pygame.mixer.music.set_volume")
@patch("skaven_soundscape.bell.pygame.mixer.music.load")
@patch("skaven_soundscape.bell.random.randint")
@patch("skaven_soundscape.bell.random.uniform")
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


@patch("skaven_soundscape.bell.pygame.mixer.music.stop")
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


@patch("skaven_soundscape.bell.servo")
@patch("skaven_soundscape.bell.random.uniform")
@patch("skaven_soundscape.bell.random.randint")
@patch("skaven_soundscape.bell.sleep")
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


@patch("skaven_soundscape.bell.start_sound")
@patch("skaven_soundscape.bell.move_bell")
@patch("skaven_soundscape.bell.stop_sound")
@patch("skaven_soundscape.bell.random.uniform")
@patch("skaven_soundscape.bell.random.random")
@patch("skaven_soundscape.bell.sleep")
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


@patch("skaven_soundscape.bell.start_sound")
@patch("skaven_soundscape.bell.move_bell")
@patch("skaven_soundscape.bell.stop_sound")
@patch("skaven_soundscape.bell.random.uniform")
@patch("skaven_soundscape.bell.random.random")
@patch("skaven_soundscape.bell.sleep")
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
    def raise_interrupt() -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(bell, "random_trigger_loop", raise_interrupt)

    servo_mock = MagicMock()
    monkeypatch.setattr(bell, "servo", servo_mock)

    bell.main()

    servo_mock.mid.assert_called_once()
    captured = capfd.readouterr()
    assert "🛑 Exiting... setting bell to neutral." in captured.out


def test_mixer_init_success(monkeypatch: pytest.MonkeyPatch) -> None:
    # Simulate successful mixer init and reload module
    called: list[bool] = []

    def fake_init() -> None:
        called.append(True)

    monkeypatch.setattr(pygame.mixer, "init", fake_init)
    # Reload bell module to trigger init
    import skaven_soundscape.bell as bell_mod

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
