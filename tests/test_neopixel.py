import pytest
import logging
from displayboard.neopixel import NeoPixel, GRB
from typing import Any
from unittest.mock import MagicMock
import sys


@pytest.mark.parametrize("pin", ["D18", "D21", "D99"])
def test_neopixel_initialization(mock_neopixel: Any, pin: str) -> None:
    # Test initialization of NeoPixel object with different pins
    count = 10
    brightness = 0.5
    auto_write = True
    pixel_order = GRB
    neopixel = NeoPixel(pin, count, brightness, auto_write, pixel_order)
    assert isinstance(neopixel, NeoPixel)


@pytest.mark.parametrize("pin", ["D18", "D21", "D99"])
def test_neopixel_show(mock_neopixel: Any, pin: str) -> None:
    # Test the show method (stubbed) for different pins
    neopixel = NeoPixel(pin, 10, 0.5, True, GRB)
    try:
        neopixel.show()
    except Exception as e:
        pytest.fail(f"show() raised an exception: {e}")


@pytest.mark.parametrize("pin", ["D18", "D21", "D99"])
def test_neopixel_fill(mock_neopixel: Any, pin: str) -> None:
    # Test the fill method (stubbed) for different pins
    color = (255, 0, 0)  # Red
    neopixel = NeoPixel(pin, 10, 0.5, True, GRB)
    try:
        neopixel.fill(color)
    except Exception as e:
        pytest.fail(f"fill() raised an exception: {e}")


@pytest.mark.parametrize("pin", ["D18", "D21", "D99"])
def test_neopixel_setitem(mock_neopixel: Any, pin: str) -> None:
    # Test the __setitem__ method (stubbed) for different pins
    index: int = 0
    color: tuple[int, int, int] = (0, 255, 0)  # Green
    neopixel: NeoPixel = NeoPixel(pin, 10, 0.5, True, GRB)
    try:
        neopixel[index] = color
    except Exception as e:
        pytest.fail(f"__setitem__ raised an exception: {e}")


def test_neopixel_permission_error_on_init(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test NeoPixel handles PermissionError during initialization gracefully."""
    caplog.set_level(logging.ERROR)

    # Force Linux platform to trigger real hardware path
    monkeypatch.setattr(sys, "platform", "linux")

    # Mock board module with all required pins
    import types

    mock_board = types.SimpleNamespace(D18=18, D21=21, D12=12, D10=10)

    # Create a mock real_neopixel that raises PermissionError
    class MockNeoPixelClass:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise PermissionError("Can't access /dev/mem")

    mock_real_neopixel = types.SimpleNamespace(NeoPixel=MockNeoPixelClass)

    # Patch the module-level imports
    monkeypatch.setattr("displayboard.neopixel.HAS_NEOPIXEL", True)
    monkeypatch.setattr("displayboard.neopixel.board", mock_board)
    monkeypatch.setattr("displayboard.neopixel.real_neopixel", mock_real_neopixel)

    # Initialize should handle PermissionError gracefully
    neopixel = NeoPixel(18, 10, 0.5, True, GRB)

    # Should log error with helpful message
    assert "Permission denied initializing NeoPixel" in caplog.text
    assert "setup-permissions.sh" in caplog.text
    assert neopixel._pixels is None


def test_neopixel_runtime_error_on_init(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test NeoPixel handles RuntimeError during initialization gracefully."""
    caplog.set_level(logging.ERROR)

    # Force Linux platform
    monkeypatch.setattr(sys, "platform", "linux")

    # Mock board module with all required pins
    import types

    mock_board = types.SimpleNamespace(D18=18, D21=21, D12=12, D10=10)

    # Create a mock real_neopixel that raises RuntimeError
    class MockNeoPixelClass:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("DMA channel busy")

    mock_real_neopixel = types.SimpleNamespace(NeoPixel=MockNeoPixelClass)

    # Patch the module-level imports
    monkeypatch.setattr("displayboard.neopixel.HAS_NEOPIXEL", True)
    monkeypatch.setattr("displayboard.neopixel.board", mock_board)
    monkeypatch.setattr("displayboard.neopixel.real_neopixel", mock_real_neopixel)

    # Initialize should handle RuntimeError gracefully
    neopixel = NeoPixel(18, 10, 0.5, True, GRB)

    # Should log error with helpful message
    assert "RuntimeError initializing NeoPixel" in caplog.text
    assert "setup-permissions.sh" in caplog.text
    assert neopixel._pixels is None


def test_neopixel_generic_exception_on_init(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test NeoPixel handles generic Exception during initialization gracefully."""
    caplog.set_level(logging.ERROR)

    # Force Linux platform
    monkeypatch.setattr(sys, "platform", "linux")

    # Mock board module
    import types

    mock_board = types.SimpleNamespace(D18=18, D21=21)

    # Create a mock real_neopixel that raises generic Exception
    class MockNeoPixelClass:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise Exception("Unknown error")

    mock_real_neopixel = types.SimpleNamespace(NeoPixel=MockNeoPixelClass)

    # Patch the module-level imports
    monkeypatch.setattr("displayboard.neopixel.HAS_NEOPIXEL", True)
    monkeypatch.setattr("displayboard.neopixel.board", mock_board)
    monkeypatch.setattr("displayboard.neopixel.real_neopixel", mock_real_neopixel)

    # Initialize should handle Exception gracefully
    neopixel = NeoPixel(18, 10, 0.5, True, GRB)

    # Should log error with helpful message
    assert "Failed to initialize NeoPixel hardware" in caplog.text
    assert "/dev/mem" in caplog.text
    assert neopixel._pixels is None


def test_neopixel_show_clears_on_failure(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that show() clears _pixels reference on persistent failure."""
    caplog.set_level(logging.ERROR)

    # Create NeoPixel instance with mock pixels
    neopixel = NeoPixel(18, 10, 0.5, True, GRB)

    # Create a failing mock pixel object
    mock_pixels = MagicMock()
    mock_pixels.show.side_effect = RuntimeError("Hardware failure")
    neopixel._pixels = mock_pixels

    # Call show() - should handle error and clear _pixels
    neopixel.show()

    assert "Failed to update NeoPixel display" in caplog.text
    assert neopixel._pixels is None


def test_neopixel_fill_clears_on_failure(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that fill() clears _pixels reference on persistent failure."""
    caplog.set_level(logging.ERROR)

    # Create NeoPixel instance with mock pixels
    neopixel = NeoPixel(18, 10, 0.5, False, GRB)

    # Create a failing mock pixel object
    mock_pixels = MagicMock()
    mock_pixels.fill.side_effect = RuntimeError("Hardware failure")
    neopixel._pixels = mock_pixels

    # Call fill() - should handle error and clear _pixels
    neopixel.fill((255, 0, 0))

    assert "Failed to fill NeoPixel strip" in caplog.text
    assert neopixel._pixels is None


def test_neopixel_setitem_clears_on_failure(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that __setitem__() clears _pixels reference on persistent failure."""
    caplog.set_level(logging.ERROR)

    # Create NeoPixel instance with mock pixels
    neopixel = NeoPixel(18, 10, 0.5, False, GRB)

    # Create a failing mock pixel object
    mock_pixels = MagicMock()
    mock_pixels.__setitem__.side_effect = RuntimeError("Hardware failure")
    neopixel._pixels = mock_pixels

    # Call setitem - should handle error and clear _pixels
    neopixel[0] = (255, 0, 0)

    assert "Failed to set pixel 0" in caplog.text
    assert neopixel._pixels is None


def test_neopixel_operations_safe_when_pixels_none() -> None:
    """Test that all operations are safe when _pixels is None."""
    neopixel = NeoPixel(18, 10, 0.5, True, GRB)
    neopixel._pixels = None

    # None of these should raise exceptions
    neopixel.show()
    neopixel.fill((255, 0, 0))
    neopixel[0] = (0, 255, 0)
