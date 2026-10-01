from typing import Optional
import sys
import os
import types
import pytest
import threading
import time
import random
from typing import Any, Callable, Union

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


class DummyServo:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.mid_called = False
        self.closed = False
        self.detach_called = False
        self.history: list[Any] = []
        self._value: Union[float, None] = (
            None  # Replace `float | None` with `Union[float, None]`
        )

    @property
    def value(
        self,
    ) -> Union[float, None]:  # Replace `float | None` with `Union[float, None]`
        return self._value

    @value.setter
    def value(
        self, val: Union[float, None]
    ) -> None:  # Replace `float | None` with `Union[float, None]`
        self._value = val

    def mid(self) -> None:
        self.mid_called = True

    def close(self) -> None:
        self.closed = True

    def detach(self) -> None:
        self.detach_called = True

    def __call__(self, angle: float) -> None:
        self.value = angle
        self.history.append(angle)


# --- Specialized DummyServo subclasses for error simulation in tests ---
class DummyServoMinimal(DummyServo):
    def __init__(self) -> None:
        # Do not call super().__init__() to avoid setting self.value
        self.mid_called = False
        self.closed = False
        self.detach_called = False
        self.history = []

    @property
    def value(self) -> Optional[float]:
        raise Exception("move fail minimal")

    @value.setter
    def value(self, val: Optional[float]) -> None:
        raise Exception("move fail minimal")

    def mid(self) -> None:
        raise Exception("mid fail minimal")


class DummyServoWithFailMid(DummyServo):
    def __init__(self) -> None:
        # Do not call super().__init__() to avoid setting self.value
        self.mid_called = False
        self.closed = False
        self.detach_called = False
        self.history = []

    def mid(self) -> None:
        raise RuntimeError("mid fail")

    @property
    def value(self) -> Optional[float]:
        raise Exception("move fail")

    @value.setter
    def value(self, val: Optional[float]) -> None:
        raise Exception("move fail")


class DummyServoDoubleFail(DummyServo):
    def __init__(self) -> None:
        # Do not call super().__init__() to avoid setting self.value
        self.mid_called = False
        self.closed = False
        self.detach_called = False
        self.history = []

    @property
    def value(self) -> Optional[float]:
        raise Exception("move fail")

    @value.setter
    def value(self, val: Optional[float]) -> None:
        raise Exception("move fail")

    def mid(self) -> None:
        raise Exception("mid fail 2")


class DummyServoMid(DummyServo):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.mid_called = False
        self.closed = False

    def mid(self) -> None:
        self.mid_called = True
        raise RuntimeError("mid finally fail")


class DummyServoClose(DummyServo):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.mid_called = False
        self.closed = False

    def close(self) -> None:
        self.closed = True
        raise RuntimeError("close finally fail")


class ServoFailsOnClose(DummyServo):

    def close(self) -> None:
        self.closed = True
        raise RuntimeError("servo close boom")


# Inject a dummy gpiozero module so bell.py always sees DummyServo
_gpiozero_stub = types.ModuleType("gpiozero")
setattr(_gpiozero_stub, "Servo", DummyServo)
sys.modules["gpiozero"] = _gpiozero_stub


# This fixture is now a no-op, but kept for test compatibility
@pytest.fixture
def mock_servo() -> type:
    """Returns the DummyServo class used for all Servo references in tests."""
    return DummyServo


@pytest.fixture(autouse=False)
def dummy_event() -> threading.Event:
    """
    Returns a dummy threading.Event with controllable .wait() and .is_set().
    Usage: pass as stop_event or patch in tests for deterministic control.
    """

    class DummyEvent(threading.Event):
        def __init__(self) -> None:
            super().__init__()
            self._is_set = False
            self.wait_calls = 0
            self.wait_return_value = False  # Set to True to break loops

        def set(self) -> None:
            self._is_set = True

        def is_set(self) -> bool:
            return self._is_set

        def wait(self, timeout: Optional[float] = None) -> bool:
            self.wait_calls += 1
            return self.wait_return_value

        def clear(self) -> None:
            self._is_set = False

    return DummyEvent()


@pytest.fixture(autouse=True)
def patch_time_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(time, "sleep", lambda s: None)


# Patch random functions for deterministic tests
@pytest.fixture(autouse=True)
def patch_random(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(random, "uniform", lambda a, b: a)
    monkeypatch.setattr(random, "randint", lambda a, b: a)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0] if seq else None)
    monkeypatch.setattr(random, "sample", lambda pop, k: list(pop[:k]))
    monkeypatch.setattr(random, "random", lambda: 0.5)


@pytest.fixture(autouse=True)
def patch_displayboard_bell_servo(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Ensure displayboard.bell.Servo is always DummyServo and clear any existing servo.
    This prevents real hardware instantiation in any test.
    """
    import displayboard.bell as bell

    # Override Servo class to DummyServo
    monkeypatch.setattr(bell, "Servo", DummyServo)
    # Do NOT reset bell.servo here; allow tests to set their own dummy instance


# --- gpiozero LED/Button and NeoPixel/board pin fixtures ---


# Mock gpiozero.LED and gpiozero.Button everywhere
@pytest.fixture(autouse=False)
def mock_led_button(monkeypatch: pytest.MonkeyPatch) -> tuple[type, type]:

    class DummyLED:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.is_lit = False

        def on(self) -> None:
            self.is_lit = True

        def off(self) -> None:
            self.is_lit = False

    class DummyButton:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.pressed = False

        def when_pressed(self, fn: Callable[[], None]) -> None:
            self._when_pressed = fn

        def press(self) -> None:
            self.pressed = True
            if hasattr(self, "_when_pressed"):
                self._when_pressed()

    monkeypatch.setattr("displayboard.board.LED", DummyLED, raising=False)
    monkeypatch.setattr("displayboard.board.Button", DummyButton, raising=False)
    monkeypatch.setattr("displayboard.lighting.LED", DummyLED, raising=False)
    monkeypatch.setattr("displayboard.lighting.Button", DummyButton, raising=False)
    return DummyLED, DummyButton


# Mock NeoPixel/LED strip class
@pytest.fixture(autouse=False)
def mock_neopixel(monkeypatch: pytest.MonkeyPatch) -> type:

    class DummyNeoPixel:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self._pixels: list[object] = []
            self._last_fill: object = None
            self._last_show: bool = False

        def show(self) -> None:
            self._last_show = True

        def fill(self, color: object) -> None:
            self._last_fill = color

        def __setitem__(self, idx: int, val: object) -> None:
            if len(self._pixels) <= idx:
                self._pixels.extend([None] * (idx + 1 - len(self._pixels)))
            self._pixels[idx] = val

        def __getitem__(self, idx: int) -> object:
            return self._pixels[idx]

    monkeypatch.setattr("displayboard.neopixel.NeoPixel", DummyNeoPixel, raising=False)
    return DummyNeoPixel


# Mock board pin constants (e.g., board.D18)
@pytest.fixture(autouse=False)
def mock_board_pins(monkeypatch: pytest.MonkeyPatch) -> object:
    import types
    import displayboard.board

    dummy_board = types.SimpleNamespace(D18=18, D21=21, D12=12, D13=13)
    monkeypatch.setattr(displayboard.board, "D18", 18, raising=False)
    monkeypatch.setattr(displayboard.board, "D21", 21, raising=False)
    monkeypatch.setattr(displayboard.board, "D12", 12, raising=False)
    monkeypatch.setattr(displayboard.board, "D13", 13, raising=False)
    return dummy_board


# Fixture to mock pygame everywhere it's imported, with realistic mixer behavior
@pytest.fixture(autouse=False)
def mock_pygame(monkeypatch: pytest.MonkeyPatch) -> object:
    from types import SimpleNamespace

    # Use a static dict to avoid infinite test loops from repeated creation
    channel_mocks = {}
    sound_mocks = {}

    from unittest.mock import MagicMock

    def sound_factory(path: object) -> MagicMock:
        if path not in sound_mocks:
            m = MagicMock()
            m.set_volume = MagicMock()
            m.get_length.return_value = 0.01
            m.play = MagicMock()
            m._fake_path = path
            sound_mocks[path] = m
        return sound_mocks[path]

    def channel_factory(i: int) -> MagicMock:
        if i not in channel_mocks:
            chan = MagicMock()
            chan.set_volume = MagicMock()
            chan.play = MagicMock()
            chan.fadeout = MagicMock()
            chan._channel_id = i
            channel_mocks[i] = chan
        return channel_mocks[i]

    mixer = SimpleNamespace(
        init=MagicMock(),
        set_num_channels=MagicMock(),
        set_reserved=MagicMock(),
        quit=MagicMock(),
        Sound=sound_factory,
        Channel=channel_factory,
        find_channel=MagicMock(return_value=channel_factory(0)),
    )

    class FakePygameError(Exception):
        pass

    mock_pygame_mod = SimpleNamespace(
        mixer=mixer,
        error=FakePygameError,
        init=MagicMock(),
    )
    monkeypatch.setattr("displayboard.bell.pygame", mock_pygame_mod)
    monkeypatch.setattr("displayboard.sounds.pygame", mock_pygame_mod)
    return mock_pygame_mod
