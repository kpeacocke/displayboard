import sys
import pytest
from unittest import mock


# Use a fixture to patch sys.modules before importing mister_control
import collections.abc


@pytest.fixture(autouse=True)
def patch_gpio_and_time(
    monkeypatch: pytest.MonkeyPatch,
) -> collections.abc.Generator[tuple[mock.MagicMock, mock.MagicMock], None, None]:
    """Fixture to patch RPi.GPIO and time before importing mister_control."""
    mock_gpio = mock.MagicMock()
    mock_time = mock.MagicMock()
    # Set constants to simple values for compatibility with implementation
    mock_gpio.BCM = 11
    mock_gpio.OUT = 0
    mock_gpio.HIGH = 1
    mock_gpio.LOW = 0
    # Explicitly set methods to MagicMock so calls are tracked
    mock_gpio.setmode = mock.MagicMock()
    mock_gpio.setup = mock.MagicMock()
    mock_gpio.output = mock.MagicMock()
    mock_gpio.cleanup = mock.MagicMock()
    sys.modules["RPi"] = mock.MagicMock()
    sys.modules["RPi.GPIO"] = mock_gpio
    sys.modules["time"] = mock_time
    # Remove skaven.mister_control from sys.modules before each test to force re-import with mocks
    if "skaven.mister_control" in sys.modules:
        del sys.modules["skaven.mister_control"]
    import skaven.mister_control as mister_control

    # Patch the GPIO in the implementation directly
    setattr(mister_control, "GPIO", mock_gpio)
    yield mock_gpio, mock_time
    del sys.modules["RPi"]
    del sys.modules["RPi.GPIO"]
    del sys.modules["time"]
    if "skaven.mister_control" in sys.modules:
        del sys.modules["skaven.mister_control"]


def test_setup(patch_gpio_and_time: tuple[mock.MagicMock, mock.MagicMock]) -> None:
    mock_gpio, _ = patch_gpio_and_time
    import skaven.mister_control as mister_control

    mister_control.setup()
    mock_gpio.setmode.assert_called_once_with(mock_gpio.BCM)
    mock_gpio.setup.assert_called_once_with(mister_control.MISTER_PIN, mock_gpio.OUT)
    mock_gpio.output.assert_called_with(mister_control.MISTER_PIN, mock_gpio.LOW)


def test_trigger_mister_default_duration(
    patch_gpio_and_time: tuple[mock.MagicMock, mock.MagicMock],
    capsys: pytest.CaptureFixture[str],
) -> None:
    mock_gpio, mock_time = patch_gpio_and_time
    import skaven.mister_control as mister_control

    mister_control.trigger_mister()
    mock_gpio.output.assert_any_call(mister_control.MISTER_PIN, mock_gpio.HIGH)
    mock_time.sleep.assert_called_once_with(5)
    mock_gpio.output.assert_any_call(mister_control.MISTER_PIN, mock_gpio.LOW)
    out = capsys.readouterr().out
    assert "Turning mister ON for 5 seconds" in out
    assert "Mister OFF." in out


def test_trigger_mister_custom_duration(
    patch_gpio_and_time: tuple[mock.MagicMock, mock.MagicMock],
    capsys: pytest.CaptureFixture[str],
) -> None:
    mock_gpio, mock_time = patch_gpio_and_time
    import skaven.mister_control as mister_control

    mister_control.trigger_mister(duration=2)
    mock_gpio.output.assert_any_call(mister_control.MISTER_PIN, mock_gpio.HIGH)
    mock_time.sleep.assert_called_once_with(2)
    mock_gpio.output.assert_any_call(mister_control.MISTER_PIN, mock_gpio.LOW)
    out = capsys.readouterr().out
    assert "Turning mister ON for 2 seconds" in out


def test_cleanup(patch_gpio_and_time: tuple[mock.MagicMock, mock.MagicMock]) -> None:
    mock_gpio, _ = patch_gpio_and_time
    import skaven.mister_control as mister_control

    mister_control.cleanup()
    mock_gpio.output.assert_any_call(mister_control.MISTER_PIN, mock_gpio.LOW)
    mock_gpio.cleanup.assert_called_once()


def test_main_normal(
    patch_gpio_and_time: tuple[mock.MagicMock, mock.MagicMock],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import skaven.mister_control as mister_control

    setup_mock = mock.MagicMock()
    trigger_mister_mock = mock.MagicMock()
    cleanup_mock = mock.MagicMock()
    mister_control.setup = setup_mock
    mister_control.trigger_mister = trigger_mister_mock
    mister_control.cleanup = cleanup_mock
    mister_control.main()
    setup_mock.assert_called_once()
    trigger_mister_mock.assert_called_once_with(duration=5)
    cleanup_mock.assert_called_once()
    out = capsys.readouterr().out
    assert "GPIO cleaned up." in out


def test_main_keyboard_interrupt(
    patch_gpio_and_time: tuple[mock.MagicMock, mock.MagicMock],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import skaven.mister_control as mister_control

    setup_mock = mock.MagicMock()
    monkeypatch.setattr(mister_control, "setup", setup_mock)

    def raise_interrupt(*args: object, **kwargs: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(mister_control, "trigger_mister", raise_interrupt)
    cleanup_mock = mock.MagicMock()
    monkeypatch.setattr(mister_control, "cleanup", cleanup_mock)
    mister_control.main()
    setup_mock.assert_called_once()
    cleanup_mock.assert_called_once()
    out = capsys.readouterr().out
    assert "Interrupted by user." in out
    assert "GPIO cleaned up." in out
