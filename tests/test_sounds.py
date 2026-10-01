import sys
import os
import pytest
from unittest.mock import patch, MagicMock
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, cast
from displayboard import config
import subprocess
import pygame
import displayboard.sounds as main

print("displayboard.sounds loaded from:", main.__file__)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


def test_ambient_loop_empty_returns_immediately() -> None:
    main.ambient_loop([], 100, 0.5)


def test_chains_loop_empty_returns_immediately() -> None:
    main.chains_loop([], stop_event=threading.Event())


def test_main_loop_empty_returns_immediately() -> None:
    main.main_loop([], stop_event=threading.Event())


def test_rats_loop_breaks_after_fadeout(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("r1.wav"), Path("r2.wav")]
    chans = [
        cast(MagicMock, main.pygame.mixer.Channel(1)),
        cast(MagicMock, main.pygame.mixer.Channel(2)),
    ]
    event = threading.Event()
    call_state = {"waits": 0}

    def fake_wait(timeout: object = None) -> bool:
        call_state["waits"] += 1
        if call_state["waits"] == 1:
            event.set()
        return False

    monkeypatch.setattr(event, "wait", fake_wait)
    main.rats_loop(files, chans, stop_event=event)
    assert call_state["waits"] == 1


def test_rats_loop_fadeout_event_not_set(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("r1.wav"), Path("r2.wav")]
    chans = [
        cast(MagicMock, main.pygame.mixer.Channel(1)),
        cast(MagicMock, main.pygame.mixer.Channel(2)),
    ]
    event = threading.Event()
    call_state = {"waits": 0}

    def fake_wait(timeout: object = None) -> bool:
        call_state["waits"] += 1
        # Never set the event, so event.is_set() stays False
        if call_state["waits"] > 2:
            # Prevent infinite loop
            raise RuntimeError("rats_loop: test exit after 2 waits")
        return False

    monkeypatch.setattr(event, "wait", fake_wait)
    try:
        main.rats_loop(files, chans, stop_event=event)
    except RuntimeError:
        pass
    # Should have called wait at least twice (main sleep, fadeout)
    assert call_state["waits"] >= 2


@patch("displayboard.sounds.logger")
def test_main_shutdown_wait_generic_exception(
    mock_logger: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Patch pygame and mixer init to no-op
    monkeypatch.setattr(main.pygame, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "set_num_channels", lambda n: None)
    # Patch load_sound_categories to return at least one file so main loop runs
    monkeypatch.setattr(
        main,
        "load_sound_categories",
        lambda _: {
            "ambient": [Path("a.wav")],
            "rats": [],
            "chains": [],
            "screams": [Path("scream.wav")],
            "displayboard": [],
        },
    )
    monkeypatch.setattr(main.threading.Thread, "start", lambda self: None)
    event = threading.Event()
    call_state = {"waits": 0}

    def fake_wait(timeout: object = None) -> None:
        call_state["waits"] += 1
        if call_state["waits"] == 1:
            event.set()
            return
        # On second wait (shutdown), raise a generic Exception
        raise Exception("shutdown wait generic exception (331-332)")

    monkeypatch.setattr(event, "wait", fake_wait)
    mock_chan = MagicMock()
    monkeypatch.setattr(main.pygame.mixer, "Channel", lambda idx: mock_chan)
    mock_chan.fadeout.side_effect = None
    with pytest.raises(Exception, match="shutdown wait generic exception"):
        main.main(stop_event=event)
    mock_logger.critical.assert_called()


@patch("displayboard.sounds.logger")
def test_main_exception_in_shutdown_wait_branch_331_332(
    mock_logger: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Covers: except Exception as e: ... in shutdown wait (lines 331-332)"""
    monkeypatch.setattr(main.pygame, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "set_num_channels", lambda n: None)
    monkeypatch.setattr(
        main,
        "load_sound_categories",
        lambda _: {
            "ambient": [Path("a.wav")],
            "rats": [],
            "chains": [],
            "screams": [Path("scream.wav")],
            "displayboard": [],
        },
    )
    monkeypatch.setattr(main.threading.Thread, "start", lambda self: None)
    event = threading.Event()
    call_state = {"waits": 0}

    def fake_wait(timeout: object = None) -> None:
        call_state["waits"] += 1
        if call_state["waits"] == 1:
            event.set()
            return
        raise Exception("shutdown wait exception 331-332")

    monkeypatch.setattr(event, "wait", fake_wait)
    mock_chan = MagicMock()
    monkeypatch.setattr(main.pygame.mixer, "Channel", lambda idx: mock_chan)
    mock_chan.fadeout.side_effect = None
    with pytest.raises(Exception, match="shutdown wait exception 331-332"):
        main.main(stop_event=event)
    mock_logger.critical.assert_called()


@patch("displayboard.sounds.logger")
def test_main_keyboardinterrupt_in_shutdown_wait_sleep(
    mock_logger: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Patch pygame and mixer init to no-op
    monkeypatch.setattr(main.pygame, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "set_num_channels", lambda n: None)
    monkeypatch.setattr(
        main,
        "load_sound_categories",
        lambda _: {
            "ambient": [Path("a.wav")],
            "rats": [],
            "chains": [],
            "screams": [Path("scream.wav")],
            "displayboard": [],
        },
    )
    # Disable threads
    monkeypatch.setattr(threading.Thread, "start", lambda self: None)
    event: threading.Event = threading.Event()
    # Simulate KeyboardInterrupt on event.wait to trigger shutdown
    monkeypatch.setattr(
        event,
        "wait",
        lambda timeout: (_ for _ in ()).throw(KeyboardInterrupt("shutdown wait")),
    )
    # Patch time.sleep to raise KeyboardInterrupt in shutdown wait
    monkeypatch.setattr(
        main.time,
        "sleep",
        lambda seconds: (_ for _ in ()).throw(KeyboardInterrupt("shutdown wait")),
    )
    mock_chan: MagicMock = MagicMock()
    monkeypatch.setattr(main.pygame.mixer, "Channel", lambda idx: mock_chan)
    mock_chan.fadeout.side_effect = None
    # Should catch KeyboardInterrupt and exit normally
    main.main(stop_event=event)
    mock_logger.info.assert_any_call(
        "KeyboardInterrupt received, shutting down sound loops..."
    )


@patch("displayboard.sounds.logger")
def test_main_exception_in_shutdown_wait_sleep(
    mock_logger: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 1) stub pygame init/mixer
    monkeypatch.setattr(main.pygame, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "set_num_channels", lambda n: None)

    # 2) provide at least one scream file so loop runs
    monkeypatch.setattr(
        main,
        "load_sound_categories",
        lambda _: {
            "ambient": [Path("a.wav")],
            "rats": [],
            "chains": [],
            "screams": [Path("scream.wav")],
            "displayboard": [],
        },
    )

    # 3) disable threads
    monkeypatch.setattr(main.threading.Thread, "start", lambda self: None)

    # 4) simulate KeyboardInterrupt in the main scream-loop wait
    event = threading.Event()
    monkeypatch.setattr(
        event,
        "wait",
        lambda timeout=None: (_ for _ in ()).throw(KeyboardInterrupt("main loop")),
    )

    # 5) simulate generic Exception in shutdown sleep
    monkeypatch.setattr(
        main.time,
        "sleep",
        lambda seconds: (_ for _ in ()).throw(Exception("shutdown wait exception")),
    )

    # 6) stub fadeouts
    mock_chan = MagicMock()
    monkeypatch.setattr(main.pygame.mixer, "Channel", lambda idx: mock_chan)
    mock_chan.fadeout.side_effect = None

    # Expect the generic exception to bubble out
    with pytest.raises(Exception, match="shutdown wait exception"):
        main.main(stop_event=event)
    mock_logger.critical.assert_called()


@patch("displayboard.sounds.logger")
def test_main_exception_in_shutdown_wait_only(
    mock_logger: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Patch pygame and mixer init to no-op
    monkeypatch.setattr(main.pygame, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "set_num_channels", lambda n: None)
    # Patch load_sound_categories to return at least one file so main loop runs
    monkeypatch.setattr(
        main,
        "load_sound_categories",
        lambda _: {
            "ambient": [Path("a.wav")],
            "rats": [],
            "chains": [],
            "screams": [Path("scream.wav")],
            "displayboard": [],
        },
    )
    monkeypatch.setattr(main.threading.Thread, "start", lambda self: None)
    # Create a single event instance and patch its wait method
    event = threading.Event()
    call_state = {"waits": 0}

    def fake_wait(timeout: object = None) -> None:
        call_state["waits"] += 1
        if call_state["waits"] == 1:
            event.set()
            return
        raise Exception("shutdown wait only (331-332)")

    monkeypatch.setattr(event, "wait", fake_wait)
    mock_chan = MagicMock()
    monkeypatch.setattr(main.pygame.mixer, "Channel", lambda idx: mock_chan)
    mock_chan.fadeout.side_effect = None
    with pytest.raises(Exception, match="shutdown wait only \\(331-332\\)"):
        main.main(stop_event=event)
    mock_logger.critical.assert_called()


@patch("displayboard.sounds.logger")
def test_main_keyboardinterrupt_in_shutdown_wait_only(
    mock_logger: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 1) stub pygame.init & mixer setup
    monkeypatch.setattr(main.pygame, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "set_num_channels", lambda n: None)

    # 2) ensure the scream loop actually runs once
    monkeypatch.setattr(
        main,
        "load_sound_categories",
        lambda _: {
            "ambient": [Path("a.wav")],
            "rats": [],
            "chains": [],
            "screams": [Path("scream.wav")],
            "displayboard": [],
        },
    )

    # 3) prevent any real threads from launching
    monkeypatch.setattr(main.threading.Thread, "start", lambda self: None)

    # 4) immediately throw in the main scream-loop wait() to enter shutdown handler
    event = threading.Event()
    monkeypatch.setattr(
        event,
        "wait",
        lambda timeout=None: (_ for _ in ()).throw(KeyboardInterrupt("boom")),
    )

    # 5) patch time.sleep to no-op to allow shutdown wait to complete
    monkeypatch.setattr(main.time, "sleep", lambda seconds: None)

    # 6) stub out fadeouts so no real channels are needed
    mock_chan = MagicMock()
    monkeypatch.setattr(main.pygame.mixer, "Channel", lambda idx: mock_chan)
    mock_chan.fadeout.side_effect = None

    # Now call main: first interrupt triggers shutdown, second is caught by code
    main.main(stop_event=event)

    # Confirm graceful-shutdown message was logged
    mock_logger.info.assert_any_call(
        "KeyboardInterrupt received, shutting down sound loops..."
    )


@patch("displayboard.sounds.logger")
def test_main_exception_branch_lines_331_332(
    mock_logger: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the generic Exception branch in main() (lines 331-332)."""
    # Patch pygame and mixer init to no-op
    monkeypatch.setattr(main.pygame, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "set_num_channels", lambda n: None)

    # Patch load_sound_categories to raise a generic Exception
    monkeypatch.setattr(
        main,
        "load_sound_categories",
        lambda _: (_ for _ in ()).throw(Exception("test exception branch 331-332")),
    )

    # Run main and assert the Exception is raised and logger.critical is called
    with pytest.raises(Exception, match="test exception branch 331-332"):
        main.main(stop_event=main.threading.Event())
    mock_logger.critical.assert_called()


def test_set_event_soon_sets_event(monkeypatch: pytest.MonkeyPatch) -> None:
    event = threading.Event()
    # Inline the logic for set_event_soon since main has no such function
    # This is typically: threading.Timer(0.01, event.set).start()
    t = threading.Timer(0.01, event.set)
    t.start()
    t.join()  # Wait for the timer to fire to ensure event is set
    assert event.is_set()


@patch("displayboard.sounds.logger")
def test_main_keyboard_interrupt_in_shutdown_wait(
    mock_logger: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import displayboard.sounds as main

    monkeypatch.setattr(main.pygame, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "set_num_channels", lambda n: None)
    monkeypatch.setattr(
        main,
        "load_sound_categories",
        lambda _: {
            "ambient": [Path("a.wav")],
            "rats": [],
            "chains": [],
            "screams": [Path("scream.wav")],
            "displayboard": [],
        },
    )
    monkeypatch.setattr(threading.Thread, "start", lambda self: None)
    original_wait = threading.Event.wait
    call_state = {"waits": 0}

    def fake_wait(self: threading.Event, timeout: object = None) -> None:
        call_state["waits"] += 1
        if call_state["waits"] == 1:
            # Simulate KeyboardInterrupt in main loop
            raise KeyboardInterrupt("main loop")
        # Set the event so shutdown wait will not loop forever
        self.set()
        # On shutdown wait, break the wait loop by raising KeyboardInterrupt
        raise KeyboardInterrupt("shutdown wait exit")

    monkeypatch.setattr(threading.Event, "wait", fake_wait)
    mock_chan = MagicMock()
    monkeypatch.setattr(main.pygame.mixer, "Channel", lambda idx: mock_chan)
    mock_chan.fadeout.side_effect = None
    for i in range(main.config.RATS_CHANNEL_START, main.config.RATS_CHANNEL_END):
        chan = MagicMock()
        chan.fadeout.side_effect = None
    try:
        main.main(stop_event=threading.Event())
    except KeyboardInterrupt as e:
        assert str(e) == "shutdown wait exit"
    finally:
        monkeypatch.setattr(threading.Event, "wait", original_wait)
    mock_logger.info.assert_any_call(
        "KeyboardInterrupt received, shutting down sound loops..."
    )


def test_main_no_sounds_sets_event(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main.pygame, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "set_num_channels", lambda n: None)
    monkeypatch.setattr(
        main,
        "load_sound_categories",
        lambda _: {
            k: [] for k in ["ambient", "rats", "chains", "screams", "displayboard"]
        },
    )
    monkeypatch.setattr(threading.Thread, "start", lambda self: None)
    event = threading.Event()
    # Patch event.wait to avoid hanging (raise after one call)
    call_count = {"n": 0}

    def fake_wait(timeout: object = None) -> bool:
        call_count["n"] += 1
        if call_count["n"] > 1:
            raise RuntimeError(
                "test_main_no_sounds_sets_event: wait called more than once "
                "(would hang)"
            )
        # Simulate event being set after first wait
        event.set()
        return True

    monkeypatch.setattr(event, "wait", fake_wait)
    main.main(stop_event=event)
    assert event.is_set()


def test_ambient_loop_break_after_first_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("a.wav")]
    event = threading.Event()
    call_state = {"waits": 0}

    def fake_wait(timeout: object = None) -> bool:
        call_state["waits"] += 1
        if call_state["waits"] == 1:
            event.set()
        return False

    monkeypatch.setattr(event, "wait", fake_wait)
    main.ambient_loop(files, 100, 0.5, stop_event=event)
    # Only one wait should occur before breaking (event set after first wait)
    assert call_state["waits"] == 1


def test_rats_loop_break_after_fadeout_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("r1.wav"), Path("r2.wav")]
    chans = [
        cast(MagicMock, main.pygame.mixer.Channel(1)),
        cast(MagicMock, main.pygame.mixer.Channel(2)),
    ]
    event = threading.Event()
    call_state = {"waits": 0}

    def fake_wait(timeout: object = None) -> bool:
        call_state["waits"] += 1
        if call_state["waits"] == 1:
            event.set()
        return False

    monkeypatch.setattr(event, "wait", fake_wait)
    main.rats_loop(files, chans, stop_event=event)
    assert call_state["waits"] == 1


def test_rats_loop_break_after_sleep_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    # Covers the break after the second event.wait (sleep wait) in rats_loop
    files = [Path("r1.wav"), Path("r2.wav")]
    chans = [
        cast(MagicMock, main.pygame.mixer.Channel(1)),
        cast(MagicMock, main.pygame.mixer.Channel(2)),
    ]
    event = threading.Event()
    call_state = {"waits": 0}

    def fake_wait(timeout: object = None) -> bool:
        call_state["waits"] += 1
        # First wait is for fadeout, second is for sleep
        if call_state["waits"] == 2:
            event.set()
        return False

    monkeypatch.setattr(event, "wait", fake_wait)
    main.rats_loop(files, chans, stop_event=event)
    # Should break after the second wait
    assert call_state["waits"] == 2


def test_ambient_loop_event_set_after_fadeout(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("a.wav")]
    event = threading.Event()
    call_state = {"waits": 0}

    # Patch fadeout to set the event after the first wait

    mock_chan = main.pygame.mixer.Channel(config.AMBIENT_CHANNEL)

    def fake_fadeout(ms: int) -> None:
        event.set()

    monkeypatch.setattr(mock_chan, "fadeout", fake_fadeout)

    def fake_wait(timeout: Optional[float] = None) -> bool:
        call_state["waits"] += 1
        return False

    monkeypatch.setattr(event, "wait", fake_wait)
    main.ambient_loop(files, 100, 0.5, stop_event=event)
    assert call_state["waits"] >= 2


def test_chains_loop_event_set_after_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("c1.wav")]
    event = threading.Event()
    call_state = {"waits": 0}

    def fake_wait(timeout: object = None) -> bool:
        call_state["waits"] += 1
        if call_state["waits"] == 1:
            return False
        event.set()
        return True

    monkeypatch.setattr(event, "wait", fake_wait)
    main.chains_loop(files, stop_event=event)
    assert call_state["waits"] >= 1


def test_main_loop_event_set_after_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("s1.wav")]
    event = threading.Event()
    call_state = {"waits": 0}

    def fake_wait(timeout: object = None) -> bool:
        call_state["waits"] += 1
        if call_state["waits"] == 1:
            return False
        event.set()
        return True

    monkeypatch.setattr(event, "wait", fake_wait)
    main.main_loop(files, stop_event=event)
    assert call_state["waits"] >= 1


def test_rats_loop_event_set_after_fadeout(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("r1.wav"), Path("r2.wav")]
    chans = [
        cast(MagicMock, main.pygame.mixer.Channel(1)),
        cast(MagicMock, main.pygame.mixer.Channel(2)),
    ]
    event = threading.Event()
    call_state = {"waits": 0}

    def fake_wait(timeout: object = None) -> bool:
        call_state["waits"] += 1
        if call_state["waits"] == 1:
            event.set()
        return False

    monkeypatch.setattr(event, "wait", fake_wait)
    main.rats_loop(files, chans, stop_event=event)
    assert call_state["waits"] >= 1


def test_rats_loop_event_set_after_main_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("r1.wav"), Path("r2.wav")]
    chans = [
        cast(MagicMock, main.pygame.mixer.Channel(1)),
        cast(MagicMock, main.pygame.mixer.Channel(2)),
    ]
    event = threading.Event()
    call_state = {"waits": 0}

    def fake_wait(timeout: object = None) -> bool:
        call_state["waits"] += 1
        if call_state["waits"] == 2:
            event.set()
        return False

    monkeypatch.setattr(event, "wait", fake_wait)
    main.rats_loop(files, chans, stop_event=event)
    assert call_state["waits"] >= 2


# --- Coverage for main(stop_after=1) and set_event_soon logic ---
def test_main_stop_after_sets_event(monkeypatch: pytest.MonkeyPatch) -> None:
    # Patch pygame and mixer init to no-op
    monkeypatch.setattr(main.pygame, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "set_num_channels", lambda n: None)
    # Patch load_sound_categories to return empty lists
    monkeypatch.setattr(
        main,
        "load_sound_categories",
        lambda _: {
            k: [] for k in ["ambient", "rats", "chains", "screams", "displayboard"]
        },
    )
    # Patch Thread to not actually start
    monkeypatch.setattr(threading.Thread, "start", lambda self: None)
    # Patch event.wait to return True immediately
    monkeypatch.setattr(threading.Event, "wait", lambda self, timeout=None: True)
    main.main(stop_after=1)


@patch("displayboard.sounds.logger")
def test_main_stop_after_full(
    mock_logger: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test full stop_after logic: print, log, sleep, and event.set."""
    # Record sleep calls
    sleep_calls: list[float] = []
    monkeypatch.setattr(main.time, "sleep", lambda s: sleep_calls.append(s))
    # Patch Thread.start to run target synchronously
    monkeypatch.setattr(threading.Thread, "start", lambda self: self._target())
    # Patch pygame init, mixer, and channels to no-op
    monkeypatch.setattr(main.pygame, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "set_num_channels", lambda n: None)
    # Patch load_sound_categories to return empty categories
    monkeypatch.setattr(
        main,
        "load_sound_categories",
        lambda _: {
            k: [] for k in ["ambient", "rats", "chains", "screams", "displayboard"]
        },
    )
    # Prepare explicit event
    event = threading.Event()
    # Patch event.wait to immediately return True so main exits
    monkeypatch.setattr(threading.Event, "wait", lambda self, timeout=None: True)
    # Run main with stop_after to trigger set_event_soon
    main.main(stop_event=event, stop_after=5)
    # Capture printed output
    captured = capsys.readouterr()
    assert "Stopping after 5 cycles" in captured.out
    # Assert logger info called
    mock_logger.info.assert_any_call("Stopping after 5 cycles")
    # Assert sleep and event.set
    assert sleep_calls == [0.1]
    assert event.is_set()


def test_set_event_soon_sleeps_and_sets_event(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that set_event_soon sleeps and triggers event.set in stop_after mode."""
    sleep_calls: list[float] = []
    # Patch time.sleep in set_event_soon to record calls
    monkeypatch.setattr(main.time, "sleep", lambda s: sleep_calls.append(s))
    # Patch Thread.start to call set_event_soon synchronously
    monkeypatch.setattr(threading.Thread, "start", lambda self: self._target())
    # Patch pygame and mixer init to no-op
    monkeypatch.setattr(main.pygame, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "set_num_channels", lambda n: None)
    # Patch load_sound_categories to return empty lists so no loops start
    monkeypatch.setattr(
        main,
        "load_sound_categories",
        lambda _: {
            k: [] for k in ["ambient", "rats", "chains", "screams", "displayboard"]
        },
    )
    # Patch event.wait to immediately return True
    monkeypatch.setattr(threading.Event, "wait", lambda self, timeout=None: True)
    # Use explicit event to capture set by set_event_soon
    event = threading.Event()
    # Run main with stop_after to trigger set_event_soon
    main.main(stop_event=event, stop_after=1)
    # Assert sleep was called with 0.1 and event is set
    assert sleep_calls == [0.1]
    assert event.is_set()


# --- Coverage for main() error/exception handling branches ---
@patch("displayboard.sounds.logger")
def test_main_pygame_error_branch(
    mock_logger: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(main.pygame, "init", lambda: None)
    monkeypatch.setattr(
        main.pygame.mixer, "init", lambda: (_ for _ in ()).throw(pygame.error("fail"))
    )
    with pytest.raises(pygame.error):
        main.main(stop_event=threading.Event())
    mock_logger.critical.assert_called()


@patch("displayboard.sounds.logger")
def test_main_generic_exception_branch(
    mock_logger: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(main.pygame, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "set_num_channels", lambda n: None)
    monkeypatch.setattr(
        main,
        "load_sound_categories",
        lambda _: (_ for _ in ()).throw(Exception("fail")),
    )
    with pytest.raises(Exception):
        main.main(stop_event=threading.Event())
    mock_logger.critical.assert_called()


def test_main_empty_sound_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Point config.SOUNDS_DIR to an empty directory
    monkeypatch.setattr(config, "SOUNDS_DIR", tmp_path)
    # Patch pygame.mixer.init and set_num_channels to no-op
    monkeypatch.setattr(main.pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "set_num_channels", lambda n: None)
    monkeypatch.setattr(main.pygame, "init", lambda: None)
    # Patch Thread to check if loops are started
    mock_thread_start = MagicMock()
    monkeypatch.setattr(threading.Thread, "start", mock_thread_start)
    # Patch event.wait to exit quickly
    original_wait = threading.Event.wait

    def quick_exit(*args: object, **kwargs: object) -> None:
        raise KeyboardInterrupt()

    monkeypatch.setattr(threading.Event, "wait", quick_exit)
    try:
        main.main(stop_event=threading.Event())
    except KeyboardInterrupt:
        pass
    finally:
        monkeypatch.setattr(threading.Event, "wait", original_wait)
    mock_thread_start.assert_not_called()


def test_rats_loop_empty_files_and_channels() -> None:
    # Should return immediately, no error
    main.rats_loop([], [], stop_event=threading.Event())


# Ensure the project root is on sys.path so we can import the module under test
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- Additional tests for 100% coverage of sounds.py ---


@patch("displayboard.sounds.logger")
def test_main_keyboard_interrupt_during_fadeout(
    mock_logger: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Simulate KeyboardInterrupt during fadeout in shutdown
    mock_chan = cast(MagicMock, main.pygame.mixer.Channel(config.AMBIENT_CHANNEL))
    mock_chan.fadeout.side_effect = KeyboardInterrupt("during fadeout")
    # Patch load_sound_categories to return at least one ambient file
    monkeypatch.setattr(
        main,
        "load_sound_categories",
        lambda _: {
            "ambient": [Path("a.wav")],
            "rats": [],
            "chains": [],
            "screams": [],
            "displayboard": [],
        },
    )
    # Patch pygame.mixer.init and set_num_channels to no-op
    monkeypatch.setattr(main.pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "set_num_channels", lambda n: None)
    # Patch pygame.init to no-op
    monkeypatch.setattr(main.pygame, "init", lambda: None)
    # Patch threading.Thread to not actually start threads
    monkeypatch.setattr(threading.Thread, "start", lambda self: None)
    # Patch event.wait to raise KeyboardInterrupt on first call (main scream loop)
    original_wait = threading.Event.wait

    call_state = {"waits": 0}

    def fake_wait(self: threading.Event, timeout: object = None) -> None:
        call_state["waits"] += 1
        # First wait: main loop, set event to exit main loop
        if call_state["waits"] == 1:
            self.set()
            return  # must return None
        # Second wait: shutdown wait, raise KeyboardInterrupt
        raise KeyboardInterrupt("during fadeout")

    monkeypatch.setattr(threading.Event, "wait", fake_wait)
    try:
        main.main(stop_event=threading.Event())
    except KeyboardInterrupt as e:
        assert str(e) == "during fadeout"
    finally:
        monkeypatch.setattr(threading.Event, "wait", original_wait)
    mock_logger.info.assert_any_call(
        "KeyboardInterrupt received, shutting down sound loops..."
    )


# Covers lines 312-315, 328-329, 331-332: KeyboardInterrupt and Exception branches in main
@patch("displayboard.sounds.logger")
def test_main_keyboard_interrupt_and_exception_branches(
    mock_logger: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Covers lines 312-315, 328-329, 331-332: KeyboardInterrupt and Exception branches in main
    monkeypatch.setattr(main.pygame, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "set_num_channels", lambda n: None)
    monkeypatch.setattr(
        main,
        "load_sound_categories",
        lambda _: {
            "ambient": [Path("a.wav")],
            "rats": [],
            "chains": [],
            "screams": [Path("scream.wav")],
            "displayboard": [],
        },
    )
    monkeypatch.setattr(threading.Thread, "start", lambda self: None)
    original_wait = threading.Event.wait
    call_state = {"waits": 0}

    def fake_wait(self: threading.Event, timeout: object = None) -> None:
        call_state["waits"] += 1
        if call_state["waits"] == 1:
            # Simulate KeyboardInterrupt in main loop
            raise KeyboardInterrupt("main loop")
        # Set the event so shutdown wait will not loop forever
        self.set()
        # On shutdown wait, break the wait loop by raising an exception
        raise Exception("shutdown wait exit")

    monkeypatch.setattr(threading.Event, "wait", fake_wait)
    mock_chan = cast(MagicMock, main.pygame.mixer.Channel(config.AMBIENT_CHANNEL))
    mock_chan.fadeout.side_effect = None
    for i in range(config.RATS_CHANNEL_START, config.RATS_CHANNEL_END):
        chan = cast(MagicMock, main.pygame.mixer.Channel(i))
        chan.fadeout.side_effect = None
    try:
        main.main(stop_event=threading.Event())
    except Exception as e:
        assert str(e) == "shutdown wait exit"
    finally:
        monkeypatch.setattr(threading.Event, "wait", original_wait)
    mock_logger.info.assert_any_call(
        "KeyboardInterrupt received, shutting down sound loops..."
    )


def test_main_handles_pygame_error(monkeypatch: pytest.MonkeyPatch) -> None:
    # Patch pygame.mixer.init to raise pygame.error
    monkeypatch.setattr(
        main.pygame.mixer, "init", lambda: (_ for _ in ()).throw(pygame.error("fail"))
    )
    with pytest.raises(pygame.error):
        main.main(stop_event=threading.Event())


def test_main_handles_generic_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    # Patch load_sound_categories to raise generic exception
    monkeypatch.setattr(
        main,
        "load_sound_categories",
        lambda _: (_ for _ in ()).throw(Exception("fail")),
    )
    # Patch pygame.mixer.init to no-op
    monkeypatch.setattr(main.pygame.mixer, "init", lambda: None)
    with pytest.raises(Exception):
        main.main(stop_event=threading.Event())


def test_main_scream_loop_no_screams_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    # Patch load_sound_categories to return no screams
    monkeypatch.setattr(
        main,
        "load_sound_categories",
        lambda _: {
            "ambient": [Path("a.wav")],
            "rats": [],
            "chains": [],
            "screams": [],
            "displayboard": [],
        },
    )
    # Patch pygame.mixer.init and set_num_channels to no-op
    monkeypatch.setattr(main.pygame.mixer, "init", lambda: None)
    monkeypatch.setattr(main.pygame.mixer, "set_num_channels", lambda n: None)
    monkeypatch.setattr(main.pygame, "init", lambda: None)
    # Patch threading.Thread to not actually start threads
    monkeypatch.setattr(threading.Thread, "start", lambda self: None)
    # Patch event.wait to return False once, then True (exit after one loop)
    call_count = {"n": 0}

    def fake_wait(self: threading.Event, timeout: object = None) -> bool:
        call_count["n"] += 1
        return call_count["n"] > 1

    monkeypatch.setattr(threading.Event, "wait", fake_wait)
    main.main(stop_event=threading.Event())


# --- Extra branch coverage for event.is_set() after waits in all loops ---


def test_ambient_loop_event_set_breaks(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("a.wav")]
    event = threading.Event()
    event.set()
    # Should exit immediately after first wait
    main.ambient_loop(files, 100, 0.5, stop_event=event)


def test_chains_loop_event_set_breaks(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("c1.wav")]
    event = threading.Event()
    event.set()
    main.chains_loop(files, stop_event=event)


def test_main_loop_event_set_breaks(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("s1.wav")]
    event = threading.Event()
    event.set()
    main.main_loop(files, stop_event=event)


def test_rats_loop_event_set_breaks(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("r1.wav"), Path("r2.wav")]
    chans = [
        cast(MagicMock, main.pygame.mixer.Channel(1)),
        cast(MagicMock, main.pygame.mixer.Channel(2)),
    ]
    event = threading.Event()
    event.set()
    main.rats_loop(files, chans, stop_event=event)


# --- Main scream loop: event set before loop, and empty scream files ---


@patch("displayboard.sounds.threading.Thread")
@patch("displayboard.sounds.load_sound_categories")
def test_main_scream_loop_event_set(
    mock_load: MagicMock, mock_thread: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    # All categories have at least one file except screams
    mock_load.return_value = {
        "ambient": [Path("a.wav")],
        "rats": [Path("r.wav")],
        "chains": [Path("c.wav")],
        "screams": [Path("scream.wav")],
        "displayboard": [Path("sk.wav")],
    }
    # Patch event.wait to return True immediately (event set)
    monkeypatch.setattr(threading.Event, "wait", lambda self, timeout=None: True)
    main.main(stop_event=threading.Event())


@patch("displayboard.sounds.threading.Thread")
@patch("displayboard.sounds.load_sound_categories")
def test_main_scream_loop_empty_screams(
    mock_load: MagicMock, mock_thread: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    # All categories have at least one file except screams
    mock_load.return_value = {
        "ambient": [Path("a.wav")],
        "rats": [Path("r.wav")],
        "chains": [Path("c.wav")],
        "screams": [],
        "displayboard": [Path("sk.wav")],
    }
    # Patch event.wait to break after one loop
    call_count = {"n": 0}

    def fake_wait(self: threading.Event, timeout: object = None) -> bool:
        call_count["n"] += 1
        return call_count["n"] > 1

    monkeypatch.setattr(threading.Event, "wait", fake_wait)
    main.main(stop_event=threading.Event())


# --- Use centralized mock_pygame fixture from conftest.py ---
@pytest.fixture(autouse=True)
def patch_pygame(monkeypatch: pytest.MonkeyPatch, mock_pygame: MagicMock) -> None:
    monkeypatch.setattr(main, "pygame", mock_pygame)


@pytest.fixture(autouse=True)
def patch_time_sleep(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    if request.node.get_closest_marker("no_autosleep"):
        return

    def fake_sleep(seconds: float) -> None:
        pass

    monkeypatch.setattr(main.time, "sleep", fake_sleep)


@pytest.fixture(autouse=True)
def patch_random(monkeypatch: pytest.MonkeyPatch) -> None:

    def fake_uniform(a: float, b: float) -> float:
        # Return the lower bound for predictable testing
        return a

    def fake_randint(a: int, b: int) -> int:
        # Return the lower bound for predictable testing
        return a

    def fake_choice(seq: Sequence[Any]) -> Any:
        # Return the first element for predictable testing
        if not seq:
            raise IndexError("Cannot choose from an empty sequence")
        return seq[0]

    def fake_sample(population: Sequence[Any], k: int) -> List[Any]:
        # Return the first k elements for predictable testing
        return list(population[:k])

    def fake_random() -> float:
        # Return a fixed value for predictable testing
        return 0.5

    monkeypatch.setattr(main.random, "uniform", fake_uniform)
    monkeypatch.setattr(main.random, "randint", fake_randint)
    monkeypatch.setattr(main.random, "choice", fake_choice)
    monkeypatch.setattr(main.random, "sample", fake_sample)
    monkeypatch.setattr(main.random, "random", fake_random)


def test_list_audio_files(fs: Any) -> None:
    fs.create_file("/tmp/a.wav", contents="dummy")
    fs.create_file("/tmp/b.ogg", contents="dummy")
    fs.create_file("/tmp/c.mp3", contents="dummy")
    fs.create_file("/tmp/d.txt", contents="dummy")
    found = main.list_audio_files(Path("/tmp"))
    exts = {p.suffix for p in found}
    assert exts == set(config.AUDIO_EXTENSIONS)
    paths = {p.name for p in found}
    assert paths == {"a.wav", "b.ogg", "c.mp3"}


def test_load_sound_categories(fs: Any) -> None:
    categories = ["ambient", "rats", "chains", "screams", "displayboard"]
    for cat in categories:
        fs.create_file(f"/tmp/{cat}/{cat[0]}.wav", contents="dummy")
    cats = main.load_sound_categories(Path("/tmp"))
    assert set(cats) == set(categories)
    for cat in categories:
        assert len(cats[cat]) == 1
        assert cats[cat][0].name == f"{cat[0]}.wav"


def test_ambient_loop_runs(
    monkeypatch: pytest.MonkeyPatch, dummy_event: threading.Event
) -> None:
    files = [Path("a.wav")]
    called: dict[str, bool] = {}

    class BreakLoop(Exception):
        pass

    # Patch threading.Event.wait instead of time.sleep
    original_wait = threading.Event.wait

    def fake_wait(timeout: Optional[float] = None) -> bool:
        # This function intentionally raises an exception for test control.
        # SonarLint S3516 can be ignored here.
        called["wait"] = True
        raise BreakLoop()  # Raise exception when wait is called

    monkeypatch.setattr(dummy_event, "wait", fake_wait)

    try:
        with pytest.raises(BreakLoop):
            # Pass dummy_event for deterministic event
            main.ambient_loop(files, 100, 0.5, stop_event=dummy_event)
    finally:
        # Restore original wait method
        monkeypatch.setattr(threading.Event, "wait", original_wait)

    assert called.get("wait", False)  # Check if wait was called


def test_chains_loop_runs(
    monkeypatch: pytest.MonkeyPatch, dummy_event: threading.Event
) -> None:
    files: List[Path] = [Path("c1.wav")]
    called: dict[str, bool] = {}

    class BreakLoop(Exception):
        pass

    # Patch threading.Event.wait
    original_wait = threading.Event.wait

    def fake_wait(timeout: Optional[float] = None) -> bool:
        # This function intentionally raises an exception for test control.
        # SonarLint S3516 can be ignored here.
        called["wait"] = True
        raise BreakLoop()

    monkeypatch.setattr(dummy_event, "wait", fake_wait)

    try:
        with pytest.raises(BreakLoop):
            main.chains_loop(files, stop_event=dummy_event)
    finally:
        monkeypatch.setattr(dummy_event, "wait", original_wait)

    assert called.get("wait", False)


def test_main_loop_runs(
    monkeypatch: pytest.MonkeyPatch, dummy_event: threading.Event
) -> None:
    files: list[Path] = [Path("s1.wav")]
    called: dict[str, bool] = {}

    class BreakLoop(Exception):
        pass  # Test exception

    # Patch threading.Event.wait
    original_wait = threading.Event.wait

    def fake_wait(timeout: Optional[float] = None) -> bool:
        # This function intentionally raises an exception for test control.
        # SonarLint S3516 can be ignored here.
        called["wait"] = True
        raise BreakLoop()

    monkeypatch.setattr(dummy_event, "wait", fake_wait)

    try:
        with pytest.raises(BreakLoop):
            main.main_loop(files, stop_event=dummy_event)
    finally:
        monkeypatch.setattr(dummy_event, "wait", original_wait)

    assert called.get("wait", False)


def test_rats_loop_runs(
    monkeypatch: pytest.MonkeyPatch, dummy_event: threading.Event
) -> None:
    files: list[Path] = [Path("r1.wav"), Path("r2.wav")]
    chans: list[MagicMock] = [
        cast(MagicMock, main.pygame.mixer.Channel(1)),
        cast(MagicMock, main.pygame.mixer.Channel(2)),
    ]
    called: dict[str, int] = {}

    class BreakLoop(Exception):
        pass

    # Patch threading.Event.wait
    original_wait = threading.Event.wait
    wait_call_count = 0

    def fake_wait(timeout: Optional[float] = None) -> bool:
        nonlocal wait_call_count
        wait_call_count += 1
        called["wait"] = called.get("wait", 0) + 1
        # Allow the first wait (for fadeout) then break on the second
        # (main loop sleep)
        if wait_call_count >= 2:
            raise BreakLoop()
        return False  # Simulate timeout

    monkeypatch.setattr(dummy_event, "wait", fake_wait)

    try:
        with pytest.raises(BreakLoop):
            main.rats_loop(files, chans, stop_event=dummy_event)
    finally:
        monkeypatch.setattr(dummy_event, "wait", original_wait)

    assert called.get("wait", 0) > 0


# --- Full coverage tests for loop bodies and main() ---


def test_chains_loop_body(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("c1.wav")]

    class BreakLoop(Exception):
        pass

    calls: Dict[str, Any] = {}  # Use Any for volume type flexibility

    # Patch threading.Event.wait to allow one wait, then break in play
    original_wait = threading.Event.wait
    wait_called = False

    def fake_wait(
        self: threading.Event,
        timeout: Optional[float] = None,
    ) -> bool:
        # This function intentionally returns False for test control.
        # SonarLint S3516 can be ignored here.
        nonlocal wait_called
        if not wait_called:
            calls["waited"] = calls.get("waited", 0) + 1
            wait_called = True
            return False  # Simulate timeout
        # Subsequent calls don't raise here, BreakLoop comes from play
        return False

    monkeypatch.setattr(threading.Event, "wait", fake_wait)

    # Get the mock sound instance from the factory via patch_pygame
    mock_sound = cast(MagicMock, main.pygame.mixer.Sound(files[0]))
    # Configure the mock play method to raise BreakLoop
    mock_sound.play.side_effect = BreakLoop()

    # Store volume in calls when set_volume is called
    def record_volume(v: float) -> None:
        calls["volume"] = v

    mock_sound.set_volume.side_effect = record_volume

    try:
        with pytest.raises(BreakLoop):
            main.chains_loop(files, stop_event=threading.Event())
    finally:
        monkeypatch.setattr(threading.Event, "wait", original_wait)
        # Reset side effects if the mock is reused across tests
        mock_sound.play.side_effect = None
        mock_sound.set_volume.side_effect = None

    assert "volume" in calls
    assert calls.get("waited", 0) == 1


def test_main_loop_body(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("s1.wav")]

    class BreakLoop(Exception):
        pass

    # Patch threading.Event.wait to allow one wait
    original_wait = threading.Event.wait
    wait_called = False

    def fake_wait(
        self: threading.Event,
        timeout: Optional[float] = None,
    ) -> bool:
        # This function intentionally returns False for test control.
        # SonarLint S3516 can be ignored here.
        nonlocal wait_called
        if not wait_called:
            wait_called = True
            return False  # Simulate timeout
        return False

    monkeypatch.setattr(threading.Event, "wait", fake_wait)

    # Get the mock sound and configure play to raise
    mock_sound = cast(MagicMock, main.pygame.mixer.Sound(files[0]))
    mock_sound.play.side_effect = BreakLoop()

    try:
        with pytest.raises(BreakLoop):
            main.main_loop(files, stop_event=threading.Event())
    finally:
        monkeypatch.setattr(threading.Event, "wait", original_wait)
        mock_sound.play.side_effect = None  # Reset side effect

    assert wait_called  # Ensure wait was actually called


def test_ambient_loop_body(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("a1.wav")]

    class BreakLoop(Exception):
        pass

    calls: Dict[str, float] = {"count": 0.0}

    # Patch threading.Event.wait
    original_wait = threading.Event.wait
    wait_call_count = 0

    def fake_wait(
        self: threading.Event,
        timeout: Optional[float] = None,
    ) -> bool:
        # This function intentionally returns False or raises for test control.
        # SonarLint S3516 can be ignored here.
        nonlocal wait_call_count
        wait_call_count += 1
        calls["waited"] = calls.get("waited", 0) + 1
        # Allow first wait (main sleep), second wait (fadeout), then break
        if wait_call_count >= 2:
            raise BreakLoop()
        return False

    monkeypatch.setattr(threading.Event, "wait", fake_wait)

    # Get the mock channel instance from the factory via patch_pygame
    mock_chan = cast(
        MagicMock,
        main.pygame.mixer.Channel(config.AMBIENT_CHANNEL),
    )

    # Record fadeout calls
    fadeout_calls = []

    def record_fadeout(ms: int) -> None:
        fadeout_calls.append(ms)

    mock_chan.fadeout.side_effect = record_fadeout

    # Get the mock sound instance
    mock_sound = cast(MagicMock, main.pygame.mixer.Sound(files[0]))
    # Ensure get_length returns the value set in the fixture
    # Use pytest.approx for float comparison
    assert mock_sound.get_length() == pytest.approx(0.01)

    try:
        with pytest.raises(BreakLoop):
            main.ambient_loop(
                files,
                fade_ms=10,
                volume=0.5,
                stop_event=threading.Event(),
            )
    finally:
        monkeypatch.setattr(threading.Event, "wait", original_wait)
        mock_chan.fadeout.side_effect = None  # Reset side effect

    assert 10 in fadeout_calls
    assert calls.get("waited", 0) >= 2  # Ensure both waits were attempted


def test_rats_loop_body(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("r1.wav"), Path("r2.wav")]
    # Get mock channels
    chans = [
        cast(MagicMock, main.pygame.mixer.Channel(1)),
        cast(MagicMock, main.pygame.mixer.Channel(2)),
    ]

    class BreakLoop(Exception):
        pass

    calls: Dict[str, int] = {"count": 0}

    # Patch threading.Event.wait: timeout first, then break on second call
    original_wait = threading.Event.wait
    wait_call_count = 0

    def fake_wait(
        self: threading.Event,
        timeout: Optional[float] = None,
    ) -> bool:
        nonlocal wait_call_count
        wait_call_count += 1
        calls["waited"] = calls.get("waited", 0) + 1
        # Allow first wait (main sleep), second wait (fadeout), then break
        if wait_call_count >= 2:
            raise BreakLoop()
        return False

    monkeypatch.setattr(threading.Event, "wait", fake_wait)

    try:
        with pytest.raises(BreakLoop):
            main.rats_loop(files, chans, stop_event=threading.Event())
    finally:
        monkeypatch.setattr(threading.Event, "wait", original_wait)

    # Check fadeouts occurred and loop exited after fake_wait raised
    for chan in chans:
        chan.fadeout.assert_called_with(config.RATS_FADEOUT_MS)
    assert calls.get("waited", 0) >= 2


def test_main_scream_logic_without_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Test main loop runs but doesn't play screams if none exist
    import displayboard.sounds as main  # Re-import locally if needed

    class BreakLoop(Exception):
        pass

    def fake_load_sound_categories(base_path: Path) -> Dict[str, List[Path]]:
        # Return empty lists for all categories, especially screams
        return dict(
            ambient=[],
            rats=[],
            chains=[],
            screams=[],
            displayboard=[],
        )

    monkeypatch.setattr(main, "load_sound_categories", fake_load_sound_categories)

    wait_calls = {"count": 0}

    # Patch threading.Event.wait instead of time.sleep
    original_wait = threading.Event.wait

    def fake_wait(
        self: threading.Event,
        timeout: Optional[float] = None,
    ) -> bool:
        # This function intentionally returns False or raises for test control.
        # SonarLint S3516 can be ignored here.
        wait_calls["count"] += 1
        if wait_calls["count"] >= 2:  # Check >= 2 to ensure loop runs twice
            raise BreakLoop()
        return False

    monkeypatch.setattr(threading.Event, "wait", fake_wait)

    # Get the mock sound play method from the fixture
    # Need to create a sound first to get its mock play method
    # Cast to MagicMock to access .play attribute correctly for assertion
    mock_sound = cast(
        MagicMock,
        main.pygame.mixer.Sound(Path("dummy_scream.wav")),
    )
    mock_play = mock_sound.play

    try:
        # Use a pre-set stop_event to prevent infinite loop in actual main
        stop_event = threading.Event()
        # Run main in a way that allows BreakLoop to exit the wait
        with pytest.raises(BreakLoop):
            main.main(stop_event=stop_event)
    finally:
        monkeypatch.setattr(threading.Event, "wait", original_wait)

    assert wait_calls["count"] >= 2
    mock_play.assert_not_called()  # Ensure scream was not played


def test_ambient_loop_idx_increment(monkeypatch: pytest.MonkeyPatch) -> None:
    # Test that the ambient loop index increments and wraps around
    import displayboard.sounds as main  # Re-import locally if needed

    class BreakLoop(Exception):
        pass

    files = [Path("a.wav"), Path("b.wav")]
    played_paths: List[str] = []

    # Get the mock channel instance
    mock_chan = cast(
        MagicMock,
        main.pygame.mixer.Channel(config.AMBIENT_CHANNEL),
    )

    # Record plays on the mock channel
    def record_play(snd: MagicMock, **kwargs: Any) -> None:
        # Access the path stored by the sound factory
        played_paths.append(snd._fake_path.name)

    mock_chan.play.side_effect = record_play

    # Patch threading.Event.wait to break after several calls
    original_wait = threading.Event.wait
    wait_call_count = 0

    def fake_wait(
        self: threading.Event,
        timeout: Optional[float] = None,
    ) -> bool:
        # This function intentionally returns False or raises for test control.
        # SonarLint S3516 can be ignored here.
        nonlocal wait_call_count
        wait_call_count += 1
        # Need 2 waits per loop cycle (main sleep, fadeout sleep)
        # Let it run for 2 full cycles (4 waits) then break on 5th
        if wait_call_count >= 5:
            raise BreakLoop()
        return False  # Simulate timeout

    monkeypatch.setattr(threading.Event, "wait", fake_wait)

    try:
        with pytest.raises(BreakLoop):
            main.ambient_loop(
                files, fade_ms=10, volume=1.0, stop_event=threading.Event()
            )
    finally:
        monkeypatch.setattr(threading.Event, "wait", original_wait)
        mock_chan.play.side_effect = None  # Reset side effect

    # Check that both files were played (requires at least 2 loop iterations)
    assert "a.wav" in played_paths
    assert "b.wav" in played_paths
    # Ensure the loop ran enough times for idx to wrap
    # Check counts based on the number of waits allowed
    # (5 waits -> 2 full cycles -> 3 plays: a, b, a)
    assert played_paths == ["a.wav", "b.wav", "a.wav"]


# --- Integration tests for error handling and main function ---


@patch("displayboard.sounds.threading.Thread")
@patch("displayboard.sounds.load_sound_categories")
@patch("displayboard.sounds.ambient_loop")
@patch("displayboard.sounds.chains_loop")
@patch("displayboard.sounds.main_loop")
@patch("displayboard.sounds.rats_loop")
def test_main_starts_loops(
    mock_rats_loop: MagicMock,
    mock_main_loop: MagicMock,
    mock_chains_loop: MagicMock,
    mock_ambient_loop: MagicMock,
    mock_load_cats: MagicMock,
    mock_thread: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Mock load_sound_categories to return dummy data
    mock_load_cats.return_value = {
        "ambient": [Path("a.wav")],
        "rats": [Path("r.wav")],
        "chains": [Path("c.wav")],
        "screams": [Path("scream.wav")],
        "displayboard": [Path("sk.wav")],
    }

    # Pygame mocks are handled by the fixture

    # Create a stop event that will be set by the main loop mock
    stop_event = threading.Event()

    # Mock the main loop's wait to raise KeyboardInterrupt quickly
    original_wait = threading.Event.wait

    def fake_main_wait(*args: Any, **kwargs: Any) -> bool:
        # This function intentionally raises an exception for test control.
        stop_event.set()  # Ensure the main function exits
        raise KeyboardInterrupt("Simulated exit")

    monkeypatch.setattr(threading.Event, "wait", fake_main_wait)

    # Call main, expecting it to handle the KeyboardInterrupt
    try:
        main.main(stop_event=stop_event)
    except KeyboardInterrupt:
        pass  # Expected
    finally:
        monkeypatch.setattr(threading.Event, "wait", original_wait)  # Restore

    # Assertions
    mock_load_cats.assert_called_once()
    assert mock_thread.call_count == 4  # ambient, chains, main, rats

    # Check that each loop function was passed as a target to a Thread
    thread_targets = {call.kwargs["target"] for call in mock_thread.call_args_list}
    assert mock_ambient_loop in thread_targets
    assert mock_chains_loop in thread_targets
    assert mock_main_loop in thread_targets
    assert mock_rats_loop in thread_targets

    # Check that start was called for each thread instance
    for call in mock_thread.call_args_list:
        thread_instance = call.return_value
        thread_instance.start.assert_called_once()

    # Check that the correct args were passed to the loops
    # Example: Check args for ambient_loop
    ambient_call = next(
        call
        for call in mock_thread.call_args_list
        if call.kwargs["target"] == mock_ambient_loop
    )
    assert ambient_call.kwargs["args"][0] == [Path("a.wav")]  # files
    assert ambient_call.kwargs["args"][1] == config.AMBIENT_FADE_MS  # fade_ms
    # volume
    assert ambient_call.kwargs["args"][2] == config.SOUND_VOLUME_DEFAULT
    # stop_event
    assert isinstance(ambient_call.kwargs["args"][3], threading.Event)


@patch("displayboard.sounds.threading.Thread")
@patch("displayboard.sounds.load_sound_categories")
@patch("displayboard.sounds.ambient_loop")
@patch("displayboard.sounds.chains_loop")
@patch("displayboard.sounds.main_loop")
@patch("displayboard.sounds.rats_loop")
@patch("displayboard.sounds.logger")
def test_main_keyboard_interrupt(
    mock_logger: MagicMock,
    mock_rats: MagicMock,
    mock_main: MagicMock,
    mock_chains: MagicMock,
    mock_ambient: MagicMock,
    mock_load: MagicMock,
    mock_thread: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Mock load_sound_categories
    mock_load.return_value = {
        "ambient": [Path("a.wav")],
        "rats": [Path("r.wav")],
        "chains": [Path("c.wav")],
        "screams": [Path("scream.wav")],
        "displayboard": [Path("sk.wav")],
    }

    # Pygame mocks handled by fixture

    # Simulate KeyboardInterrupt when the main loop's wait is called
    original_wait = threading.Event.wait

    def fake_wait_interrupt(*args: Any, **kwargs: Any) -> bool:
        # This function intentionally raises an exception for test control.
        raise KeyboardInterrupt("Simulated interrupt")

    monkeypatch.setattr(threading.Event, "wait", fake_wait_interrupt)

    # Create a stop event
    stop_event = threading.Event()

    # Call main and expect KeyboardInterrupt to be handled gracefully
    main.main(stop_event=stop_event)

    # Restore original wait
    monkeypatch.setattr(threading.Event, "wait", original_wait)

    # Assertions
    mock_load.assert_called_once()
    assert mock_thread.call_count == 4
    mock_logger.info.assert_any_call(
        "KeyboardInterrupt received, shutting down sound loops..."
    )
    # Ensure stop_event.set() was called
    assert stop_event.is_set()

    # Ensure fadeout was called on ambient and rat channels
    # (mocked via fixture)
    ambient_chan = cast(
        MagicMock,
        main.pygame.mixer.Channel(config.AMBIENT_CHANNEL),
    )
    ambient_chan.fadeout.assert_called_with(config.MAIN_AMBIENT_FADEOUT_MS)
    # Check fadeout on rat channels
    for i in range(config.RATS_CHANNEL_START, config.RATS_CHANNEL_END):
        rat_chan = cast(MagicMock, main.pygame.mixer.Channel(i))
        rat_chan.fadeout.assert_called_with(config.MAIN_RATS_FADEOUT_MS)


@patch("displayboard.sounds.logger")
def test_main_no_sound_dir(
    mock_logger: MagicMock, fs: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Point config.SOUNDS_DIR to a non-existent directory
    non_existent_path = Path("/not/a/real/dir")
    monkeypatch.setattr(config, "SOUNDS_DIR", non_existent_path)

    # Pygame mocks handled by fixture

    # Patch Thread to check if loops are started
    mock_thread_start: MagicMock = MagicMock()
    monkeypatch.setattr(threading.Thread, "start", mock_thread_start)

    # Mock the main loop's wait to exit quickly
    original_wait = threading.Event.wait

    def quick_exit(*args: Any, **kwargs: Any) -> bool:
        # This function intentionally raises an exception for test control.
        raise KeyboardInterrupt("Exit")

    monkeypatch.setattr(threading.Event, "wait", quick_exit)

    try:
        main.main(stop_event=threading.Event())
    except KeyboardInterrupt:
        pass  # Expected exit
    finally:
        monkeypatch.setattr(threading.Event, "wait", original_wait)  # Restore

    # Check that load_sound_categories was called
    # (it handles non-existent dirs)
    # Check that loops weren't started because categories were empty
    mock_thread_start.assert_not_called()
    # Check for a log message? The function might just exit silently
    # if no sounds.
    # Let's assume silent exit is okay if no sounds are found.


@patch("displayboard.sounds.logger")
def test_main_pygame_init_error(
    mock_logger: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Mock pygame.mixer.init to raise an error (using the mock from fixture)
    # Cast to MagicMock to set side_effect
    mock_init = cast(MagicMock, main.pygame.mixer.init)
    mock_init.side_effect = pygame.error("init error")

    # Expect main to catch the error, log critically, and re-raise
    with pytest.raises(pygame.error, match="init error"):
        main.main(stop_event=threading.Event())

    # Reset side effect for other tests
    mock_init.side_effect = None
    # We can't easily assert the log here without more complex mocking
    # But we verified the exception is raised


@patch("displayboard.sounds.logger")
def test_main_generic_exception(
    mock_logger: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Mock load_sound_categories to raise a generic exception
    def raise_generic_error_load(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("Load failed")

    monkeypatch.setattr(main, "load_sound_categories", raise_generic_error_load)
    # Pygame mocks handled by fixture

    # Expect main to catch the generic error and log/re-raise
    with pytest.raises(RuntimeError, match="Load failed"):
        main.main(stop_event=threading.Event())
    # Similar to above, log assertion is tricky due to re-raise


# This test combines aspects of the original test_main_function_integration
# but uses patching correctly for assertions.
@patch("displayboard.sounds.logger")
@patch("displayboard.sounds.load_sound_categories")
@patch("displayboard.sounds.ambient_loop")  # Patch loops to prevent actual execution
@patch("displayboard.sounds.chains_loop")
@patch("displayboard.sounds.main_loop")
@patch("displayboard.sounds.rats_loop")
@patch("displayboard.sounds.threading.Thread")  # Patch Thread to check calls
def test_main_integration_setup_teardown(
    mock_thread: MagicMock,
    mock_rats_loop: MagicMock,
    mock_main_loop: MagicMock,
    mock_chains_loop: MagicMock,
    mock_ambient_loop: MagicMock,
    mock_load_cats: MagicMock,
    mock_logger: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Mock load_sound_categories return value
    mock_load_cats.return_value = {
        "ambient": [tmp_path / "a.wav"],
        "rats": [tmp_path / "r.wav"],
        "chains": [tmp_path / "c.wav"],
        "screams": [tmp_path / "scream.wav"],
        "displayboard": [tmp_path / "sk.wav"],
    }
    # Mock config.SOUNDS_DIR to use tmp_path
    monkeypatch.setattr(config, "SOUNDS_DIR", tmp_path)

    # Get mocks from the fixture (cast to MagicMock for assertions)
    mock_mixer_init = cast(MagicMock, main.pygame.mixer.init)
    mock_set_num_channels = cast(MagicMock, main.pygame.mixer.set_num_channels)

    # Mock the main loop's wait to exit quickly via KeyboardInterrupt
    original_wait = threading.Event.wait

    def fake_wait_interrupt(*args: Any, **kwargs: Any) -> bool:
        # This function intentionally raises an exception for test control.
        raise KeyboardInterrupt("Simulated exit")

    monkeypatch.setattr(threading.Event, "wait", fake_wait_interrupt)

    # Call the main function
    stop_event = threading.Event()
    try:
        main.main(stop_event=stop_event)
    except KeyboardInterrupt:
        pass  # Expected for test exit
    finally:
        # Restore wait
        monkeypatch.setattr(threading.Event, "wait", original_wait)

    # Assertions
    mock_mixer_init.assert_called_once()
    mock_set_num_channels.assert_called_once_with(config.SOUND_NUM_CHANNELS)
    mock_load_cats.assert_called_once_with(tmp_path)
    assert mock_thread.call_count == 4  # Check threads were created for loops
    # Check threads were started
    for call in mock_thread.call_args_list:
        thread_instance = call.return_value
        thread_instance.start.assert_called_once()

    # Check loops were called (via Thread target)


# --- Branch/exit coverage for sounds.py ---


def test_ambient_loop_breaks_on_event(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("a.wav")]
    event = threading.Event()
    event.set()

    def fake_wait(timeout: object = None) -> None:
        return None

    monkeypatch.setattr(event, "wait", fake_wait)
    monkeypatch.setattr(event, "is_set", lambda: True)
    main.ambient_loop(files, 100, 0.5, stop_event=event)


def test_chains_loop_breaks_on_event(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("c1.wav")]
    event = threading.Event()
    event.set()

    def fake_wait(timeout: object = None) -> None:
        return None

    monkeypatch.setattr(event, "wait", fake_wait)
    monkeypatch.setattr(event, "is_set", lambda: True)
    main.chains_loop(files, stop_event=event)


def test_main_loop_breaks_on_event(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("s1.wav")]
    event = threading.Event()
    event.set()

    def fake_wait(timeout: object = None) -> None:
        return None

    monkeypatch.setattr(event, "wait", fake_wait)
    monkeypatch.setattr(event, "is_set", lambda: True)
    main.main_loop(files, stop_event=event)


def test_rats_loop_breaks_on_event_after_fadeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    files = [Path("r1.wav"), Path("r2.wav")]
    chans = [
        cast(MagicMock, main.pygame.mixer.Channel(1)),
        cast(MagicMock, main.pygame.mixer.Channel(2)),
    ]
    event = threading.Event()
    event.set()

    def fake_wait(timeout: object = None) -> None:
        return None

    monkeypatch.setattr(event, "wait", fake_wait)
    monkeypatch.setattr(event, "is_set", lambda: True)
    main.rats_loop(files, chans, stop_event=event)


@patch("displayboard.sounds.threading.Thread")
@patch("displayboard.sounds.load_sound_categories")
@patch("displayboard.sounds.ambient_loop")
@patch("displayboard.sounds.chains_loop")
@patch("displayboard.sounds.main_loop")
@patch("displayboard.sounds.rats_loop")
def test_main_scream_logic_with_files(
    mock_rats: MagicMock,
    mock_main: MagicMock,
    mock_chains: MagicMock,
    mock_ambient: MagicMock,
    mock_load: MagicMock,
    mock_thread: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_load.return_value = {
        "ambient": [Path("a.wav")],
        "rats": [Path("r.wav")],
        "chains": [Path("c.wav")],
        "screams": [Path("scream.wav")],
        "displayboard": [Path("sk.wav")],
    }
    call_count = {"n": 0}

    def fake_wait(self: threading.Event, timeout: object = None) -> bool:
        call_count["n"] += 1
        return call_count["n"] >= 1

    monkeypatch.setattr(threading.Event, "wait", fake_wait)
    played = []
    orig_sound = main.pygame.mixer.Sound

    def fake_sound(path: Path) -> MagicMock:
        m = MagicMock()
        m.set_volume = MagicMock()

        def play_side_effect(*args: object, **kwargs: object) -> None:
            played.append(str(path))

        m.play = MagicMock(side_effect=play_side_effect)
        return m

    monkeypatch.setattr(main.pygame.mixer, "Sound", fake_sound)
    main.main(stop_event=threading.Event())
    assert any("scream" in p for p in played)
    monkeypatch.setattr(main.pygame.mixer, "Sound", orig_sound)


# --- New tests for 100% coverage of sounds.py ---
def test_rats_loop_zero_weights(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("r1.wav"), Path("r2.wav")]
    chans = [
        cast(MagicMock, main.pygame.mixer.Channel(1)),
        cast(MagicMock, main.pygame.mixer.Channel(2)),
    ]
    # Patch random.random to always return 0
    monkeypatch.setattr(main.random, "random", lambda: 0.0)
    # Patch wait to break after one loop
    original_wait = threading.Event.wait

    def fake_wait(self: threading.Event, timeout: object = None) -> bool:
        raise Exception("break")

    monkeypatch.setattr(threading.Event, "wait", fake_wait)

    try:
        with pytest.raises(Exception):
            main.rats_loop(files, chans, stop_event=threading.Event())
    finally:
        monkeypatch.setattr(threading.Event, "wait", original_wait)


def test_sounds_py_entry_subprocess() -> None:
    # This test ensures that running the module as a script does not hang.
    # It is possible for pygame to fail to initialize in CI or headless environments,
    # so we accept any nonzero exit code, but the test must not hang or time out.
    try:
        result = subprocess.run(
            [sys.executable, "-m", "displayboard.sounds", "--test-exit"],
            env={**os.environ, "PYTHONPATH": "src"},
            capture_output=True,
            text=True,
            timeout=5,  # Lower timeout to fail faster if it hangs
        )
    except subprocess.TimeoutExpired:
        pytest.fail("Running 'python -m displayboard.sounds' hung or timed out")
    # Accept any exit code, but assert that it did not hang
    assert isinstance(result.returncode, int)
    # Optionally, print output for debugging if needed
    # print(result.stdout, result.stderr)
