from skaven import config


def test_volume() -> None:
    # Sound volume moved to config.py as SOUND_VOLUME_DEFAULT
    assert isinstance(config.SOUND_VOLUME_DEFAULT, float)
