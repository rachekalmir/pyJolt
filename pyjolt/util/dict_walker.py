from typing import Union


def apply_list_to_dict(dct: dict, lst: list):
    try:
        for item in lst:
            dct = dct[item]
        return dct
    except TypeError:  # catch the case where dct is not subscriptable
        return None


class DictWalker(object):
    def __init__(self, dictionary: dict, tree: list = None, match_group: list = None):
        if tree is None:
            tree = []
        if match_group is None:
            match_group = []

        self._dictionary = dictionary
        self._tree = tree
        self._match_group = match_group
        self._dict_cache = apply_list_to_dict(dictionary, tree)

    def __getitem__(self, item):
        return self._dict_cache[item]

    def __repr__(self):
        return str(self._dict_cache)

    def value_type(self, compare_type: type) -> bool:
        return isinstance(self._dict_cache, compare_type)

    def items(self):
        if isinstance(self._dict_cache, dict):
            return self._dict_cache.items()
        else:
            return self._dict_cache

    def tree(self) -> list:
        return list(iter(self._tree))

    def match_group(self, number: int) -> list:
        if number == 0:
            return self._tree[-1]
        else:
            return self._match_group[-1][1 - number]

    def ascend(self, levels: int):
        # type(...) -> DictWalker:
        if levels == 0:
            return self
        if levels < 0:
            pass
            # TODO raise exception here
        return DictWalker(self._dictionary, self._tree[:-levels], self._match_group[:-levels])

    def descend(self, key: Union[str, list], match_group: Union[list, tuple] = None) -> DictWalker:
        return DictWalker(self._dictionary,
                          self._tree + (key if isinstance(key, list) else [key]),
                          self._match_group + [match_group if match_group is not None else ()])
