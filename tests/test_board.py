from _pytest.monkeypatch import MonkeyPatch


def test_d18_value(monkeypatch: MonkeyPatch) -> None:
    """
    Test to ensure D18 has the correct value for different hardware pins.
    """
    import displayboard.board

    for pin in [18, 21, 99]:
        monkeypatch.setattr(displayboard.board, "D18", pin, raising=False)
        assert displayboard.board.D18 == pin, f"D18 should be equal to {pin}"
