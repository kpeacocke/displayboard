# test_consumer.py

from skaven import main


def test_volume() -> None:
    assert isinstance(main.SOUND_VOLUME, float)
