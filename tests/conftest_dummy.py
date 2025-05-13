import pytest
import threading


@pytest.fixture
def dummy_event() -> threading.Event:
    return threading.Event()
