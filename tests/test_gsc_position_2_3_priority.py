from tests.test_gsc_position_priority import labels_for_position


def test_gsc_position_2_3_priority_file():
    assert "existing ranking position 2-3" in labels_for_position(2.2)
