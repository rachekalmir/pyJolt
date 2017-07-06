import re
from collections import Mapping
from fnmatch import fnmatch
from functools import partial

from typing import Union, List

from ..util import recursive_dict


def update(base: dict, update_dict: dict):
    for key, value in update_dict.items():
        if isinstance(value, Mapping):
            r = update(base.get(key, {}), value)
            base[key] = r
        else:
            base[key] = update_dict[key]
    return base


def process_amp(data: str, tree: List, char: str, offset: int = 0) -> str:
    if re.match(re.escape(char) + r'$', data):
        return tree[-1 + offset - 0]
    elif re.match(re.escape(char) + r'\d+', data):
        return tree[-1 + offset - int(data[1:])]
    elif re.match(re.escape(char) + r'\(\d+(,\d+)?\)', data):
        # TODO finish this
        return
    else:
        # TODO make new exception
        raise Exception


def process_amp_regex(data, tree: List, char: str, offset: int = 0):
    return process_amp(data.group(), tree=tree, char=char, offset=offset)


def process_amp_str(data: str, tree: List, char: str, offset: int = 0) -> str:
    repl = partial(process_amp_regex, tree=tree, char=char, offset=offset)
    return re.sub(r'{0}\(\d+(,\d+)?\)|{0}\d*'.format(re.escape(char)), repl, str(data))


class ShiftrSpec(object):
    key = None
    spec = None

    def process(self, data: Union[str, dict], tree: List) -> dict:
        """
        Process the shift algorithm:
        Walk the input data and the spec simultaneously then output the transformation

        * First search the spec for a literal match to the input key
        * Then search for a spec match based on computed & values
        * Finally search for a spec match based on the * wildcard

        :param data:
        :param tree:
        :return:
        """
        pass

    def __lt__(self, other):
        return self.key < other.key

    def __repr__(self):
        return [self.key, self.spec]


class ShiftrLeafSpec(ShiftrSpec):
    def __init__(self, key: Union[None, str], spec: str):
        self.key = key
        self.spec = spec

    def __repr__(self):
        return "ShiftrLeafSpec('{}', '{}')".format(self.key, self.spec)

    def process(self, data: str, tree: List) -> dict:
        base_dict = recursive_dict()
        rec_dict = base_dict
        # TODO fix this
        for ikey in self.spec.split('.')[:-1]:
            if '&' in ikey:
                rec_dict = rec_dict[process_amp_str(ikey, tree, '&')]
            else:
                rec_dict = rec_dict[ikey]
        if '$' in self.key:
            rec_dict[process_amp_str(self.spec.split('.')[-1], tree, '&')] = process_amp_str(self.key, tree, '$', -1)
        else:
            rec_dict[process_amp_str(self.spec.split('.')[-1], tree, '&')] = process_amp_str(data, tree, '&') if '&' in str(data) else data

        return base_dict


class ShiftrNodeSpec(ShiftrSpec):
    literal_children = None
    computed_children = None
    wildcard_children = None
    dollar_children = None

    def __init__(self, key: Union[None, str], spec: dict):
        self.key = key
        self.spec = spec

        self.literal_children = []
        self.computed_children = []
        self.wildcard_children = []
        self.dollar_children = []

        for key, value in spec.items():
            child = shiftr_leaf_factory(key, value)

            if '*' in key:
                self.wildcard_children.append(child)
            elif '&' in key:
                self.computed_children.append(child)
            elif '$' in key:
                self.dollar_children.append(child)
            self.literal_children.append(child)

        self.literal_children.sort()
        self.wildcard_children.sort()

    def __repr__(self):
        return "ShiftNodeSpec('{}', {})".format(self.key, self.spec)

    def process(self, data: dict, tree: List) -> dict:
        base = dict()
        for key, value in data.items():
            match = False
            for child in self.literal_children:
                if child.key == key:
                    match = True
                    update(base, child.process(value, tree + [key]))

            if not match:
                for child in self.computed_children:
                    # TODO: compute & operator
                    if process_amp_str(child.key, tree, '&') == key:
                        match = True
                        update(base, child.process(value, tree + [key]))

            if not match:
                for child in self.wildcard_children:
                    # TODO: compute * (wildcard) operator
                    if fnmatch(key, child.key):
                        update(base, child.process(value, tree + [key]))

            for child in self.dollar_children:
                update(base, child.process(value, tree + [key]))

        return base


def shiftr_leaf_factory(key, spec, *args, **kwargs):
    if isinstance(spec, dict):
        return ShiftrNodeSpec(key, spec)
    else:
        return ShiftrLeafSpec(key, spec)


def shiftr_factory(spec: dict, *args, **kwargs):
    return ShiftrNodeSpec(None, spec)
