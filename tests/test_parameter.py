import os
from ongtrum.ongtrum import run
from ongtrum.annotation import parameters

class TestParameter:
    @parameters([{'a': 1, 'b': 2}, {'a': 10, 'b': 20}])
    def test_add(self, a, b):
        assert a in [1, 10]
        assert b in [2, 20]

if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    res = run(current_file, quiet=False)

    assert res['collected'] == 1, f'Collected Tests, Expected: 1, Actual: {res["collected"]}'
    assert res['executed'] == 2, f'Executed Tests, Expected: 2, Actual: {res["executed"]}'
    assert res['failed'] == 0, f'Failed Tests, Expected: 0, Actual: {res["failed"]}'
    assert res['passed'] == 2, f'Passed Tests, Expected: 1, Actual: {res["passed"]}'