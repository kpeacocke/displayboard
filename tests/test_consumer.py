import pytest


@pytest.mark.parametrize("vol", [0.5, 1.0, 2.0])
def test_volume(vol: float) -> None:
    # Sound volume moved to config.py as SOUND_VOLUME_DEFAULT

    from displayboard import config

    setattr(config, "SOUND_VOLUME_DEFAULT", vol)
    assert isinstance(config.SOUND_VOLUME_DEFAULT, float)
