from tests.test_gsc_position_priority import labels_for_position


def test_gsc_position_4_20_priority_file():
    assert "existing ranking position 4-10" in labels_for_position(5)
    assert "existing ranking position 11-20" in labels_for_position(18)
