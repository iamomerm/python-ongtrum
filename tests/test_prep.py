import os

from ongtrum.annotation import preps
from ongtrum.ongtrum import run


@preps('class_prep')
class TestPrep:
    @preps('method_prep')
    def test_dummy_1(self, method_prep):
        assert method_prep == 'Method Prep'

    def test_dummy_2(self):
        assert self.class_prep == 'Class Prep'

    def test_dummy_3(self):
        assert self.session_prep == 'Session Prep'


if __name__ == '__main__':
    res = run(os.path.abspath(__file__), quiet=False, config='ongtrum.yaml')
    assert res['collected'] == 3, f'Collected Tests, Expected: 3, Actual: {res["collected"]}'
    assert res['executed'] == 3, f'Executed Tests, Expected: 3, Actual: {res["executed"]}'
    assert res['failed'] == 0, f'Failed Tests, Expected: 0, Actual: {res["failed"]}'
    assert res['passed'] == 3, f'Passed Tests, Expected: 3, Actual: {res["passed"]}'
