# test_consumer.py

from skaven_soundscape import main


def test_volume() -> None:
    assert isinstance(main.SOUND_VOLUME, float)
