from skaven.board import D18


def test_d18_value(mock_board_pins: object) -> None:
    """
    Test to ensure D18 has the correct value.
    """
    assert D18 == 18, "D18 should be equal to 18"
