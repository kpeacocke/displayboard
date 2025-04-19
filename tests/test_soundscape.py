from pathlib import Path
from skaven_soundscape import main as sound_main
from unittest.mock import patch, MagicMock
from typing import Any, List


def fake_choice(seq: List[Any]) -> Any:
    return seq[0]


def fake_choices(*args: Any, **kwargs: Any) -> List[str]:
    return ["rats"]


def fake_uniform(a: float, b: float) -> float:
    return 1


def fake_sleep(x: float) -> None:
    return None


def test_sound_directories_exist() -> None:
    base_path = Path(__file__).resolve().parent.parent / "sounds"
    for subfolder in ["ambient", "rats", "chains", "screams"]:
        path = base_path / subfolder
        assert path.exists(), f"Missing folder: {subfolder}"
        assert path.is_dir(), f"{subfolder} is not a directory"


def test_audio_file_extensions() -> None:
    base_path = Path(__file__).resolve().parent.parent / "sounds"
    for subfolder in ["rats", "chains", "screams"]:
        for file in (base_path / subfolder).glob("*"):
            assert file.suffix == ".wav", f"Unsupported format in {file.name}"


def test_pick_random_category_distribution() -> None:
    cat = sound_main.pick_random_category()
    assert cat in ["rats", "chains", "screams"]


@patch("skaven_soundscape.main.random.choice", fake_choice)
def test_load_sound_categories_structure() -> None:
    path = Path(__file__).resolve().parent.parent / "sounds"
    cats = sound_main.load_sound_categories(path)
    assert all(isinstance(v, list) for v in cats.values())


@patch(
    "skaven_soundscape.main.load_sound_categories",
    return_value={
        "rats": [Path("fake_rat.wav")],
        "chains": [Path("fake_chain.wav")],
        "screams": [Path("fake_scream.wav")],
    },
)
@patch("skaven_soundscape.main.random.choice", fake_choice)
@patch("skaven_soundscape.main.random.choices", fake_choices)
@patch("skaven_soundscape.main.random.uniform", fake_uniform)
@patch("skaven_soundscape.main.time.sleep", fake_sleep)
@patch("skaven_soundscape.main.pygame.init")
@patch("skaven_soundscape.main.pygame.mixer.init")
@patch("skaven_soundscape.main.pygame.mixer.Sound")
@patch("skaven_soundscape.main.pygame.mixer.music")
def test_main_runs_once(
    mock_music: MagicMock,
    mock_sound: MagicMock,
    *mocks: Any,
) -> None:
    mock_music.load = MagicMock()
    mock_music.set_volume = MagicMock()
    mock_music.play = MagicMock()
    mock_music.stop = MagicMock()
    mock_sound.return_value.set_volume = MagicMock()
    mock_sound.return_value.play = MagicMock()
    sound_main.main(iterations=1)


@patch(
    "skaven_soundscape.main.load_sound_categories",
    return_value={
        "rats": [Path("fake_rat.wav")],
        "chains": [Path("fake_chain.wav")],
        "screams": [Path("fake_scream.wav")],
    },
)
@patch("skaven_soundscape.main.random.choice", fake_choice)
@patch("skaven_soundscape.main.random.choices", fake_choices)
@patch("skaven_soundscape.main.random.uniform", fake_uniform)
@patch("skaven_soundscape.main.time.sleep", side_effect=KeyboardInterrupt)
@patch("skaven_soundscape.main.pygame.init")
@patch("skaven_soundscape.main.pygame.mixer.init")
@patch("skaven_soundscape.main.pygame.mixer.Sound")
@patch("skaven_soundscape.main.pygame.mixer.music")
def test_main_keyboard_interrupt(
    mock_music: MagicMock,
    mock_sound: MagicMock,
    *mocks: Any,
) -> None:
    mock_music.load = MagicMock()
    mock_music.set_volume = MagicMock()
    mock_music.play = MagicMock()
    mock_music.stop = MagicMock()
    mock_sound.return_value.set_volume = MagicMock()
    mock_sound.return_value.play = MagicMock()
    sound_main.main()


@patch(
    "skaven_soundscape.main.load_sound_categories",
    return_value={
        "rats": [Path("fake_rat.wav")],
        "chains": [Path("fake_chain.wav")],
        "screams": [Path("fake_scream.wav")],
    },
)
@patch("skaven_soundscape.main.random.choice", fake_choice)
@patch("skaven_soundscape.main.random.choices", fake_choices)
@patch("skaven_soundscape.main.random.uniform", fake_uniform)
@patch("skaven_soundscape.main.time.sleep", fake_sleep)
@patch("skaven_soundscape.main.pygame.init")
@patch("skaven_soundscape.main.pygame.mixer.init")
@patch("skaven_soundscape.main.pygame.mixer.Sound")
@patch("skaven_soundscape.main.pygame.mixer.music")
def test_main_noop_exit(
    mock_music: MagicMock,
    mock_sound: MagicMock,
    *mocks: Any,
) -> None:
    mock_music.load = MagicMock()
    mock_music.set_volume = MagicMock()
    mock_music.play = MagicMock()
    mock_music.stop = MagicMock()
    mock_sound.return_value.set_volume = MagicMock()
    mock_sound.return_value.play = MagicMock()
    sound_main.main(iterations=0)
