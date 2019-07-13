import pytest
from deepdiff import DeepDiff


def assert_shiftr(expected_output, output):
    if DeepDiff(expected_output, output, ignore_order=True, report_repetition=True) != {}:
        pytest.fail('Expected output does not match output.')
