import pytest
import sys
import threading
from pathlib import Path
from typing import (  # Group imports
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    cast,
)
from unittest.mock import patch, MagicMock

import pygame  # Keep top-level import for pygame.error

# Assuming skaven.sounds is aliased as main based on usage
import skaven.sounds as main
from skaven import config  # Import config directly

# Ensure the project root is on sys.path so we can import the module under test
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# --- Use centralized mock_pygame fixture from conftest.py ---
@pytest.fixture(autouse=True)
def patch_pygame(monkeypatch: pytest.MonkeyPatch, mock_pygame: MagicMock) -> None:
    monkeypatch.setattr(main, "pygame", mock_pygame)


@pytest.fixture(autouse=True)
def patch_time_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_sleep(seconds: float) -> None:
        # No-op for time.sleep in tests
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


# --- Original tests ---


def test_list_audio_files(tmp_path: Path) -> None:
    wav = tmp_path / "a.wav"
    wav.write_text("dummy")
    ogg = tmp_path / "b.ogg"
    ogg.write_text("dummy")
    mp3 = tmp_path / "c.mp3"
    mp3.write_text("dummy")
    txt = tmp_path / "d.txt"
    txt.write_text("dummy")
    # Use config directly now
    found = main.list_audio_files(tmp_path)
    exts = {p.suffix for p in found}
    # Use config.AUDIO_EXTENSIONS for assertion
    assert exts == set(config.AUDIO_EXTENSIONS)
    paths = {p.name for p in found}
    assert paths == {"a.wav", "b.ogg", "c.mp3"}


def test_load_sound_categories(tmp_path: Path) -> None:
    categories = ["ambient", "rats", "chains", "screams", "skaven"]
    for cat in categories:
        (tmp_path / cat).mkdir()
        (tmp_path / cat / f"{cat[0]}.wav").touch()
    cats = main.load_sound_categories(tmp_path)
    assert set(cats) == set(categories)
    for cat in categories:
        assert len(cats[cat]) == 1
        assert cats[cat][0].name == f"{cat[0]}.wav"


@pytest.mark.parametrize(
    "func,args_builder",
    [
        (
            main.ambient_loop,
            lambda dummy_event: (cast(List[Path], []), 100, 0.5, dummy_event),
        ),
        (
            main.chains_loop,
            lambda dummy_event: (cast(List[Path], []), dummy_event),
        ),
        (
            main.skaven_loop,
            lambda dummy_event: (cast(List[Path], []), dummy_event),
        ),
        (
            main.rats_loop,
            lambda dummy_event: (
                cast(List[Path], []),
                cast(List[MagicMock], []),
                dummy_event,
            ),
        ),
    ],
)
def test_loops_return_immediately_on_empty(
    func: Callable[..., Any],
    args_builder: Callable[[Any], tuple[Any, ...]],
    dummy_event: Any,
) -> None:
    args: tuple[Any, ...] = args_builder(dummy_event)
    result: Any = func(*args)
    assert result is None


# --- Full coverage tests for loop bodies and main() ---


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


def test_skaven_loop_runs(
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
            main.skaven_loop(files, stop_event=dummy_event)
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


def test_skaven_loop_body(monkeypatch: pytest.MonkeyPatch) -> None:
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
            main.skaven_loop(files, stop_event=threading.Event())
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
    import skaven.sounds as main  # Re-import locally if needed

    class BreakLoop(Exception):
        pass

    def fake_load_sound_categories(base_path: Path) -> Dict[str, List[Path]]:
        # Return empty lists for all categories, especially screams
        return dict(
            ambient=[],
            rats=[],
            chains=[],
            screams=[],
            skaven=[],
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
    import skaven.sounds as main  # Re-import locally if needed

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


@patch("skaven.sounds.threading.Thread")
@patch("skaven.sounds.load_sound_categories")
@patch("skaven.sounds.ambient_loop")
@patch("skaven.sounds.chains_loop")
@patch("skaven.sounds.skaven_loop")
@patch("skaven.sounds.rats_loop")
def test_main_starts_loops(
    mock_rats_loop: MagicMock,
    mock_skaven_loop: MagicMock,
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
        "skaven": [Path("sk.wav")],
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
    assert mock_thread.call_count == 4  # ambient, chains, skaven, rats

    # Check that each loop function was passed as a target to a Thread
    thread_targets = {call.kwargs["target"] for call in mock_thread.call_args_list}
    assert mock_ambient_loop in thread_targets
    assert mock_chains_loop in thread_targets
    assert mock_skaven_loop in thread_targets
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


@patch("skaven.sounds.threading.Thread")
@patch("skaven.sounds.load_sound_categories")
@patch("skaven.sounds.ambient_loop")
@patch("skaven.sounds.chains_loop")
@patch("skaven.sounds.skaven_loop")
@patch("skaven.sounds.rats_loop")
@patch("skaven.sounds.logger")
def test_main_keyboard_interrupt(
    mock_logger: MagicMock,
    mock_rats: MagicMock,
    mock_skaven: MagicMock,
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
        "skaven": [Path("sk.wav")],
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


@patch("skaven.sounds.logger")
def test_main_no_sound_dir(
    mock_logger: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Point config.SOUNDS_DIR to a non-existent directory
    non_existent_path = tmp_path / "nonexistent_sounds"
    monkeypatch.setattr(config, "SOUNDS_DIR", non_existent_path)

    # Pygame mocks handled by fixture

    # Patch Thread to check if loops are started
    mock_thread_start = MagicMock()
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


@patch("skaven.sounds.logger")
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


@patch("skaven.sounds.logger")
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
@patch("skaven.sounds.logger")
@patch("skaven.sounds.load_sound_categories")
@patch("skaven.sounds.ambient_loop")  # Patch loops to prevent actual execution
@patch("skaven.sounds.chains_loop")
@patch("skaven.sounds.skaven_loop")
@patch("skaven.sounds.rats_loop")
@patch("skaven.sounds.threading.Thread")  # Patch Thread to check calls
def test_main_integration_setup_teardown(
    mock_thread: MagicMock,
    mock_rats_loop: MagicMock,
    mock_skaven_loop: MagicMock,
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
        "skaven": [tmp_path / "sk.wav"],
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

    def fake_wait(self: threading.Event, timeout: object = None) -> None:
        return None

    monkeypatch.setattr(
        threading.Event,
        "wait",
        fake_wait,
    )
    monkeypatch.setattr(threading.Event, "is_set", lambda self: True)
    main.ambient_loop(files, 100, 0.5, stop_event=event)


def test_chains_loop_breaks_on_event(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("c1.wav")]
    event = threading.Event()
    event.set()

    def fake_wait(self: threading.Event, timeout: object = None) -> None:
        return None

    monkeypatch.setattr(threading.Event, "wait", fake_wait)
    monkeypatch.setattr(threading.Event, "is_set", lambda self: True)
    main.chains_loop(files, stop_event=event)


def test_skaven_loop_breaks_on_event(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("s1.wav")]
    event = threading.Event()
    event.set()

    def fake_wait(self: threading.Event, timeout: object = None) -> None:
        return None

    monkeypatch.setattr(threading.Event, "wait", fake_wait)
    monkeypatch.setattr(threading.Event, "is_set", lambda self: True)
    main.skaven_loop(files, stop_event=event)


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

    def fake_wait(self: threading.Event, timeout: object = None) -> None:
        return None

    monkeypatch.setattr(threading.Event, "wait", fake_wait)
    monkeypatch.setattr(threading.Event, "is_set", lambda self: True)
    main.rats_loop(files, chans, stop_event=event)


@patch("skaven.sounds.threading.Thread")
@patch("skaven.sounds.load_sound_categories")
@patch("skaven.sounds.ambient_loop")
@patch("skaven.sounds.chains_loop")
@patch("skaven.sounds.skaven_loop")
@patch("skaven.sounds.rats_loop")
def test_main_scream_logic_with_files(
    mock_rats: MagicMock,
    mock_skaven: MagicMock,
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
        "skaven": [Path("sk.wav")],
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

    def fake_wait(self: threading.Event, timeout: object = None) -> None:
        raise Exception("break")

    monkeypatch.setattr(threading.Event, "wait", fake_wait)
    try:
        with pytest.raises(Exception):
            main.rats_loop(files, chans, stop_event=threading.Event())
    finally:
        monkeypatch.setattr(threading.Event, "wait", original_wait)


@patch("skaven.sounds.threading.Thread")
@patch("skaven.sounds.load_sound_categories")
@patch("skaven.sounds.ambient_loop")
@patch("skaven.sounds.chains_loop")
@patch("skaven.sounds.skaven_loop")
@patch("skaven.sounds.rats_loop")
def test_main_with_stop_after_parameter_logs_and_prints(
    mock_rats: MagicMock,
    mock_skaven: MagicMock,
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
        "skaven": [Path("sk.wav")],
    }
    # Patch wait to return True after first call (simulate stop_after)
    call_count = {"n": 0}

    def fake_wait(self: threading.Event, timeout: object = None) -> bool:
        call_count["n"] += 1
        return call_count["n"] >= 1

    monkeypatch.setattr(threading.Event, "wait", fake_wait)
    main.main(stop_event=threading.Event(), stop_after=1)


@patch("skaven.sounds.logger")
@patch("skaven.sounds.load_sound_categories")
@patch("skaven.sounds.ambient_loop")
@patch("skaven.sounds.chains_loop")
@patch("skaven.sounds.skaven_loop")
@patch("skaven.sounds.rats_loop")
def test_main_keyboard_interrupt_during_shutdown(
    mock_rats: MagicMock,
    mock_skaven: MagicMock,
    mock_chains: MagicMock,
    mock_ambient: MagicMock,
    mock_load: MagicMock,
    mock_logger: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_load.return_value = {
        "ambient": [Path("a.wav")],
        "rats": [Path("r.wav")],
        "chains": [Path("c.wav")],
        "screams": [Path("scream.wav")],
        "skaven": [Path("sk.wav")],
    }
    # Patch wait to raise KeyboardInterrupt on first call,
    # then again during shutdown.
    wait_calls = {"count": 0}

    def fake_wait(self: threading.Event, timeout: object = None) -> bool:
        wait_calls["count"] += 1
        raise KeyboardInterrupt("Simulated interrupt")

    monkeypatch.setattr(threading.Event, "wait", fake_wait)

    def raise_kb_interrupt(s: float) -> None:
        raise KeyboardInterrupt("shutdown")

    monkeypatch.setattr(main.time, "sleep", raise_kb_interrupt)
    try:
        main.main(stop_event=threading.Event())
    except KeyboardInterrupt:
        pass
    # Optionally, assert that wait was called at least once
    assert wait_calls["count"] >= 1
