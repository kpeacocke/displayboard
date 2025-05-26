import pytest
from displayboard.neopixel import NeoPixel, GRB
from typing import Any


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
