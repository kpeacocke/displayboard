import sys
import time
import threading
import pytest
from typing import Callable, Optional, Dict
from skaven import sounds, lighting, video_loop

import skaven.main as dispatcher


class FakeThread:
    """A fake Thread to capture target and name,
    without starting real threads."""

    instances: list["FakeThread"] = []

    def __init__(
        self,
        target: Optional[Callable[[], None]] = None,
        name: Optional[str] = None,
        daemon: Optional[bool] = None,
    ) -> None:
        self.target = target
        self.name = name
        self.daemon = daemon
        FakeThread.instances.append(self)

    def start(self) -> None:
        if callable(self.target):
            try:
                self.target()
            except KeyboardInterrupt:
                pass


@pytest.fixture(autouse=True)
def patch_threads_and_calls(monkeypatch: pytest.MonkeyPatch) -> Dict[str, int]:
    FakeThread.instances.clear()
    monkeypatch.setattr(threading, "Thread", FakeThread)

    calls: Dict[str, int] = {"sounds": 0, "lighting": 0, "video": 0}
    monkeypatch.setattr(
        sounds, "main", lambda: calls.update(sounds=calls["sounds"] + 1)
    )
    monkeypatch.setattr(
        lighting,
        "skaven_flicker_breathe",
        lambda: calls.update(lighting=calls["lighting"] + 1),
    )
    monkeypatch.setattr(
        video_loop, "main", lambda: calls.update(video=calls["video"] + 1)
    )

    def fake_sleep(sec: float) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(time, "sleep", fake_sleep)
    return calls


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
    """
    Ensure default parse_args has all flags False.
    """
    # Simulate clean command line invocation: `skaven`
    monkeypatch.setattr(sys, "argv", ["skaven"])

    args = dispatcher.parse_args()
    assert not args.no_sounds
    assert not args.no_video
    assert not args.no_lighting
