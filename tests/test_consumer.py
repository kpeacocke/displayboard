from skaven import sounds


def test_volume() -> None:
    assert isinstance(sounds.SOUND_VOLUME, float)
