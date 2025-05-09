import threading
import sys
import importlib
import types
from unittest.mock import patch, MagicMock
from typing import Generator
from _pytest.monkeypatch import MonkeyPatch


def test_skaven_flicker_breathe_runs_and_stops() -> None:
    stop_event = threading.Event()

    def time_generator() -> Generator[float, None, None]:
        t = 0.0
        while True:
            yield t
            t += 0.1

    time_gen = time_generator()
    call_count = 0

    def mock_wait(timeout: float) -> bool:
        nonlocal call_count
        call_count += 1
        if call_count > 5:
            stop_event.set()
            return True
        next(time_gen)
        return False

    with patch("skaven.neopixel.NeoPixel", autospec=True) as mock_neopixel:
        mock_pixels = MagicMock()
        mock_pixels.__setitem__ = MagicMock()
        mock_pixels.show = MagicMock()
        mock_pixels.fill = MagicMock()
        mock_neopixel.return_value = mock_pixels
        sys.modules.pop("skaven.lighting", None)
        import skaven.lighting as lighting_module

        importlib.reload(lighting_module)
        with patch("skaven.lighting.time.time", side_effect=lambda: next(time_gen)):
            with patch("skaven.lighting.random.random", return_value=0.1):
                with patch("skaven.lighting.random.randint", return_value=10):
                    with patch.object(stop_event, "wait", side_effect=mock_wait):
                        lighting_module.skaven_flicker_breathe(stop_event=stop_event)
        # Use the mock_pixels object for assertions,
        # not the function references
        assert mock_pixels.show.call_count > 0
        mock_pixels.fill.assert_called_with((0, 0, 0))
        assert mock_pixels.show.call_count >= 1


def test_lighting_pin_selection_branches(monkeypatch: MonkeyPatch) -> None:
    """
    Test pin selection logic:
    - D18 == config.LED_PIN_BCM
    - D18 != config.LED_PIN_BCM
    - ImportError (D18 missing)
    """
    with patch("skaven.neopixel.NeoPixel", autospec=True) as mock_neopixel:
        mock_pixels = MagicMock()
        mock_pixels.__setitem__ = MagicMock()
        mock_pixels.show = MagicMock()
        mock_pixels.fill = MagicMock()
        mock_neopixel.return_value = mock_pixels

        # --- Case 1: D18 == config.LED_PIN_BCM ---
        sys.modules.pop("skaven.lighting", None)
        sys.modules.pop("skaven.board", None)
        sys.modules.pop("skaven.config", None)
        monkeypatch.setattr("skaven.board.D18", 42, raising=False)
        monkeypatch.setattr("skaven.config.LED_PIN_BCM", 42, raising=False)
        import skaven.lighting as lighting_module

        importlib.reload(lighting_module)
        assert lighting_module.led_pin_to_use == 42

        # --- Case 2: D18 != config.LED_PIN_BCM ---
        sys.modules.pop("skaven.lighting", None)
        sys.modules.pop("skaven.board", None)
        sys.modules.pop("skaven.config", None)
        monkeypatch.setattr("skaven.board.D18", 1, raising=False)
        monkeypatch.setattr("skaven.config.LED_PIN_BCM", 2, raising=False)
        import skaven.lighting as lighting_module

        importlib.reload(lighting_module)
        assert lighting_module.led_pin_to_use == 2

        # --- Case 3: D18 missing (fallback to config.LED_PIN_BCM) ---
        sys.modules.pop("skaven.lighting", None)
        sys.modules.pop("skaven.board", None)
        sys.modules.pop("skaven.config", None)
        # Replace skaven.board with a dummy module that raises ImportError
        # on D18 import

        class DummyBoard(types.ModuleType):

            def __getattr__(self, name: str) -> object:
                if name == "D18":
                    raise ImportError("No module named 'D18'")
                raise AttributeError(name)

        sys.modules["skaven.board"] = DummyBoard("skaven.board")
        monkeypatch.setattr("skaven.config.LED_PIN_BCM", 99, raising=False)
        import skaven.lighting as lighting_module

        importlib.reload(lighting_module)
        assert lighting_module.led_pin_to_use == 99
        # Restore real skaven.board for subsequent tests
        sys.modules.pop("skaven.board", None)


def test_skaven_flicker_breathe_finally_cleanup() -> None:
    """
    Test that the finally block in skaven_flicker_breathe is always
    executed (cleanup).
    """
    stop_event = threading.Event()
    with patch("skaven.neopixel.NeoPixel", autospec=True) as mock_neopixel:
        mock_pixels = MagicMock()
        mock_pixels.__setitem__ = MagicMock()
        # Patch show to raise after first call
        called = False

        def show_side_effect() -> None:
            nonlocal called
            if not called:
                called = True
            else:
                raise Exception("fail!")

        mock_pixels.show.side_effect = show_side_effect
        mock_pixels.fill = MagicMock()
        mock_neopixel.return_value = mock_pixels
        sys.modules.pop("skaven.lighting", None)
        import skaven.lighting as lighting_module

        importlib.reload(lighting_module)
        with patch("skaven.lighting.time.time", return_value=0.0):
            try:
                lighting_module.skaven_flicker_breathe(stop_event=stop_event)
            except Exception as e:
                assert str(e) == "fail!"
        mock_pixels.fill.assert_called_with((0, 0, 0))
        assert mock_pixels.show.call_count >= 1
