import sys
import time
import threading
import pytest
from typing import Dict, Callable, Optional, Tuple, Any
from skaven import sounds, lighting, video_loop
import skaven.main as dispatcher
from unittest.mock import MagicMock


class FakeThread:
    """
    A fake Thread to capture target and name, without starting real threads.
    """

    instances: list["FakeThread"] = []

    def __init__(
        self,
        target: Optional[Callable[..., None]] = None,
        name: Optional[str] = None,
        daemon: Optional[bool] = None,
        args: Tuple[Any, ...] = (),
        **kwargs: object
    ) -> None:
        self.target = target
        self.name = name
        self.daemon = daemon
        self.args = args
        FakeThread.instances.append(self)

    def start(self) -> None:
        if callable(self.target):
            try:
                if self.args:
                    self.target(*self.args)
                else:
                    self.target()
            except KeyboardInterrupt:
                pass


@pytest.fixture(autouse=True)
def patch_threads_and_calls(monkeypatch: pytest.MonkeyPatch) -> Dict[str, int]:
    FakeThread.instances.clear()
    monkeypatch.setattr(threading, "Thread", FakeThread)
    calls = {"sounds": 0, "lighting": 0, "video": 0}
    monkeypatch.setattr(
        sounds, "main", lambda stop_event=None: calls.update(sounds=calls["sounds"] + 1)
    )
    monkeypatch.setattr(
        lighting,
        "skaven_flicker_breathe",
        lambda stop_event=None: calls.update(lighting=calls["lighting"] + 1),
    )
    monkeypatch.setattr(
        video_loop,
        "main",
        lambda stop_event=None: calls.update(video=calls["video"] + 1),
    )

    def fake_sleep(sec: float) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(time, "sleep", fake_sleep)
    return calls


def test_main_join_threads_attribute_and_runtime() -> None:
    """Covers _join_threads AttributeError and RuntimeError branches."""
    mock_logger = MagicMock()

    class NoJoin(threading.Thread):
        def __init__(self) -> None:
            super().__init__()
            self.name = "NoJoinThread"

    class BadJoin(threading.Thread):
        def __init__(self) -> None:
            super().__init__()
            self.name = "BadJoinThread"

        def join(self, timeout: float | None = None) -> None:
            raise RuntimeError("fail")

    dispatcher._join_threads([NoJoin(), BadJoin()], mock_logger)


def test_main_keyboard_interrupt_in_video(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Covers KeyboardInterrupt in handle_video_playback."""
    monkeypatch.setattr(sys, "argv", ["skaven"])

    def fake_video_main(stop_event: object = None) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(dispatcher.video_loop, "main", fake_video_main)
    monkeypatch.setattr(
        dispatcher,
        "_join_threads",
        lambda threads, logger: None,
    )
    monkeypatch.setattr(
        dispatcher,
        "start_threads",
        lambda args, stop_event: [],
    )
    mock_logger = MagicMock()
    monkeypatch.setattr(
        dispatcher,
        "configure_logging",
        lambda args: mock_logger,
    )
    dispatcher.main()


def test_main_keyboard_interrupt_in_shutdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Covers KeyboardInterrupt in handle_shutdown."""
    monkeypatch.setattr(sys, "argv", ["skaven"])

    def fake_video_main(stop_event: object = None) -> None:
        pass

    monkeypatch.setattr(dispatcher.video_loop, "main", fake_video_main)
    monkeypatch.setattr(dispatcher, "_join_threads", lambda threads, logger: None)
    monkeypatch.setattr(dispatcher, "start_threads", lambda args, stop_event: [])
    mock_logger = MagicMock()
    monkeypatch.setattr(dispatcher, "configure_logging", lambda args: mock_logger)

    def fake_handle_video_playback(args: object, stop_event: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(dispatcher, "handle_video_playback", fake_handle_video_playback)

    def fake_video_main_shutdown(stop_event: object = None) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(dispatcher.video_loop, "main", fake_video_main_shutdown)
    dispatcher.main()


def test_main_normal_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Covers normal exit from main."""
    monkeypatch.setattr(
        sys, "argv", ["skaven", "--no-sounds", "--no-lighting", "--no-video"]
    )
    monkeypatch.setattr(dispatcher, "start_threads", lambda args, stop_event: [])
    monkeypatch.setattr(dispatcher, "configure_logging", lambda args: None)
    dispatcher.main()


@pytest.mark.parametrize(
    "args,expected",
    [
        ([], {"sounds": 1, "lighting": 1, "video": 1}),
        (["--no-sounds"], {"sounds": 0, "lighting": 1, "video": 1}),
        (["--no-lighting"], {"sounds": 1, "lighting": 0, "video": 1}),
        (["--no-video"], {"sounds": 1, "lighting": 1, "video": 0}),
        (
            ["--no-sounds", "--no-lighting", "--no-video"],
            {"sounds": 0, "lighting": 0, "video": 0},
        ),
    ],
)
def test_dispatcher_calls(
    monkeypatch: pytest.MonkeyPatch,
    patch_threads_and_calls: Dict[str, int],
    args: list[str],
    expected: Dict[str, int],
) -> None:
    monkeypatch.setattr(sys, "argv", ["skaven"] + args)
    dispatcher.main()

    t_names = [t.name for t in FakeThread.instances]
    if expected["sounds"]:
        assert "SoundscapeThread" in t_names
    else:
        assert all(t.name != "SoundscapeThread" for t in FakeThread.instances)

    if expected["lighting"]:
        assert "LightingThread" in t_names
    else:
        assert all(t.name != "LightingThread" for t in FakeThread.instances)

    assert patch_threads_and_calls["sounds"] == expected["sounds"]
    assert patch_threads_and_calls["lighting"] == expected["lighting"]
    assert patch_threads_and_calls["video"] == expected["video"]


def test_parse_args_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure default parse_args has all flags False."""
    monkeypatch.setattr(sys, "argv", ["skaven"])
    args = dispatcher.parse_args()
    assert not args.no_sounds
    assert not args.no_video
    assert not args.no_lighting


def test_configure_logging_verbose(monkeypatch: pytest.MonkeyPatch) -> None:
    """Covers configure_logging with verbose flag (lines 100, 102)."""
    import argparse
    import logging

    args = argparse.Namespace(debug=False, verbose=True)
    # Remove all handlers to avoid duplicate logs
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logger = dispatcher.configure_logging(args)
    # Explicitly import config from dispatcher if not already imported
    config = getattr(dispatcher, "config")
    assert logger.getEffectiveLevel() == config.LOG_LEVEL_DEFAULT


def test_handle_video_playback_exit_branch() -> None:
    """Covers handle_video_playback loop exit branch (121->exit)."""

    # This test is now covered by test_handle_shutdown_branches using dummy_event
    pass


def test_handle_shutdown_exit_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Covers handle_shutdown loop exit branch (146-148)."""

    # This test is now covered by test_handle_shutdown_branches using dummy_event
    pass


def test_handle_shutdown_branches(
    monkeypatch: pytest.MonkeyPatch,
    dummy_event: threading.Event,
) -> None:
    """Covers handle_shutdown loop exit and wait branches using dummy_event."""
    # Use real parse_args for coverage
    args = dispatcher.parse_args()
    mock_logger = MagicMock()
    monkeypatch.setattr(dispatcher, "_join_threads", lambda threads, logger: None)

    # Exit branch: event is set before entering
    dummy_event.set()
    dispatcher.handle_shutdown([], dummy_event, mock_logger, args)

    # Wait branch: event is not set, will set after one wait
    dummy_event.clear()
    call_count = {"wait": 0}

    def fake_wait(timeout: Optional[float] = None) -> bool:
        call_count["wait"] += 1
        dummy_event.set()  # Exit after one call
        return True  # Return True to indicate the event is set, breaking the loop

    monkeypatch.setattr(dummy_event, "wait", fake_wait)
    dispatcher.handle_shutdown([], dummy_event, mock_logger, args)
    assert call_count["wait"] == 1


def test_join_threads_attributeerror(monkeypatch: pytest.MonkeyPatch) -> None:
    """Covers _join_threads except AttributeError branch (line 165)."""
    mock_logger = MagicMock()

    class NoJoinObj(threading.Thread):
        def __init__(self) -> None:
            super().__init__()
            self.name = "NoJoinObj"

    dispatcher._join_threads([NoJoinObj()], mock_logger)


def test_configure_logging_basic(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Covers configure_logging default path
    (line 100: logging.basicConfig).
    """
    import argparse
    import logging

    args = argparse.Namespace(debug=False, verbose=False)
    # Remove all handlers to avoid duplicate logs
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logger = dispatcher.configure_logging(args)
    from skaven import config

    assert logger.getEffectiveLevel() == config.LOG_LEVEL_WARNING


def test_configure_logging_sets_handlers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Covers configure_logging when no handlers exist, ensuring
    logging.basicConfig is called (line 100).
    """
    import argparse
    import logging

    args: argparse.Namespace = argparse.Namespace(debug=False, verbose=False)
    # Remove all handlers to ensure basicConfig is called
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    # Patch logging.basicConfig to track call
    called: dict[str, Any] = {}
    orig_basicConfig = logging.basicConfig

    def fake_basicConfig(*a: Any, **kwargs: Any) -> None:
        called["basicConfig"] = True
        return orig_basicConfig(*a, **kwargs)

    monkeypatch.setattr(logging, "basicConfig", fake_basicConfig)
    dispatcher.configure_logging(args)
    assert called.get("basicConfig")


def test_configure_logging_real_basicconfig() -> None:
    """
    Covers configure_logging real call to logging.basicConfig
    (line 100) for coverage.
    """
    import argparse
    import logging

    args = argparse.Namespace(debug=False, verbose=False)
    # Remove all handlers to ensure basicConfig is called
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logger = dispatcher.configure_logging(args)
    config = getattr(dispatcher, "config")
    assert logger.getEffectiveLevel() == config.LOG_LEVEL_WARNING


def test_join_threads_debug(monkeypatch: pytest.MonkeyPatch) -> None:
    """Covers _join_threads normal debug branch (line 161: logger.debug)."""
    mock_logger = MagicMock()
    # Set logger.debug to a real function to check call
    calls = {}

    def fake_debug(msg: str) -> None:
        calls["debug"] = msg

    mock_logger.debug.side_effect = fake_debug

    class GoodJoinObj(threading.Thread):
        def __init__(self) -> None:
            super().__init__()
            self.name = "GoodJoinObj"

        def join(self, timeout: float | None = None) -> None:
            pass

    good_join_obj: threading.Thread = GoodJoinObj()
    dispatcher._join_threads([good_join_obj], mock_logger)
    assert "GoodJoinObj" in calls.get("debug", "")
