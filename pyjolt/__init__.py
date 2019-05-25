from pyjolt.transforms.shiftr_rewrite import shiftr

__version__ = '0.0.1'


class Jolt(object):
    def __init__(self, data: dict):
        self.data = data

    def shift(self, spec: dict):
        # type: (...) -> Jolt
        self.data = shiftr(self.data, spec)
        return self

    def default(self, spec: dict):
        # type: (...) -> Jolt
        return self

    def remove(self, spec: dict):
        # type: (...) -> Jolt
        return self

    def sort(self, spec: dict):
        # type: (...) -> Jolt
        return self

    def cardinality(self, spec: dict):
        # type: (...) -> Jolt
        return self
