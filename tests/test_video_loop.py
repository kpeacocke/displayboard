from typing import Optional
import sys
import types
import pytest
import platform
import threading
import displayboard.video_loop as video_loop


@pytest.fixture(autouse=True)
def patch_config(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyConfig:
        LOOP_WAIT_TIMEOUT = 0.01
        PROCESS_WAIT_TIMEOUT = 0.01
        VIDEO_FILE = "dummy.mp4"
        VIDEO_DISABLED = False

    monkeypatch.setattr(video_loop, "config", DummyConfig)


@pytest.mark.parametrize("platform_name", ["Linux", "Darwin", "Windows"])
def test_check_mpv_installed_linux_installed(
    monkeypatch: pytest.MonkeyPatch, platform_name: str
) -> None:
    import shutil

    monkeypatch.setattr(platform, "system", lambda: platform_name)
    monkeypatch.setattr(shutil, "which", lambda x: "/usr/bin/mpv")
    # Should not raise or exit
    video_loop.check_mpv_installed()


@pytest.mark.parametrize("platform_name", ["Linux", "Darwin", "Windows"])
def test_check_mpv_installed_linux_not_installed(
    monkeypatch: pytest.MonkeyPatch, platform_name: str
) -> None:
    import shutil

    monkeypatch.setattr(platform, "system", lambda: platform_name)
    monkeypatch.setattr(shutil, "which", lambda x: None)
    monkeypatch.setattr(
        sys,
        "exit",
        lambda code=1: (_ for _ in ()).throw(SystemExit(code)),
    )
    if platform_name in ("Linux", "Darwin"):
        with pytest.raises(SystemExit):
            video_loop.check_mpv_installed()
    else:
        # Should not raise SystemExit for non-Linux platforms
        video_loop.check_mpv_installed()


@pytest.mark.parametrize("platform_name", ["Linux", "Darwin", "Windows"])
def test_check_mpv_installed_non_linux(
    monkeypatch: pytest.MonkeyPatch, platform_name: str
) -> None:
    import shutil

    monkeypatch.setattr(platform, "system", lambda: platform_name)
    monkeypatch.setattr(shutil, "which", lambda x: "/usr/local/bin/mpv")
    # Should not raise or exit
    video_loop.check_mpv_installed()


def test_handle_video_process_starts_new(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dummy_proc = type("P", (), {"poll": lambda self: None, "pid": 12345})()
    popen_called = {}

    def dummy_popen(cmd: str) -> object:
        popen_called["called"] = True
        return dummy_proc

    monkeypatch.setattr(
        video_loop,
        "logger",
        types.SimpleNamespace(
            info=lambda *a, **k: None,
            debug=lambda *a, **k: None,
            error=lambda *a, **k: None,
            warning=lambda *a, **k: None,
        ),
    )
    import subprocess
    import time

    monkeypatch.setattr(subprocess, "Popen", dummy_popen)
    monkeypatch.setattr(video_loop, "subprocess", subprocess)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setattr(video_loop, "time", time)
    proc = video_loop.handle_video_process(None)
    assert popen_called["called"]
    assert proc is dummy_proc


def test_handle_video_process_file_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_fnf(cmd: str) -> None:
        raise FileNotFoundError()

    import subprocess

    monkeypatch.setattr(subprocess, "Popen", raise_fnf)
    monkeypatch.setattr(video_loop, "subprocess", subprocess)
    proc = video_loop.handle_video_process(None)
    assert proc is None


def test_handle_video_process_called_process_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: dict[str, bool] = {}

    def dummy_handle_process_error(process: object, e: Exception) -> None:
        called["called"] = True

    monkeypatch.setattr(
        video_loop,
        "logger",
        types.SimpleNamespace(
            info=lambda *a, **k: None,
            debug=lambda *a, **k: None,
            error=lambda *a, **k: None,
            warning=lambda *a, **k: None,
        ),
    )
    monkeypatch.setattr(video_loop, "handle_process_error", dummy_handle_process_error)

    import subprocess

    def raise_cpe(cmd: str) -> None:
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(subprocess, "Popen", raise_cpe)
    monkeypatch.setattr(video_loop, "subprocess", subprocess)
    video_loop.handle_video_process(None)
    assert called["called"]


def test_handle_video_process_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: dict[str, bool] = {}
    monkeypatch.setattr(
        video_loop,
        "logger",
        types.SimpleNamespace(
            info=lambda *a, **k: None,
            debug=lambda *a, **k: None,
            error=lambda *a, **k: None,
            warning=lambda *a, **k: None,
        ),
    )
    monkeypatch.setattr(
        video_loop,
        "handle_keyboard_interrupt",
        lambda: called.setdefault("called", True),
    )

    def raise_ki(cmd: str) -> None:
        raise KeyboardInterrupt()

    import subprocess

    monkeypatch.setattr(subprocess, "Popen", raise_ki)
    monkeypatch.setattr(video_loop, "subprocess", subprocess)
    proc = video_loop.handle_video_process(None)
    assert called["called"]
    assert proc is None


def test_handle_video_process_unexpected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: dict[str, bool] = {}
    monkeypatch.setattr(
        video_loop,
        "logger",
        types.SimpleNamespace(info=lambda *a, **k: None, error=lambda *a, **k: None),
    )

    monkeypatch.setattr(
        video_loop,
        "handle_unexpected_error",
        lambda p, e: called.setdefault("called", True),
    )

    def raise_exc(cmd: str) -> None:
        raise RuntimeError("fail")

    import subprocess

    monkeypatch.setattr(subprocess, "Popen", raise_exc)
    monkeypatch.setattr(video_loop, "subprocess", subprocess)
    video_loop.handle_video_process(None)
    assert called["called"]


def test_handle_process_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:

    import subprocess

    # Create a real Popen object using a harmless command
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(0.1)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    monkeypatch.setattr(
        video_loop,
        "logger",
        types.SimpleNamespace(error=lambda *a, **k: None),
    )
    import time

    monkeypatch.setattr(time, "sleep", lambda t: None)
    try:
        video_loop.handle_process_error(proc, Exception("fail"))
        out = capsys.readouterr().out
        assert "🔴 Error playing video" in out
    finally:
        proc.terminate()
        proc.wait()


def test_handle_keyboard_interrupt(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        video_loop, "logger", types.SimpleNamespace(info=lambda *a, **k: None)
    )
    video_loop.handle_keyboard_interrupt()
    out = capsys.readouterr().out
    assert "👋 Exiting" in out


def test_handle_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess

    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(0.1)"])
    monkeypatch.setattr(
        video_loop, "logger", types.SimpleNamespace(error=lambda *a, **k: None)
    )
    import time

    monkeypatch.setattr(time, "sleep", lambda t: None)
    try:
        video_loop.handle_unexpected_error(proc, Exception("fail"))
    finally:
        proc.terminate()
        proc.wait()


def test_cleanup_process_terminates(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess
    from unittest.mock import Mock

    terminated: dict[str, bool] = {}

    dummy_proc = Mock(spec=subprocess.Popen)
    dummy_proc.poll.return_value = None
    dummy_proc.terminate.side_effect = lambda: terminated.setdefault("terminated", True)
    dummy_proc.wait.side_effect = lambda timeout=None: terminated.setdefault(
        "waited", True
    )

    monkeypatch.setattr(
        video_loop,
        "logger",
        types.SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None),
    )
    video_loop.cleanup_process(dummy_proc)
    assert terminated.get("terminated")


def test_cleanup_process_kills_on_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess
    from unittest.mock import Mock

    killed: dict[str, bool] = {}

    dummy_proc = Mock(spec=subprocess.Popen)
    dummy_proc.poll.return_value = None
    dummy_proc.terminate.return_value = None
    dummy_proc.wait.side_effect = subprocess.TimeoutExpired(cmd="mpv", timeout=1)
    dummy_proc.kill.side_effect = lambda: killed.setdefault("killed", True)

    monkeypatch.setattr(
        video_loop,
        "logger",
        types.SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None),
    )
    video_loop.cleanup_process(dummy_proc)
    assert killed.get("killed")

    # Use Mock instead of DummyProc to match Popen signature and typing
    dummy_proc2 = Mock(spec=subprocess.Popen)
    dummy_proc2.poll.return_value = None

    def terminate() -> None:
        pass

    def wait(timeout: Optional[float] = None) -> None:
        raise subprocess.TimeoutExpired(cmd="mpv", timeout=1)

    def kill() -> None:
        killed.setdefault("killed", True)

    dummy_proc2.terminate.side_effect = terminate
    dummy_proc2.wait.side_effect = wait
    dummy_proc2.kill.side_effect = kill

    monkeypatch.setattr(
        video_loop,
        "logger",
        types.SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None),
    )
    video_loop.cleanup_process(dummy_proc2)
    assert killed.get("killed")


def test_cleanup_process_none(monkeypatch: pytest.MonkeyPatch) -> None:
    # Should do nothing
    video_loop.cleanup_process(None)
    # This test is now covered by test_run_video_loop_runs_once using dummy_event
    pass


def test_run_video_loop_runs_once(
    monkeypatch: pytest.MonkeyPatch,
    dummy_event: threading.Event,
) -> None:
    """Covers run_video_loop running once and returning dummy_proc."""
    called: dict[str, bool] = {}

    from unittest.mock import Mock
    import subprocess

    dummy_proc = Mock(spec=subprocess.Popen)

    def handle_video_process(proc: object) -> object:
        if not called:
            called["called"] = True
            return dummy_proc
        return None

    monkeypatch.setattr(video_loop, "is_headless_environment", lambda: False)
    monkeypatch.setattr(video_loop, "handle_video_process", handle_video_process)
    result = video_loop.run_video_loop(dummy_event)
    assert result is dummy_proc


def test_play_video_loop_calls_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: dict[str, bool] = {}
    monkeypatch.setattr(video_loop, "run_video_loop", lambda event: "proc")
    monkeypatch.setattr(
        video_loop,
        "cleanup_process",
        lambda proc: called.setdefault("cleanup", True),
    )
    video_loop.play_video_loop()
    assert called.get("cleanup")


def test_main_calls_all(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, bool] = {}
    monkeypatch.setattr(
        video_loop,
        "check_mpv_installed",
        lambda: called.setdefault("check", True),
    )
    monkeypatch.setattr(
        video_loop,
        "play_video_loop",
        lambda event: called.setdefault("play", True),
    )
    video_loop.main()
    assert called.get("check")
    assert called.get("play")


def test_run_video_loop_event_set(dummy_event: threading.Event) -> None:
    dummy_event.set()  # Event is set before entering loop
    result = video_loop.run_video_loop(dummy_event)
    assert result is None


def test_handle_video_process_returns_existing() -> None:
    import subprocess
    from unittest.mock import Mock

    proc = Mock(spec=subprocess.Popen)
    proc.poll.return_value = None
    # Should just return the same process
    assert video_loop.handle_video_process(proc) is proc


def test_cleanup_process_none_and_poll(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess
    from unittest.mock import Mock

    # Should do nothing if process is None
    video_loop.cleanup_process(None)
    # Should do nothing if poll() is not None
    dummy_proc = Mock(spec=subprocess.Popen)
    dummy_proc.poll.return_value = 1
    video_loop.cleanup_process(dummy_proc)


def test_cleanup_process_none_and_poll_2(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Should do nothing if process is None
    video_loop.cleanup_process(None)

    # Should do nothing if poll() is not None
    import subprocess
    from unittest.mock import Mock

    dummy_proc = Mock(spec=subprocess.Popen)
    dummy_proc.poll.return_value = 1
    video_loop.cleanup_process(dummy_proc)


def test_is_headless_environment_with_display(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test headless detection when DISPLAY is set."""
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

    class DummyConfig:
        VIDEO_DISABLED = False

    monkeypatch.setattr(video_loop, "config", DummyConfig)
    assert video_loop.is_headless_environment() is False


def test_is_headless_environment_with_wayland(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test headless detection when WAYLAND_DISPLAY is set."""
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")

    class DummyConfig:
        VIDEO_DISABLED = False

    monkeypatch.setattr(video_loop, "config", DummyConfig)
    assert video_loop.is_headless_environment() is False


def test_is_headless_environment_no_display(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test headless detection when no display variables are set."""
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

    class DummyConfig:
        VIDEO_DISABLED = False

    monkeypatch.setattr(video_loop, "config", DummyConfig)
    assert video_loop.is_headless_environment() is True


def test_is_headless_environment_explicitly_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test headless detection when VIDEO_DISABLED is True."""
    monkeypatch.setenv("DISPLAY", ":0")

    class DummyConfig:
        VIDEO_DISABLED = True

    monkeypatch.setattr(video_loop, "config", DummyConfig)
    assert video_loop.is_headless_environment() is True


def test_run_video_loop_skips_in_headless(
    monkeypatch: pytest.MonkeyPatch, dummy_event: threading.Event
) -> None:
    """Test run_video_loop returns None immediately in headless environment."""
    monkeypatch.setattr(video_loop, "is_headless_environment", lambda: True)

    result = video_loop.run_video_loop(dummy_event)
    assert result is None
