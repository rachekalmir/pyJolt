from deepdiff import DeepDiff

from pyjolt import Jolt


class JoltTestObject(object):
    def __init__(self, filename, input_data, spec, expected):
        self.filename = filename
        self.input_data = input_data
        self.spec = spec
        self.expected = expected


def test_shiftr(shiftr_test: JoltTestObject):
    assert DeepDiff(shiftr_test.expected, Jolt(shiftr_test.input_data).shift(shiftr_test.spec).data, ignore_order=True, report_repetition=True) == {}
