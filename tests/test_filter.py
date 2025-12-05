import os

from ongtrum.annotation import preps
from ongtrum.ongtrum import run


@preps('class_prep')
class TestFilter:
    def test_dummy_1(self):
        assert True

    def test_dummy_2(self):
        assert True

    def test_dummy_3(self):
        assert True


if __name__ == '__main__':
    current_file = os.path.abspath(__file__)

    # Filter Method
    res = run(current_file, quiet=False, test_filter='*.TestFilter.test_dummy_1')
    assert res['collected'] == 3, f'Collected Tests, Expected: 3, Actual: {res["collected"]}'
    assert res['executed'] == 1, f'Executed Tests, Expected: 1, Actual: {res["executed"]}'
    assert res['passed'] == 1, f'Failed Tests, Expected: 1, Actual: {res["failed"]}'
    assert res['failed'] == 0, f'Passed Tests, Expected: 0, Actual: {res["passed"]}'

    # Filter Class
    res = run(current_file, quiet=False, test_filter='*.TestFilter')
    assert res['collected'] == 3, f'Collected Tests, Expected: 3, Actual: {res["collected"]}'
    assert res['executed'] == 3, f'Executed Tests, Expected: 3, Actual: {res["executed"]}'
    assert res['passed'] == 3, f'Failed Tests, Expected: 3, Actual: {res["failed"]}'
    assert res['failed'] == 0, f'Passed Tests, Expected: 0, Actual: {res["passed"]}'

    # Filter File
    res = run(current_file, quiet=False, test_filter=f'{os.path.splitext(os.path.basename(__file__))[0]}.*.*')
    assert res['collected'] == 3, f'Collected Tests, Expected: 3, Actual: {res["collected"]}'
    assert res['executed'] == 3, f'Executed Tests, Expected: 3, Actual: {res["executed"]}'
    assert res['passed'] == 3, f'Failed Tests, Expected: 3, Actual: {res["failed"]}'
    assert res['failed'] == 0, f'Passed Tests, Expected: 0, Actual: {res["passed"]}'
