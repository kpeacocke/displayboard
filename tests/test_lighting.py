import pytest
from unittest.mock import patch, MagicMock
from skaven.lighting import skaven_flicker_breathe_v2, skaven_flicker_breathe
from typing import Generator


@pytest.fixture
def mock_pixels() -> Generator[MagicMock, None, None]:
    with patch("skaven.lighting.pixels") as mock_pixels:
        yield mock_pixels


def test_skaven_flicker_breathe_v2_runs(mock_pixels: MagicMock) -> None:
    # Test that the function runs without errors
    # for a fixed number of iterations
    skaven_flicker_breathe_v2(iterations=5)
    assert mock_pixels.show.call_count > 0


def test_skaven_flicker_breathe_v2_clears_pixels_on_exit(
    mock_pixels: MagicMock,
) -> None:
    # Test that the pixels are cleared (set to (0, 0, 0))
    # when the function exits
    skaven_flicker_breathe_v2(iterations=1)
    mock_pixels.fill.assert_called_with((0, 0, 0))
    mock_pixels.show.assert_called()


def test_skaven_flicker_breathe_v2_breathe_calculation() -> None:
    # Test the internal breathe calculation logic
    with patch("skaven.lighting.math.sin", return_value=0) as mock_sin:
        with patch("skaven.lighting.time.time", side_effect=[0, 1]):
            skaven_flicker_breathe_v2(iterations=1)
            mock_sin.assert_called()


def test_skaven_flicker_breathe(mock_pixels: MagicMock) -> None:
    # Mock time and random to control the behavior
    def time_generator() -> Generator[int, None, None]:
        t = 0
        while True:
            yield t
            t += 1

    time_gen = time_generator()
    with patch(
        "skaven.lighting.time.time",
        side_effect=lambda: next(time_gen),
    ):
        with patch(
            "skaven.lighting.random.random",
            side_effect=(value for value in [0.1, 0.3, 0.5, 0.7] * 100),
        ):
            with patch(
                "skaven.lighting.time.sleep",
                side_effect=KeyboardInterrupt,
            ):
                # Run the function and stop it with a KeyboardInterrupt
                try:
                    skaven_flicker_breathe()
                except KeyboardInterrupt:
                    pass

    # Verify pixel updates and cleanup
    assert mock_pixels.show.call_count > 0
    mock_pixels.fill.assert_called_with((0, 0, 0))
    mock_pixels.show.assert_called()
