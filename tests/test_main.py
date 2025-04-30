import sys
import importlib
import pytest
from pathlib import Path
from typing import Callable, Any, Tuple, List, cast, Dict
import types

# Ensure the project root is on sys.path so we can import the module under test
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import skaven.main as main  # noqa: E402


# --- Fixtures for patching pygame, time, and random ---
@pytest.fixture(autouse=True)
def patch_pygame(monkeypatch: pytest.MonkeyPatch) -> None:
    mixer = types.SimpleNamespace()

    def init() -> None:
        # No-op for pygame.mixer.init in tests
        pass

    def set_num_channels(n: int) -> None:
        # No-op for setting number of channels in tests
        pass

    def sound(path: Path) -> types.SimpleNamespace:
        def set_volume(v: float) -> None:
            # No-op for setting volume in tests
            pass

        def get_length() -> float:
            # Return dummy length
            return 1.0

        def play(**kwargs: Any) -> None:
            # No-op for playing sound in tests
            pass

        def fadeout(ms: int) -> None:
            # No-op for fading out sound in tests
            pass

        return types.SimpleNamespace(
            set_volume=set_volume,
            get_length=get_length,
            play=play,
            fadeout=fadeout,
        )

    def channel(i: int = 0) -> types.SimpleNamespace:
        def play(s: types.SimpleNamespace, **kwargs: Any) -> None:
            # No-op for channel play in tests
            pass

        def fadeout(ms: int) -> None:
            # No-op for channel fadeout in tests
            pass

        return types.SimpleNamespace(
            play=play,
            fadeout=fadeout,
        )

    def pygame_init_override() -> None:
        # No-op for pygame.init in tests
        pass

    mixer.init = init
    mixer.set_num_channels = set_num_channels
    mixer.Sound = sound
    mixer.Channel = channel
    monkeypatch.setattr(main.pygame, "mixer", mixer)
    monkeypatch.setattr(main.pygame, "init", pygame_init_override)


@pytest.fixture(autouse=True)
def patch_time_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    def sleep_override(seconds: float) -> None:
        # No-op sleep in tests
        pass

    monkeypatch.setattr(main.time, "sleep", sleep_override)


@pytest.fixture(autouse=True)
def patch_random(monkeypatch: pytest.MonkeyPatch) -> None:
    def uniform_override(a: float, b: float) -> float:
        return a

    def choice_override(seq: List[Path]) -> Path:
        return seq[0] if seq else Path()

    def randint_override(a: int, b: int) -> int:
        return a

    def sample_override(seq: List[Path], n: int) -> List[Path]:
        return seq[:n]

    def random_override() -> float:
        return 1.0

    monkeypatch.setattr(main.random, "uniform", uniform_override)
    monkeypatch.setattr(main.random, "choice", choice_override)
    monkeypatch.setattr(main.random, "randint", randint_override)
    monkeypatch.setattr(main.random, "sample", sample_override)
    monkeypatch.setattr(main.random, "random", random_override)


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
    found = main.list_audio_files(tmp_path)
    exts = {p.suffix for p in found}
    assert exts == {".wav", ".ogg", ".mp3"}
    paths = {p.name for p in found}
    assert paths == {"a.wav", "b.ogg", "c.mp3"}


def test_load_sound_categories(tmp_path: Path) -> None:
    categories = ["ambient", "rats", "chains", "screams", "skaven"]
    for cat in categories:
        d = tmp_path / cat
        d.mkdir()
        f = d / f"{cat}_1.wav"
        f.write_text("dummy")
    cats = main.load_sound_categories(tmp_path)
    assert set(cats) == set(categories)
    for cat in categories:
        files = cats[cat]
        assert len(files) == 1
        assert files[0].name == f"{cat}_1.wav"


@pytest.mark.parametrize(
    "func, args",
    [
        (main.ambient_loop, (cast(List[Path], []), 100, 0.5)),
        (main.chains_loop, (cast(List[Path], []),)),
        (main.skaven_loop, (cast(List[Path], []),)),
        (
            main.rats_loop,
            (cast(List[Path], []), cast(List[types.SimpleNamespace], [])),
        ),
    ],
)
def test_loops_return_immediately_on_empty(
    func: Callable[..., Any], args: Tuple[Any, ...]
) -> None:
    result = func(*args)
    assert result is None


def test_sound_volume_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOUND_VOLUME", "0.42")
    importlib.reload(main)
    assert isinstance(main.SOUND_VOLUME, float)
    assert abs(main.SOUND_VOLUME - 0.42) < 1e-6


# --- Full coverage tests for loop bodies and main() ---


def test_ambient_loop_runs() -> None:
    files = [Path("a.wav")]
    called = {}

    class BreakLoop(Exception):
        pass

    def fake_sleep(secs: float) -> None:
        called["sleep"] = True
        raise BreakLoop()

    main.time.sleep = fake_sleep
    with pytest.raises(BreakLoop):
        main.ambient_loop(files, 100, 0.5)
    assert called["sleep"]


def test_chains_loop_runs() -> None:
    files = [Path("c1.wav")]
    called = {}

    class BreakLoop(Exception):
        pass

    def fake_sleep(secs: float) -> None:
        called["sleep"] = True
        raise BreakLoop()

    main.time.sleep = fake_sleep
    with pytest.raises(BreakLoop):
        main.chains_loop(files)
    assert called["sleep"]


def test_skaven_loop_runs() -> None:
    files = [Path("s1.wav")]
    called = {}

    class BreakLoop(Exception):
        pass

    def fake_sleep(secs: float) -> None:
        called["sleep"] = True
        raise BreakLoop()

    main.time.sleep = fake_sleep
    with pytest.raises(BreakLoop):
        main.skaven_loop(files)
    assert called["sleep"]


def test_rats_loop_runs() -> None:
    files = [Path("r1.wav"), Path("r2.wav")]
    chans = [main.pygame.mixer.Channel(1), main.pygame.mixer.Channel(2)]
    called: dict[str, int] = {}

    class BreakLoop(Exception):
        pass

    def fake_sleep(secs: float) -> None:
        called["sleep"] = called.get("sleep", 0) + 1
        if called["sleep"] > 2:
            raise BreakLoop()

    main.time.sleep = fake_sleep
    with pytest.raises(BreakLoop):
        main.rats_loop(files, chans)
    assert called["sleep"] > 0


def test_main_runs_and_keyboardinterrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # simulate KeyboardInterrupt on sleep
    def pygame_init_override() -> None:
        # no-op pygame.init override
        pass

    monkeypatch.setattr(main.pygame, "init", pygame_init_override)

    def mixer_init_override() -> None:
        # no-op mixer.init override
        pass

    monkeypatch.setattr(main.pygame.mixer, "init", mixer_init_override)

    def set_num_channels_override(n: int) -> None:
        # no-op set_num_channels override
        pass

    monkeypatch.setattr(
        main.pygame.mixer,
        "set_num_channels",
        set_num_channels_override,
    )

    def fake_thread(*args: Any, **kwargs: Any) -> types.SimpleNamespace:
        def start() -> None:
            # no-op thread start
            pass

        return types.SimpleNamespace(start=start)

    monkeypatch.setattr(
        main.threading,
        "Thread",
        fake_thread,
    )

    def fake_sleep(s: float) -> None:
        raise KeyboardInterrupt()

    monkeypatch.setattr(main.time, "sleep", fake_sleep)

    def channel_override(i: int = 0) -> types.SimpleNamespace:
        def fadeout(ms: int = 0) -> None:
            # no-op channel fadeout
            pass

        return types.SimpleNamespace(fadeout=fadeout)

    monkeypatch.setattr(
        main.pygame.mixer,
        "Channel",
        channel_override,
    )

    main.main()


# --- Additional coverage tests from test_main_extra.py ---


def test_chains_loop_body(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("c1.wav")]

    class BreakLoop(Exception):
        pass

    # allow sleep to run once, then break inside play
    calls: Dict[str, float] = {}  # track call counts (float for volume)

    def fake_sleep(secs: float) -> None:
        calls["slept"] = calls.get("slept", 0) + 1
        return None

    monkeypatch.setattr(main.time, "sleep", fake_sleep)

    # inject a Sound whose play raises BreakLoop after set_volume
    def fake_sound(path: Path) -> types.SimpleNamespace:
        def set_volume(v: float) -> None:
            # record volume used
            calls["volume"] = v

        def play(**kwargs: Any) -> None:
            # play raises to break loop
            raise BreakLoop()

        return types.SimpleNamespace(
            set_volume=set_volume,
            play=play,
        )

    monkeypatch.setattr(main.pygame.mixer, "Sound", fake_sound)

    with pytest.raises(BreakLoop):
        main.chains_loop(files)
    assert "volume" in calls


def test_skaven_loop_body(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("s1.wav")]

    class BreakLoop(Exception):
        pass

    def fake_sleep(secs: float) -> None:
        return None

    monkeypatch.setattr(main.time, "sleep", fake_sleep)

    def fake_sound(path: Path) -> types.SimpleNamespace:
        def set_volume(v: float) -> None:
            # no-op volume in tests
            pass

        def play(**kwargs: Any) -> None:
            # break loop on play
            raise BreakLoop()

        return types.SimpleNamespace(
            set_volume=set_volume,
            play=play,
        )

    monkeypatch.setattr(main.pygame.mixer, "Sound", fake_sound)

    with pytest.raises(BreakLoop):
        main.skaven_loop(files)


def test_ambient_loop_body(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("a1.wav")]

    class BreakLoop(Exception):
        pass

    calls: Dict[str, float] = {"count": 0.0}

    def fake_sleep(secs: float) -> None:
        if calls["count"] == 0:
            calls["count"] += 1.0
            return None
        raise BreakLoop()

    monkeypatch.setattr(main.time, "sleep", fake_sleep)

    # fake Channel to record fadeout
    def chan_play(s: Any, **kwargs: Any) -> None:
        # no-op play
        pass

    def chan_fadeout(ms: int) -> None:
        # record fadeout duration
        calls["faded"] = float(ms)

    fake_chan = types.SimpleNamespace(
        play=chan_play,
        fadeout=chan_fadeout,
    )

    def channel_override(i: int) -> types.SimpleNamespace:
        # return the fake channel regardless of index
        return fake_chan

    monkeypatch.setattr(
        main.pygame.mixer,
        "Channel",
        channel_override,
    )

    # fake Sound with a small length
    def fake_sound(path: Path) -> types.SimpleNamespace:
        def set_volume(v: float) -> None:
            # no-op volume in tests
            pass

        def get_length() -> float:
            return 0.01

        def play(**kwargs: Any) -> None:
            # no-op play
            pass

        return types.SimpleNamespace(
            set_volume=set_volume,
            get_length=get_length,
            play=play,
        )

    monkeypatch.setattr(main.pygame.mixer, "Sound", fake_sound)

    with pytest.raises(BreakLoop):
        main.ambient_loop(files, fade_ms=10, volume=0.5)
    assert calls.get("faded") == 10


def test_rats_loop_body(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [Path("r1.wav"), Path("r2.wav")]

    # typed no-op channel methods
    def _no_op_play(s: types.SimpleNamespace) -> None:
        pass

    def _no_op_fadeout(ms: int) -> None:
        # No-op fadeout in tests during test runs
        pass

    chans = [
        types.SimpleNamespace(play=_no_op_play, fadeout=_no_op_fadeout)
        for _ in range(2)
    ]

    class BreakLoop(Exception):
        pass

    calls: Dict[str, int] = {"count": 0}

    def fake_sleep(secs: float) -> None:
        if calls["count"] < 2:
            calls["count"] += 1
            return None
        raise BreakLoop()

    monkeypatch.setattr(main.time, "sleep", fake_sleep)

    # fake Sound that raises in play
    def fake_sound(path: Path) -> types.SimpleNamespace:
        def set_volume(v: float) -> None:
            # no-op volume
            pass

        def play(**kwargs: Any) -> None:
            # break on play
            raise BreakLoop()

        return types.SimpleNamespace(
            set_volume=set_volume,
            play=play,
        )

    monkeypatch.setattr(main.pygame.mixer, "Sound", fake_sound)

    with pytest.raises(BreakLoop):
        main.rats_loop(files, chans)


def test_main_with_stop_after(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that the main function handles the stop_after argument."""

    def fake_load_sound_categories(base_path: Path) -> Dict[str, List[Path]]:
        return {
            "ambient": [],
            "rats": [],
            "chains": [],
            "screams": [],
            "skaven": [],
        }

    monkeypatch.setattr(
        main,
        "load_sound_categories",
        fake_load_sound_categories,
    )

    def fake_sleep(s: float) -> None:
        raise KeyboardInterrupt()

    monkeypatch.setattr(main.time, "sleep", fake_sleep)

    try:
        main.main(stop_after=5)
    except KeyboardInterrupt:
        pass

    captured = capsys.readouterr()
    assert "Stopping after 5 cycles" in captured.out


def test_main_scream_logic_with_files(monkeypatch: pytest.MonkeyPatch) -> None:
    scream_files = [Path("scream1.wav"), Path("scream2.wav")]
    calls = {"played": 0}

    def fake_sleep(secs: float) -> None:
        if calls["played"] >= 1:
            raise KeyboardInterrupt()

    monkeypatch.setattr(main.time, "sleep", fake_sleep)

    def fake_sound(path: Path) -> types.SimpleNamespace:
        def set_volume(v: float) -> None:
            # No-op for setting volume in tests
            pass

        def play(**kwargs: Any) -> None:
            # Simulate playing sound
            calls["played"] += 1

        return types.SimpleNamespace(
            set_volume=set_volume,
            play=play,
        )

    monkeypatch.setattr(main.pygame.mixer, "Sound", fake_sound)

    def fake_load_sound_categories(base_path: Path) -> Dict[str, List[Path]]:
        return {
            "ambient": [],
            "rats": [],
            "chains": [],
            "screams": scream_files,
            "skaven": [],
        }

    monkeypatch.setattr(
        main,
        "load_sound_categories",
        fake_load_sound_categories,
    )

    try:
        main.main()
    except KeyboardInterrupt:
        pass

    assert calls["played"] == 1


# --- Merged tests from test_main_extra.py


def test_main_scream_logic_without_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that main loop skips scream logic
    when no scream files are present."""

    from skaven import main

    class BreakLoop(Exception):
        pass

    def fake_load_sound_categories(base_path: Path) -> Dict[str, List[Path]]:
        return {
            "ambient": [],
            "rats": [],
            "chains": [],
            "screams": [],
            "skaven": [],
        }

    monkeypatch.setattr(
        main,
        "load_sound_categories",
        fake_load_sound_categories,
    )

    calls = {"count": 0}

    def fake_sleep(seconds: float) -> None:
        if calls["count"] < 2:
            calls["count"] += 1
        else:
            raise BreakLoop()

    monkeypatch.setattr(
        main.time,
        "sleep",
        fake_sleep,
    )

    with pytest.raises(BreakLoop):
        main.main()
    assert calls["count"] == 2


def test_ambient_loop_idx_increment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that ambient_loop cycles through files by incrementing idx."""

    from skaven import main

    class BreakLoop(Exception):
        pass

    files = [Path("a.wav"), Path("b.wav")]
    played: List[str] = []

    def chan_play(snd: types.SimpleNamespace, **kwargs: Any) -> None:
        # no-op for tests
        pass

    def chan_fadeout(ms: int) -> None:
        # no-op for tests
        pass

    fake_chan = types.SimpleNamespace(play=chan_play, fadeout=chan_fadeout)

    def channel_override(i: int = 0) -> types.SimpleNamespace:
        return fake_chan

    monkeypatch.setattr(
        main.pygame.mixer,
        "Channel",
        channel_override,
    )

    def fake_sound(path: Any) -> types.SimpleNamespace:
        # path may be a str in main implementation, normalize to Path
        p = Path(path)
        played.append(p.name)

        def set_volume(v: float) -> None:
            # no-op for tests
            pass

        def get_length() -> float:
            return 0.01

        def play(**kwargs: Any) -> None:
            # no-op for tests
            pass

        return types.SimpleNamespace(
            set_volume=set_volume,
            get_length=get_length,
            play=play,
        )

    monkeypatch.setattr(main.pygame.mixer, "Sound", fake_sound)

    calls = {"count": 0}

    def fake_sleep(seconds: float) -> None:
        if calls["count"] < 3:
            calls["count"] += 1
        else:
            raise BreakLoop()

    monkeypatch.setattr(main.time, "sleep", fake_sleep)

    with pytest.raises(BreakLoop):
        main.ambient_loop(files, fade_ms=10, volume=1.0)
    assert "a.wav" in played and "b.wav" in played
