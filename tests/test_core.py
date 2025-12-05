import os

from ongtrum.ongtrum import run


class TestCore:
    def test_dummy_1(self):
        assert 1 == 1

    def test_dummy_2(self):
        assert 1 == 0, '1 != 0'


if __name__ == '__main__':
    res = run(os.path.abspath(__file__), quiet=False)
    assert res['collected'] == 2, f'Collected Tests, Expected: 2, Actual: {res["collected"]}'
    assert res['executed'] == 2, f'Executed Tests, Expected: 2, Actual: {res["executed"]}'
    assert res['failed'] == 1, f'Failed Tests, Expected: 1, Actual: {res["failed"]}'
    assert res['passed'] == 1, f'Passed Tests, Expected: 1, Actual: {res["passed"]}'
