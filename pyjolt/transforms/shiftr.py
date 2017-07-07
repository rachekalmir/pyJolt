import re
from collections import Mapping
from functools import partial

from ..util import recursive_dict, translate


def update(base,  # type: dict
           update_dict,  # type: dict
           ):
    # type: (...) -> dict
    for key, value in update_dict.items():
        if isinstance(value, Mapping):
            r = update(base.get(key, {}), value)
            base[key] = r
        else:
            base[key] = update_dict[key]
    return base


def process_amp(data,  # type: str
                tree,  # type: list
                char,  # type: str
                offset=0,  # type: int
                ):
    # type: (...) -> str
    if re.match(re.escape(char) + r'$', data):
        result = tree[-1 + offset - 0]
    elif re.match(re.escape(char) + r'\d+', data):
        result = tree[-1 + offset - int(data[1:])]
    else:
        match = re.match(re.escape(char) + r'\((\d+)(?:,(\d+))?\)', data)
        if match:
            result = tree[-1 + offset - int(match.groups()[0])][int(match.groups()[1])]
        else:
            # TODO make new exception
            raise Exception

    return result[0] if isinstance(result, list) else result


def process_amp_regex(data,
                      tree,  # type: list
                      char,  # type: str
                      offset=0,  # type: int
                      ):
    # type: (...) -> str
    return process_amp(data.group(), tree=tree, char=char, offset=offset)


def process_amp_str(data,  # type: str
                    tree,  # type: list
                    char,  # type: str
                    offset=0,  # type: int
                    ):
    # type: (...) -> str
    repl = partial(process_amp_regex, tree=tree, char=char, offset=offset)
    return re.sub(r'{0}\(\d+(,\d+)?\)|{0}\d*'.format(re.escape(char)), repl, str(data))


class ShiftrSpec(object):
    key = None
    spec = None

    def process(self,
                data,  # type: Union[str, dict]
                tree,  # type: list
                ):
        # type: (...) -> dict
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
    def __init__(self,
                 key,  # type: Union[None, str]
                 spec,  # type: str
                 ):
        self.key = key
        self.spec = spec

    def __repr__(self):
        return "ShiftrLeafSpec('{}', '{}')".format(self.key, self.spec)

    def process(self,
                data,  # type: str
                tree,  # type: list
                ):
        # type: (...) -> dict
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

    def __init__(self,
                 key,  # type: Union[None, str]
                 spec,  # type: dict
                 ):
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

    def process(self,
                data,  # type: dict
                tree,  # type: list
                ):
        # type: (...) -> dict
        base = dict()
        for key, value in data.items():
            match = False
            for child in self.literal_children:
                if child.key == key:
                    match = True
                    update(base, child.process(value, tree + [key]))

            if not match:
                for child in self.computed_children:
                    # compute & operator
                    if process_amp_str(child.key, tree, '&') == key:
                        match = True
                        update(base, child.process(value, tree + [key]))

            if not match:
                for child in self.wildcard_children:
                    # compute * (wildcard) operator
                    match = re.match(translate(child.key), key)
                    if match:
                        update(base, child.process(value, tree + [[key] + list(match.groups()) if match.groups() else key]))

            for child in self.dollar_children:
                update(base, child.process(value, tree + [key]))

        return base


def shiftr_leaf_factory(key,
                        spec,
                        *args,
                        **kwargs):
    if isinstance(spec, dict):
        return ShiftrNodeSpec(key, spec)
    else:
        return ShiftrLeafSpec(key, spec)


def shiftr_factory(spec,  # type: dict
                   *args,
                   **kwargs):
    return ShiftrNodeSpec(None, spec)
