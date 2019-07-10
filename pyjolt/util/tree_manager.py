import itertools
from collections import defaultdict
from typing import Union, List, Dict

from pyjolt.exceptions import JoltException


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.zip_longest(a, b)


def type_generator(item):
    if isinstance(item, str):
        return {}
    elif isinstance(item, int):
        return []
    raise JoltException()


def id_generator():
    """Generator function to generate numbers from 0 onwards"""
    start_value = 0
    while True:
        yield start_value
        start_value += 1


class AutoDefaultDict(defaultdict):
    """Default dictionary that calls the specified function to get the new value."""

    def __init__(self, f_of_x):
        super().__init__(None)  # Create the base defaultdict class with no default
        self.f_of_x = f_of_x  # Save the function

    def __missing__(self, key):  # __missing__ is called when a default value is needed
        ret = next(self.f_of_x)  # Calculate default value
        self[key] = ret  # Save the default value in the local dictionary
        return ret


class ResultManager(object):
    def __init__(self):
        self._data = {}

    def assign(self, path_list: list, value):
        dv = self._data
        for item, next_item in pairwise(path_list):
            if next_item is None:
                # If next item is None then this is where the assignment to the value will take place
                if isinstance(dv, list):
                    dv[item] += [value]
                elif isinstance(dv, dict) and dv.get(item) is not None:
                    dv[item] = [dv[item], value]
                else:
                    dv[item] = value
                break

            elif isinstance(dv, list) and len(dv) <= item:
                # Special case for array indexing to extend the array thereby ensuring no IndexOutOfBounds exception is encountered
                dv += [None] * (item + 1 - len(dv))

            if isinstance(dv, dict) and dv.get(item) is not None:
                dv = dv[item]
            elif isinstance(dv, list) and len(dv) > item and dv[item] is not None:
                dv = dv[item]
            else:
                dv[item] = dv = type_generator(next_item)


class PropertyHolder(object):
    def __init__(self, matches: list = None):
        self.matches = [] if matches is None else matches
        self.array_bind = AutoDefaultDict(id_generator())

    def __repr__(self):
        return 'PropertyHolder({matches})'.format(matches=self.matches)


class PropertyManager(object):
    def __init__(self):
        self._properties = {}

    def __getitem__(self, key: Union[tuple, list]) -> PropertyHolder:
        key = tuple(key) if isinstance(key, list) else key
        v = self._properties.get(key)
        if not isinstance(v, PropertyHolder):
            v = self._properties[key] = PropertyHolder()
        return v

    # def __setitem__(self, key, value):
    #     self._properties[tuple(key) if isinstance(key, list) else key] = value


class Tree(object):
    """
    A recursive dictionary type object with tree context.
    """

    def __init__(self, dictionary: dict):
        self.dictionary = dictionary

    def __getitem__(self, item):
        return self.dictionary[item]

    def __repr__(self):
        return "Tree(" + repr(self.dictionary) + ")"


class TreeManager(object):
    def __init__(self, tree: Union[Tree, Dict], path: List[str]):
        self._tree = tree if isinstance(tree, Tree) else Tree(tree)
        self.path = path
        # self._dict = reduce(operator.getitem, [self._tree.dictionary] + path)
        self._dict = self._tree.dictionary
        for i in path:
            if isinstance(self._dict, dict):
                self._dict = self._dict[i]
            elif isinstance(self._dict, list):
                self._dict = self._dict[int(i)]
            elif self._dict == i:
                self._dict = None
            else:
                raise KeyError()

    def __getitem__(self, item: str):
        # type: (...) -> TreeManager
        return TreeManager(self._tree, self.path + [item])

    def __iter__(self):
        for key, value in self._dict.items():
            yield key, TreeManager(self._tree, self.path + [key])

    def __repr__(self):
        return 'TreeManager(' + repr(self.current_key) + ', ' + repr(self._dict) + ')'

    def keys(self):
        if isinstance(self._dict, dict):
            return self._dict.keys()
        elif isinstance(self._dict, list):
            return self._dict
        return [self._dict]

    @property
    def current_key(self):
        return self.path[-1] if self.path else None

    @property
    def value(self):
        return self._dict

    def ascend(self, levels: int):
        # type(...) -> DictWalker:
        if levels == 0:
            return self
        if levels < 0:
            # TODO raise exception here
            pass
        return TreeManager(self._tree, self.path[:-levels])

    def descend(self, key: Union[str, list]):
        # type(...) -> DictWalker:
        return TreeManager(self._tree, self.path + (key if isinstance(key, list) else [key]))
