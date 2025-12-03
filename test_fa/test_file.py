class TestMath:
    def test_add(self):
        assert 1 + 1 == 2

    def test_subtract(self):
        assert 5 - 3 == 2

    def test_fail(self):
        assert 1 == 0, '1 != 0'

