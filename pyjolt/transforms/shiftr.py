import re
from collections import Mapping
from functools import partial
from queue import Queue

from ..util import recursive_dict, translate, UnsortedList


def update(base,  # type: dict
           update_dict,  # type: Mapping
           append=True,  # type: bool
           ):
    # type: (...) -> dict
    for key, value in update_dict.items():
        if isinstance(value, Mapping):
            # if the value is a dictionary, recursive update it
            r = update(base.get(key, {}), value, append=append)
            base[key] = r
        elif key in base and append:
            # if the key already exists in the base, update the list bucket
            if isinstance(base[key], list):
                base[key] += UnsortedList([value])
            else:
                base[key] = UnsortedList([base[key], value])
        else:
            # otherwise just append the value
            base[key] = value
    return base


def process_amp(data,  # type: str
                tree,  # type: list
                char,  # type: str
                offset=0,  # type: int
                ):
    # type: (...) -> str

    # First try to match the form of '&'
    if re.match(re.escape(char) + r'$', data):
        result = tree[-1 + offset - 0]

    # Else, try to match the form of '&1'
    elif re.match(re.escape(char) + r'[0-9]+', data):
        result = tree[-1 + offset - int(data[1:])]

    # Else, try to match the full form of '&(1, 2)'
    else:
        match = re.match(re.escape(char) + r'\(([0-9]+)(?:,([0-9]+))?\)', data)
        if match:
            result = tree[-1 + offset - int(match.groups()[0])][int(match.groups()[1])]
        else:
            # TODO make new exception
            raise Exception

    # return the processed pattern result
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
    return re.sub(r'(?<!\\){0}\([0-9]+(,[0-9]+)?\)|(?<!\\){0}[0-9]*'.format(re.escape(char)), repl, str(data))


def process_str(data,  # type: str
                tree,  # type: list
                ):
    # type: (...) -> str)
    result = process_amp_str(data=data, tree=tree, char='&')
    result = process_amp_str(data=result, tree=tree, char='@')
    result = process_amp_str(data=result, tree=tree, char='$')
    return result


class ShiftrSpec(object):
    spec_key = None
    spec_value = None

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
        return self.spec_key < other.spec_key

    def __repr__(self):
        return [self.spec_key, self.spec_value]


class ShiftrLeafSpec(ShiftrSpec):
    def __init__(self,
                 spec_key,  # type: Union[None, str]
                 spec_value,  # type: str
                 ):
        self.spec_key = spec_key
        self.spec_value = spec_value

    def __repr__(self):
        return "ShiftrLeafSpec('{}', '{}')".format(self.spec_key, self.spec_value)

    def process(self,
                data,  # type: str
                tree,  # type: list
                ):
        # type: (...) -> dict
        base_dict = recursive_dict()
        rec_dict = base_dict

        # TODO fix this

        # Breakdown the spec_value from 'a.b.c.d' into its constituent parts and build up the result dictionary
        for ikey in self.spec_value.split('.')[:-1]:
            rec_dict = rec_dict[process_str(ikey, tree)]

        #
        if self.spec_key.startswith('#'):
            rec_dict[process_str(self.spec_value.split('.')[-1], tree)] = self.spec_key[1:]
        elif '$' in self.spec_key:
            rec_dict[process_str(self.spec_value.split('.')[-1], tree)] = process_amp_str(self.spec_key, tree, '$', -1)
        else:
            rec_dict[process_str(self.spec_value.split('.')[-1], tree)] = process_str(data, tree) if isinstance(data, str) else data

        return base_dict


class ShiftrNodeSpec(ShiftrSpec):
    literal_children = None  # type: list
    computed_children = None  # type: list
    wildcard_children = None  # type: list
    dollar_children = None  # type: list

    process_queue = None  # type: Queue

    def __init__(self,
                 spec_key,  # type: Union[None, str]
                 spec_value,  # type: dict
                 ):
        self.spec_key = spec_key
        self.spec_value = spec_value

        self.literal_children = []
        self.computed_children = []
        self.wildcard_children = []
        self.dollar_children = []

        self.process_queue = Queue()

        spec_queue = Queue()

        for spec_key, value in spec_value.items():
            spec_queue.put((spec_key, value))

        while not spec_queue.empty():
            spec_key, value = spec_queue.get()
            child = shiftr_leaf_factory(spec_key, value)

            # Re-add the value to the process queue if there is an OR in the key and it didn't match a literal key
            # TODO: check if this is the intended functionality
            if '|' in spec_key:
                for k in spec_key.split('|'):
                    spec_queue.put((k, value))
                    continue

            if '*' in spec_key:
                self.wildcard_children.append(child)
            elif '&' in spec_key:
                self.computed_children.append(child)
            elif '$' in spec_key or '#' in spec_key or '@' in spec_key:
                self.dollar_children.append(child)
            self.literal_children.append(child)

        self.literal_children.sort()
        self.wildcard_children.sort()

    def __repr__(self):
        return "ShiftNodeSpec('{}', {})".format(self.spec_key, self.spec_value)

    def process(self,
                data,  # type: dict
                tree,  # type: list
                ):
        # type: (...) -> dict
        base = dict()
        if type(data) is dict:
            for key, value in data.items():
                self.process_queue.put((key, value))
        else:
            # Allow for processing of the # wildcard if the spec contains more nodes but the data stream doesn't
            self.process_queue.put((data, None))

        while not self.process_queue.empty():
            key, value = self.process_queue.get()

            match = False
            for child in self.literal_children:
                if child.spec_key == key:
                    match = True
                    update(base, child.process(value, tree + [key]))

            # compute & operator
            if not match:
                for child in self.computed_children:
                    if process_amp_str(child.spec_key, tree, '&') == key:
                        match = True
                        update(base, child.process(value, tree + [key]))

            # compute * (wildcard) operator
            if not match:
                for child in self.wildcard_children:
                    match = re.match(translate(child.spec_key), key)
                    if match:
                        update(base, child.process(value, tree + [[key] + list(match.groups()) if match.groups() else key]))

            for child in self.dollar_children:
                update(base, child.process(value, tree + [key]), append=False)

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
