import os

from ongtrum.annotation import suites
from ongtrum.ongtrum import run


class TestSuite:
    @suites('suite_one')
    def test_dummy_1(self):
        assert 1 == 1

    @suites('suite_one')
    def test_dummy_2(self):
        assert 1 == 0

    @suites('suite_two')
    def test_dummy_3(self):
        assert 2 == 2

    @suites('suite_two')
    def test_dummy_4(self):
        assert 2 == 3


class TestMultiSuites:
    @suites(['suite_three', 'suite_four'])
    def test_dummy_5(self):
        assert 10 == 10

    @suites(['suite_three', 'suite_four'])
    def test_dummy_6(self):
        assert 5 == 0

    @suites(['suite_three', 'suite_four'])
    def test_dummy_7(self):
        assert 3 == 3


if __name__ == '__main__':
    # Run only suite_one
    res_suite1 = run(os.path.abspath(__file__), quiet=False, suite='suite_one')
    assert res_suite1['collected'] == 7, f'Collected Tests, Expected: 7, Actual: {res_suite1["collected"]}'
    assert res_suite1['executed'] == 2, f'Executed Tests, Expected: 2, Actual: {res_suite1["executed"]}'
    assert res_suite1['failed'] == 1, f'Failed Tests, Expected: 1, Actual: {res_suite1["failed"]}'
    assert res_suite1['passed'] == 1, f'Passed Tests, Expected: 1, Actual: {res_suite1["passed"]}'

    # Run only suite_two
    res_suite2 = run(os.path.abspath(__file__), quiet=False, suite='suite_two')
    assert res_suite2['collected'] == 7, f'Collected Tests, Expected: 7, Actual: {res_suite2["collected"]}'
    assert res_suite2['executed'] == 2, f'Executed Tests, Expected: 2, Actual: {res_suite2["executed"]}'
    assert res_suite2['failed'] == 1, f'Failed Tests, Expected: 1, Actual: {res_suite2["failed"]}'
    assert res_suite2['passed'] == 1, f'Passed Tests, Expected: 1, Actual: {res_suite2["passed"]}'

    # Run only suite_three
    res_suite2 = run(os.path.abspath(__file__), quiet=False, suite='suite_three')
    assert res_suite2['collected'] == 7, f'Collected Tests, Expected: 7, Actual: {res_suite2["collected"]}'
    assert res_suite2['executed'] == 3, f'Executed Tests, Expected: 3, Actual: {res_suite2["executed"]}'
    assert res_suite2['failed'] == 1, f'Failed Tests, Expected: 1, Actual: {res_suite2["failed"]}'
    assert res_suite2['passed'] == 2, f'Passed Tests, Expected: 2, Actual: {res_suite2["passed"]}'

    # Run only suite_four
    res_suite2 = run(os.path.abspath(__file__), quiet=False, suite='suite_three')
    assert res_suite2['collected'] == 7, f'Collected Tests, Expected: 7, Actual: {res_suite2["collected"]}'
    assert res_suite2['executed'] == 3, f'Executed Tests, Expected: 3, Actual: {res_suite2["executed"]}'
    assert res_suite2['failed'] == 1, f'Failed Tests, Expected: 1, Actual: {res_suite2["failed"]}'
    assert res_suite2['passed'] == 2, f'Passed Tests, Expected: 2, Actual: {res_suite2["passed"]}'

    # Run all suites
    res_all = run(os.path.abspath(__file__), quiet=False)
    assert res_all['collected'] == 7, f'Collected Tests, Expected: 7, Actual: {res_all["collected"]}'
    assert res_all['executed'] == 7, f'Executed Tests, Expected: 7, Actual: {res_all["executed"]}'
    assert res_all['failed'] == 3, f'Failed Tests, Expected: 3, Actual: {res_all["failed"]}'
    assert res_all['passed'] == 4, f'Passed Tests, Expected: 4, Actual: {res_all["passed"]}'
