from collections import defaultdict
from typing import Union, List, Dict


def recursive_dict():
    return defaultdict(recursive_dict)


class PropertyHolder(object):
    def __init__(self, matches: list = None):
        self.matches = [] if matches is None else matches

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
