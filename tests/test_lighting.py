import unittest
from unittest.mock import patch, MagicMock
from itertools import cycle
from skaven.lighting import skaven_flicker_breathe


class TestLightingEffects(unittest.TestCase):
    @patch("skaven.lighting.time")
    @patch("skaven.lighting.random")
    def test_skaven_flicker_breathe(
        self,
        mock_random: MagicMock,
        mock_time: MagicMock,
    ) -> None:
        # Mock time to simulate elapsed time
        # Simulate time progression
        mock_time.time.side_effect = cycle([0, 1, 2, 3])

        # Mock random to control flicker behavior
        # Alternate flicker indefinitely
        seq = cycle([0.1, 0.3])
        mock_random.random.side_effect = seq

        # Mock NeoPixel object
        pixels_mock = MagicMock()
        with patch("skaven.lighting.pixels", pixels_mock):
            # Run the function for a single iteration
            with patch(
                "skaven.lighting.time.sleep",
                return_value=None,
            ):
                try:
                    skaven_flicker_breathe()
                except KeyboardInterrupt:
                    pass

            # Verify pixel updates
            self.assertTrue(pixels_mock.__setitem__.called)
            self.assertTrue(pixels_mock.show.called)

    def test_pixels_cleanup_on_interrupt(self) -> None:
        # Mock NeoPixel object
        pixels_mock = MagicMock()
        with patch(
            "skaven.lighting.pixels",
            pixels_mock,
        ):
            # Run one cycle, which always cleans up
            skaven_flicker_breathe()
            pixels_mock.fill.assert_called_once_with((0, 0, 0))
            # show() used in update or cleanup
            pixels_mock.show.assert_called()


if __name__ == "__main__":
    unittest.main()
