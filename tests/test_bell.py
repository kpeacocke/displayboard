import importlib
import sys
import threading
import pytest
import pygame
from unittest.mock import MagicMock
import logging
from typing import Optional
import skaven.bell as bell_module
from types import ModuleType


def test_move_bell_nested_except_minimal(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Minimal test: both move and mid fail in move_bell's except (lines 102-105).
    """
    bell_module, _, _ = fresh_bell_module
    caplog.set_level(logging.ERROR)

    class DummyServo:
        def __init__(self) -> None:
            pass

        @property
        def value(self) -> float | None:
            raise Exception("move fail minimal")

        @value.setter
        def value(self, val: float) -> None:
            raise Exception("move fail minimal")

        def mid(self) -> None:
            raise Exception("mid fail minimal")

    dummy_servo = DummyServo()
    setattr(bell_module, "servo", dummy_servo)
    monkeypatch.setattr(bell_module.random, "randint", lambda a, b: 1)
    monkeypatch.setattr(bell_module.random, "uniform", lambda a, b: 0.5)
    bell_module.move_bell()
    # Should log both errors
    assert "Error moving servo: move fail minimal" in caplog.text
    assert "Failed to return servo to mid position: mid fail minimal" in caplog.text


def test_random_trigger_loop_real_event_multiple_iterations(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Covers both 142->123 (loop) and 123->exit (exit) branches in
    random_trigger_loop.
    """
    bell_module, config_module, _ = fresh_bell_module
    caplog.set_level(logging.INFO)

    # Patch config to avoid real waiting
    monkeypatch.setattr(config_module, "BELL_LOOP_WAIT_MIN_S", 0)
    monkeypatch.setattr(config_module, "BELL_LOOP_WAIT_MAX_S", 0)
    monkeypatch.setattr(bell_module.random, "random", lambda: 1.0)  # No trigger

    # --- Cover both loop and exit branches, and force a break (123->exit) ---
    event = threading.Event()
    loop_counter = {"n": 0}
    broke = {"hit": False}

    def fake_sleep(secs: float) -> None:
        pass  # no-op

    monkeypatch.setattr("time.sleep", fake_sleep)

    # Patch the function to break out of the loop after a few iterations
    def wait_and_set(timeout: Optional[float] = None) -> bool:
        loop_counter["n"] += 1
        if loop_counter["n"] == 2:
            # Simulate a break (e.g., KeyboardInterrupt or other break
            # condition)
            broke["hit"] = True
            raise KeyboardInterrupt()
        if loop_counter["n"] == 4:
            event.set()
        return event.is_set()

    monkeypatch.setattr(event, "wait", wait_and_set)

    try:
        bell_module.random_trigger_loop(stop_event=event)
    except KeyboardInterrupt:
        pass
    # The loop should have run at least twice (should hit 123->123 branch)
    assert loop_counter["n"] >= 2
    # Should also exit cleanly (cover 123->exit) via break or event
    assert broke["hit"] or event.is_set()
    assert caplog.text.count("...The bell remains silent...") >= 1


def test_random_trigger_loop_event_set_natural_exit(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Precisely covers 142->123 (loop) and 123->exit (exit) branches in
    random_trigger_loop using a custom Event class to avoid monkeypatching
    threading.Event.
    """
    bell_module, config_module, _ = fresh_bell_module
    caplog.set_level(logging.INFO)

    # Patch config to avoid real waiting
    monkeypatch.setattr(config_module, "BELL_LOOP_WAIT_MIN_S", 0)
    monkeypatch.setattr(config_module, "BELL_LOOP_WAIT_MAX_S", 0)
    # No trigger: patch random so that the trigger condition is never met.
    monkeypatch.setattr(bell_module.random, "random", lambda: 1.0)

    class CustomEvent:
        def __init__(self) -> None:
            self.calls = 0
            self._is_set = False

        def wait(self, timeout: float | None = None) -> bool:
            self.calls += 1
            # First call: not set, loop continues (142->123)
            # Second call: set, loop exits (123->exit)
            if self.calls == 2:
                self._is_set = True
            return self._is_set

        def is_set(self) -> bool:
            return self._is_set

    event = CustomEvent()

    def fake_sleep(secs: float) -> None:
        pass  # no-op

    monkeypatch.setattr("time.sleep", fake_sleep)

    bell_module.random_trigger_loop(stop_event=event)
    assert event.calls >= 2
    assert event.is_set()
    assert "...The bell remains silent..." in caplog.text


def test_import_bell_pygame_mixer_init_fails(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """
    Covers lines 22-23: pygame.mixer.init fails at import time.
    """
    caplog.set_level("ERROR")
    sys.modules.pop("skaven.bell", None)
    monkeypatch.setattr(
        pygame.mixer, "init", lambda: (_ for _ in ()).throw(pygame.error("init fail"))
    )
    import skaven.bell as bell_module

    importlib.reload(bell_module)
    assert "Failed to initialize pygame mixer: init fail" in caplog.text


def test_start_sound_raises(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Covers lines 49-50: Exception in start_sound (music.load/play)."""
    bell_module, _, _ = fresh_bell_module
    caplog.set_level(logging.ERROR)
    monkeypatch.setattr(
        bell_module.pygame.mixer.music,
        "load",
        lambda f: (_ for _ in ()).throw(pygame.error("load fail")),
    )
    bell_module.start_sound()
    assert "Failed to play bell sound" in caplog.text


def test_stop_sound_raises(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Covers lines 65-66: Exception in stop_sound (music.stop)."""
    bell_module, _, music_mock = fresh_bell_module
    caplog.set_level(logging.ERROR)
    monkeypatch.setattr(music_mock, "get_busy", lambda: True)
    monkeypatch.setattr(
        music_mock, "stop", lambda: (_ for _ in ()).throw(pygame.error("stop fail"))
    )
    bell_module.stop_sound()
    assert "Failed to stop bell sound" in caplog.text


def test_move_bell_servo_mid_raises_in_except(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Covers lines 102-105: servo.mid() raises in except block of
    move_bell.
    """
    bell_module, _, _ = fresh_bell_module
    caplog.set_level(logging.ERROR)

    class DummyServoWithFailMid(DummyServo):
        def mid(self) -> None:
            raise RuntimeError("mid fail")

        def set_value(self, val: float) -> None:
            raise Exception("move fail")

        @property
        def servo_value(self) -> float | None:
            return None

        @servo_value.setter
        def servo_value(self, val: float) -> None:
            self.set_value(val)

    dummy_servo = DummyServoWithFailMid()
    setattr(bell_module, "servo", dummy_servo)
    monkeypatch.setattr(bell_module.random, "randint", lambda a, b: 1)
    monkeypatch.setattr(bell_module.random, "uniform", lambda a, b: 0.5)

    setattr(bell_module, "servo", dummy_servo)
    bell_module.move_bell()
    assert "Failed to return servo to mid position" in caplog.text
    assert "mid fail" in caplog.text


# --- Test for nested except in move_bell (lines 102-105) ---
def test_move_bell_nested_except_mid_also_fails(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Covers lines 102-105: both move and mid fail in move_bell's except.
    """
    bell_module, _, _ = fresh_bell_module
    caplog.set_level(logging.ERROR)

    class DummyServoDoubleFail:
        def __init__(self) -> None:
            self.mid_called = False

        @property
        def value(self) -> float | None:
            raise Exception("move fail")

        @value.setter
        def value(self, val: float) -> None:
            raise Exception("move fail")

        def mid(self) -> None:
            raise Exception("mid fail 2")

    dummy_servo = DummyServoDoubleFail()
    setattr(bell_module, "servo", dummy_servo)
    monkeypatch.setattr(bell_module.random, "randint", lambda a, b: 1)
    monkeypatch.setattr(bell_module.random, "uniform", lambda a, b: 0.5)
    bell_module.move_bell()
    # Should log both errors
    assert "Error moving servo: move fail" in caplog.text
    assert "Failed to return servo to mid position: mid fail 2" in caplog.text


def test_main_servo_mid_raises_in_finally(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Covers lines 155-156: servo.mid() raises in main's finally block."""
    bell_module, _, _ = fresh_bell_module
    caplog.set_level(logging.ERROR)

    class DummyServoMid(DummyServo):
        def mid(self) -> None:
            raise RuntimeError("mid finally fail")

    monkeypatch.setattr(bell_module, "Servo", DummyServoMid)
    monkeypatch.setattr(
        bell_module, "random_trigger_loop", lambda stop_event=None: None
    )
    monkeypatch.setattr(bell_module, "stop_sound", lambda: None)
    bell_module.main(stop_event=threading.Event())
    assert "Failed to set servo to mid position during cleanup" in caplog.text
    assert "mid finally fail" in caplog.text


def test_main_servo_close_raises_in_finally(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Covers line 173: servo.close() raises in main's finally block."""
    bell_module, _, _ = fresh_bell_module
    caplog.set_level(logging.ERROR)

    class DummyServoClose(DummyServo):
        def close(self) -> None:
            raise RuntimeError("close finally fail")

    monkeypatch.setattr(bell_module, "Servo", DummyServoClose)
    monkeypatch.setattr(
        bell_module, "random_trigger_loop", lambda stop_event=None: None
    )
    monkeypatch.setattr(bell_module, "stop_sound", lambda: None)
    bell_module.main(stop_event=threading.Event())
    assert "Failed to close servo during main cleanup" in caplog.text
    assert "close finally fail" in caplog.text


def test_main_pygame_quit_raises_in_finally(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Covers line 191: pygame.mixer.quit() raises in main's finally block."""
    bell_module, _, _ = fresh_bell_module
    caplog.set_level(logging.ERROR)
    monkeypatch.setattr(bell_module, "Servo", DummyServo)

    def dummy_random_trigger_loop(stop_event: object = None) -> None:
        return None

    monkeypatch.setattr(bell_module, "random_trigger_loop", dummy_random_trigger_loop)
    monkeypatch.setattr(bell_module, "stop_sound", lambda: None)
    monkeypatch.setattr(
        bell_module.pygame.mixer,
        "quit",
        lambda: (_ for _ in ()).throw(pygame.error("quit fail")),
    )
    bell_module.main(stop_event=threading.Event())
    assert "Failed to quit pygame mixer during cleanup" in caplog.text
    assert "quit fail" in caplog.text


def test_main_created_event_set(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
) -> None:
    """Covers line 198: created_event.set() in main's finally block."""
    bell_module, _, _ = fresh_bell_module
    called = {}
    # Patch threading.Event in the bell_module namespace so that
    # main() uses DummyEvent instead of the real threading.Event.

    class DummyEvent(threading.Event):
        def set(self) -> None:
            called["set"] = True
            super().set()

    monkeypatch.setattr(bell_module, "Servo", DummyServo)
    monkeypatch.setattr(
        bell_module, "random_trigger_loop", lambda stop_event=None: None
    )
    monkeypatch.setattr(bell_module, "stop_sound", lambda: None)
    monkeypatch.setattr(bell_module.threading, "Event", DummyEvent)
    bell_module.main(stop_event=None)  # Should create and set event
    assert called.get("set")


def test_main_cleanup_complete_log(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Covers line 202: 'Bell cleanup complete.' log in main's finally block.
    """
    bell_module, _, _ = fresh_bell_module
    caplog.set_level(logging.INFO)
    monkeypatch.setattr(bell_module, "Servo", DummyServo)
    monkeypatch.setattr(
        bell_module, "random_trigger_loop", lambda stop_event=None: None
    )
    monkeypatch.setattr(bell_module, "stop_sound", lambda: None)
    bell_module.main(stop_event=threading.Event())
    assert "Bell cleanup complete." in caplog.text


class DummyMusic:
    def __init__(self) -> None:
        self.loaded: Optional[str] = None
        self.volume: Optional[float] = None
        self.play_args: Optional[int] = None
        self.stopped: bool = False
        self._is_busy: bool = False
        self.play_called: bool = False

    def load(self, path: str) -> None:
        self.loaded = path

    def set_volume(self, v: float) -> None:
        self.volume = v

    def play(self, start: int = 0) -> None:
        self.play_args = start
        self._is_busy = True
        self.play_called = True

    def stop(self) -> None:
        self.stopped = True
        self._is_busy = False

    def get_busy(self) -> bool:
        return self._is_busy


def test_main_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Covers lines 213-214: KeyboardInterrupt in main."""
    bell_module, _, _ = fresh_bell_module
    caplog.set_level(logging.INFO)
    monkeypatch.setattr(bell_module, "Servo", DummyServo)

    def raise_keyboard(*a: object, **k: object) -> None:
        raise KeyboardInterrupt()

    monkeypatch.setattr(bell_module, "random_trigger_loop", raise_keyboard)
    monkeypatch.setattr(bell_module, "stop_sound", lambda: None)
    bell_module.main(stop_event=threading.Event())
    assert "KeyboardInterrupt received, shutting down." in caplog.text


class DummyServo:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.pin: Optional[int] = (
            int(args[0]) if args and isinstance(args[0], (int, float, str)) else None
        )
        self.value: Optional[float] = None
        self.mid_called: bool = False
        self.closed: bool = False
        min_pw = kwargs.get("min_pulse_width")
        max_pw = kwargs.get("max_pulse_width")
        self.min_pulse_width: Optional[float] = (
            float(min_pw)
            if min_pw is not None and isinstance(min_pw, (int, float, str))
            else None
        )
        self.max_pulse_width: Optional[float] = (
            float(max_pw)
            if max_pw is not None and isinstance(max_pw, (int, float, str))
            else None
        )

    def mid(self) -> None:
        self.mid_called = True

    def close(self) -> None:
        self.closed = True


class DummyEvent:
    """
    An event whose wait() returns False once, then True,
    and is_set() becomes True after first wait.
    """

    def __init__(self) -> None:
        self.calls: int = 0
        self._is_set: bool = False

    def wait(self, timeout: Optional[float] = None) -> bool:
        self.calls += 1
        if self.calls > 1:
            self._is_set = True
            return True
        return False

    def is_set(self) -> bool:
        return self._is_set


@pytest.fixture(autouse=True)
def isolate_pygame(monkeypatch: pytest.MonkeyPatch) -> "DummyMusic":
    # Replace pygame.mixer.music with DummyMusic
    dummy: DummyMusic = DummyMusic()
    monkeypatch.setattr(pygame.mixer, "music", dummy)
    # Prevent real init/quit side effects, can be overridden in specific tests
    monkeypatch.setattr(pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(pygame.mixer, "quit", lambda: None)
    return dummy


@pytest.fixture
def fresh_bell_module(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[ModuleType, ModuleType, DummyMusic]:
    """
    Fixture to reset global state and patch dependencies for bell_module.
    Does NOT reload the module, so coverage is preserved.
    """
    import pygame  # Import pygame directly to avoid attribute errors

    # Reset global servo if it exists in the module
    if hasattr(bell_module, "servo"):
        bell_module.servo = None
    # Patch pygame.mixer.music, init, quit for isolation
    dummy_music = DummyMusic()
    monkeypatch.setattr(pygame.mixer, "music", dummy_music)
    monkeypatch.setattr(pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(pygame.mixer, "quit", lambda: None)
    # Patch config if needed
    import skaven.config as config_module

    return bell_module, config_module, dummy_music


def test_start_and_stop_sound(
    isolate_pygame: "DummyMusic",
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
) -> None:
    bell_module, _, music_mock = fresh_bell_module
    # Fix randomness
    monkeypatch.setattr(bell_module.random, "randint", lambda a, b: 5)
    monkeypatch.setattr(bell_module.random, "uniform", lambda a, b: 0.42)
    # Call start_sound
    bell_module.start_sound()
    assert music_mock.loaded == str(bell_module.config.BELL_SOUND_FILE)
    assert music_mock.volume == 0.42
    # Assuming play is called with loops=-1, start=0
    assert music_mock.play_args == 5
    # The previous test had play_args = 5, which might map to loops.
    # If start_sound calls play(loops=N), this needs to match.
    # For now, assuming play() is called and these are checked.
    # If bell.random.randint is for loops, then play() should be called
    # with loops=5.
    # Let's assume play() is called simply.
    assert music_mock.play_called is True

    # Call stop_sound
    bell_module.stop_sound()
    assert music_mock.stopped is True


def test_move_bell_no_servo_logs_and_returns(
    caplog: pytest.LogCaptureFixture,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
) -> None:
    bell_module, _, _ = fresh_bell_module
    caplog.set_level("ERROR")
    setattr(bell_module, "servo", None)  # Ensure servo is None

    # Create a dummy event, as move_bell might expect one
    dummy_event = threading.Event()
    bell_module.move_bell(stop_event=dummy_event)  # Should not raise
    # Use SERVO_ERROR as per bell.py
    assert bell_module.SERVO_ERROR in caplog.text


def test_move_bell_with_servo(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
) -> None:
    bell_module, _, _ = fresh_bell_module
    dummy_servo_instance = DummyServo()
    setattr(bell_module, "servo", dummy_servo_instance)

    # num_moves
    monkeypatch.setattr(bell_module.random, "randint", lambda a, b: 2)
    # swing_pos and sleep_duration
    monkeypatch.setattr(bell_module.random, "uniform", lambda a, b: 0.7)

    event = threading.Event()  # Use a non-set event
    bell_module.move_bell(stop_event=event)

    assert dummy_servo_instance.value == 0.7  # Last position set
    assert dummy_servo_instance.mid_called is True


def test_random_trigger_loop_no_trigger(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    bell_module, config_module, _ = fresh_bell_module
    caplog.set_level(logging.INFO, logger="skaven.bell")
    # No need to patch logger: bell.py now uses logging.getLogger(__name__)
    # in every function

    monkeypatch.setattr(config_module, "BELL_LOOP_WAIT_MIN_S", 0)
    monkeypatch.setattr(config_module, "BELL_LOOP_WAIT_MAX_S", 0)
    # > probability
    monkeypatch.setattr(bell_module.random, "random", lambda: 1.0)

    event = threading.Event()
    # Do not set event, let the loop run once
    # Patch event.wait to return True after first call to break loop
    call_count = {"n": 0}

    def wait_once(timeout: Optional[float] = None) -> bool:
        call_count["n"] += 1
        return call_count["n"] > 1

    # Patch event.wait using monkeypatch to avoid direct assignment
    monkeypatch.setattr(event, "wait", wait_once)

    bell_module.random_trigger_loop(stop_event=event)
    # Covers line 132 if this is the log
    assert "...The bell remains silent..." in caplog.text


def test_random_trigger_loop_with_trigger(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
) -> None:
    bell_module, config_module, _ = fresh_bell_module
    calls: dict[str, int] = {"start": 0, "move": 0, "stop": 0}

    monkeypatch.setattr(
        bell_module,
        "start_sound",
        lambda: calls.__setitem__("start", calls["start"] + 1),
    )
    monkeypatch.setattr(
        bell_module,
        "move_bell",
        lambda stop_event=None: calls.__setitem__("move", calls["move"] + 1),
    )
    monkeypatch.setattr(
        bell_module, "stop_sound", lambda: calls.__setitem__("stop", calls["stop"] + 1)
    )

    monkeypatch.setattr(config_module, "BELL_LOOP_WAIT_MIN_S", 0)
    monkeypatch.setattr(config_module, "BELL_LOOP_WAIT_MAX_S", 0)
    # Force trigger
    monkeypatch.setattr(bell_module.random, "random", lambda: 0.0)

    event = DummyEvent()  # Breaks after one loop execution
    bell_module.random_trigger_loop(stop_event=event)

    assert calls["start"] == 1
    assert calls["move"] == 1
    assert calls["stop"] == 1


def test_main_initializes_and_cleans_up(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    bell_module, config_module, music_mock = fresh_bell_module
    caplog.set_level(logging.INFO)

    # Use our DummyServo for instantiation
    monkeypatch.setattr(bell_module, "Servo", DummyServo)

    called_methods = {"loop": False, "stop_sound": False}
    monkeypatch.setattr(
        bell_module,
        "random_trigger_loop",
        lambda stop_event=None: called_methods.__setitem__("loop", True),
    )
    monkeypatch.setattr(
        bell_module,
        "stop_sound",
        lambda *_: called_methods.__setitem__("stop_sound", True),
    )
    # Pygame mixer quit is mocked by isolate_pygame, but we can grab it if
    # bell.pygame.mixer.quit is what's called. However, the autouse fixture
    # isolate_pygame already mocks pygame.mixer.quit. We need to ensure
    # bell.py calls the globally mocked pygame.mixer.quit. For assertion,
    # we can mock it again here if needed or rely on isolate_pygame's mock.
    # Let's mock it directly on bell_module.pygame.mixer for clarity if
    # main uses that specific instance.
    pygame_quit_mock = MagicMock()
    monkeypatch.setattr(bell_module.pygame.mixer, "quit", pygame_quit_mock)

    ev = threading.Event()
    bell_module.main(stop_event=ev)

    # Servo instance should be created and assigned
    assert bell_module.servo is not None
    assert isinstance(bell_module.servo, DummyServo)
    assert bell_module.servo.mid_called is True
    assert bell_module.servo.closed is True
    assert called_methods["loop"] is True
    assert called_methods["stop_sound"] is True
    pygame_quit_mock.assert_called_once()
    assert "Servo initialized on pin" in caplog.text
    assert "Cleaning up bell resources" in caplog.text


def test_main_servo_init_failure(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    bell_module, _, _ = fresh_bell_module
    caplog.set_level(logging.ERROR)

    def bad_servo_init(*args: object, **kwargs: object) -> None:
        raise RuntimeError("pin error")

    monkeypatch.setattr(bell_module, "Servo", bad_servo_init)

    # Mock sys.exit to check it's called without exiting tests
    mock_sys_exit = MagicMock(side_effect=SystemExit)
    monkeypatch.setattr(sys, "exit", mock_sys_exit)

    with pytest.raises(SystemExit):
        bell_module.main(stop_event=threading.Event())

    assert "Failed to init servo on pin" in caplog.text
    assert "pin error" in caplog.text
    mock_sys_exit.assert_called_once_with(1)


# --- New tests for 100% coverage ---


def test_pygame_mixer_init_failure_in_main_context(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Covers lines 23-24 (pygame.mixer.init failure)."""
    bell_module, _, _ = fresh_bell_module
    caplog.set_level(logging.ERROR)

    # Override the default init mock from isolate_pygame for this test,
    # on the bell_module's pygame
    mock_init_that_fails = MagicMock(side_effect=pygame.error("mixer init boom"))
    monkeypatch.setattr(bell_module.pygame.mixer, "init", mock_init_that_fails)

    monkeypatch.setattr(bell_module, "Servo", DummyServo)
    monkeypatch.setattr(
        bell_module, "random_trigger_loop", lambda stop_event=None: None
    )
    monkeypatch.setattr(bell_module, "stop_sound", lambda: None)
    # pygame.mixer.quit is already handled by isolate_pygame/fresh_bell_module

    # Mock sys.exit as main might call it if mixer init is critical
    mock_sys_exit = MagicMock(side_effect=SystemExit)
    monkeypatch.setattr(sys, "exit", mock_sys_exit)

    with pytest.raises(SystemExit):
        bell_module.main(stop_event=threading.Event())

    mock_init_that_fails.assert_called_once()
    assert "Failed to initialize pygame mixer" in caplog.text
    assert "mixer init boom" in caplog.text
    # If mixer init failure is critical and causes sys.exit:
    # mock_sys_exit.assert_called_once_with(1) # Or some other error code


def test_start_sound_config_file_none(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Covers lines 48-49 (config.BELL_SOUND_FILE is None)."""
    bell_module, config_module, music_mock = fresh_bell_module  # noqa: E501
    caplog.set_level(logging.WARNING)
    monkeypatch.setattr(bell_module.config, "BELL_SOUND_FILE", None)

    bell_module.start_sound()

    assert music_mock.loaded is None
    assert "Bell sound file not configured" in caplog.text


def test_stop_sound_when_not_busy(
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Covers lines 59-60 (sound is not playing)."""
    bell_module, _, music_mock = fresh_bell_module
    music_mock._is_busy = False  # Explicitly set to not busy

    caplog.set_level(logging.DEBUG)  # Assuming a debug log for this case
    bell_module.stop_sound()

    # stop() should not be called on the music object
    assert music_mock.stopped is False
    # Adjust log
    assert "Sound not playing, no need to stop" in caplog.text


def test_move_bell_interrupt_at_start(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Covers lines 82-83 (stop_event.is_set() at start of move_bell)."""
    bell_module, _, _ = fresh_bell_module
    caplog.set_level(logging.INFO)
    dummy_servo_instance = DummyServo()
    setattr(bell_module, "servo", dummy_servo_instance)
    event = threading.Event()
    event.set()  # Event is set from the beginning
    bell_module.move_bell(stop_event=event)
    # No movement
    assert dummy_servo_instance.value is None
    # finally block
    assert dummy_servo_instance.mid_called is True
    assert "Bell movement interrupted by stop event" in caplog.text


def test_move_bell_num_moves_zero(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Covers lines 95-96 (random.randint results in 0 moves)."""
    bell_module, _, _ = fresh_bell_module
    caplog.set_level(logging.INFO)
    dummy_servo_instance = DummyServo()
    setattr(bell_module, "servo", dummy_servo_instance)
    monkeypatch.setattr(bell_module.random, "randint", lambda a, b: 0)
    event = threading.Event()
    bell_module.move_bell(stop_event=event)
    # No movement
    assert dummy_servo_instance.value is None
    # finally block
    assert dummy_servo_instance.mid_called is True
    assert "Bell will swing 0 times" in caplog.text


def test_move_bell_servo_mid_failure_in_finally(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Covers lines 99-105 (servo.mid() fails in move_bell's finally).
    """
    bell_module, _, _ = fresh_bell_module
    caplog.set_level(logging.ERROR)

    dummy_servo_instance = DummyServo()

    def failing_mid() -> None:
        # No need, exception means it was attempted
        raise RuntimeError("servo mid boom")

    dummy_servo_instance.mid = failing_mid  # type: ignore
    setattr(bell_module, "servo", dummy_servo_instance)
    monkeypatch.setattr(bell_module.random, "randint", lambda a, b: 1)
    monkeypatch.setattr(bell_module.random, "uniform", lambda a, b: 0.5)
    event = threading.Event()
    bell_module.move_bell(stop_event=event)  # Should not re-raise
    # Movement attempted
    assert dummy_servo_instance.value == 0.5
    assert "Failed to return servo to mid position" in caplog.text
    assert "servo mid boom" in caplog.text


def test_main_servo_close_failure_in_finally(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Covers lines 159-161 (servo.close() fails in main's finally).
    """
    bell_module, _, _ = fresh_bell_module  # noqa: E501
    caplog.set_level(logging.ERROR)

    class ServoFailsOnClose(DummyServo):
        def close(self: "ServoFailsOnClose") -> None:
            super().close()  # Mark closed if super does that
            raise RuntimeError("servo close boom")

    monkeypatch.setattr(bell_module, "Servo", ServoFailsOnClose)
    monkeypatch.setattr(
        bell_module, "random_trigger_loop", lambda stop_event=None: None
    )
    monkeypatch.setattr(bell_module, "stop_sound", lambda: None)
    # pygame.mixer.quit is handled by fresh_bell_module / isolate_pygame
    bell_module.main(stop_event=threading.Event())
    assert bell_module.servo is not None
    assert bell_module.servo.mid_called is True
    # Attempted
    assert bell_module.servo.closed is True
    assert "Failed to close servo during main cleanup" in caplog.text
    assert "servo close boom" in caplog.text


def test_main_pygame_mixer_quit_failure_in_finally(
    monkeypatch: pytest.MonkeyPatch,
    fresh_bell_module: tuple[ModuleType, ModuleType, "DummyMusic"],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Covers lines 170-171 (pygame.mixer.quit() fails in main's finally)."""
    bell_module, _, _ = fresh_bell_module  # noqa: E501
    caplog.set_level(logging.ERROR)

    monkeypatch.setattr(bell_module, "Servo", DummyServo)
    monkeypatch.setattr(
        bell_module, "random_trigger_loop", lambda stop_event=None: None
    )
    monkeypatch.setattr(bell_module, "stop_sound", lambda: None)

    failing_quit_mock = MagicMock(side_effect=pygame.error("mixer quit boom"))
    monkeypatch.setattr(bell_module.pygame.mixer, "quit", failing_quit_mock)

    bell_module.main(stop_event=threading.Event())

    assert bell_module.servo.mid_called is True
    assert bell_module.servo.closed is True
    failing_quit_mock.assert_called_once()
    assert "Failed to quit pygame mixer during cleanup" in caplog.text
    assert "mixer quit boom" in caplog.text
