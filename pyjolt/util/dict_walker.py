from copy import copy


def apply_list_to_dict(dct,  # type: dict
                       lst,  # type: list
                       ):
    try:
        for item in lst:
            dct = dct[item]
        return dct
    except TypeError:  # catch the case where dct is not subscriptable
        return None


class DictWalker(object):
    def __init__(self,
                 dictionary,  # type: dict
                 tree=None  # type: list
                 ):
        if tree is None:
            tree = []

        self._dictionary = dictionary
        self._tree = tree
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

    def tree(self):
        # type: (...) -> Iterator
        return list(iter(self._tree))

    def ascend(self,
               levels  # type: int
               ):
        # type: (...) -> DictWalker

        return DictWalker(self._dictionary, self._tree[:-levels])

    def descend(self,
                key,  # type: Union[str, list]
                ):
        # type: (...) -> DictWalker
        return DictWalker(self._dictionary, self._tree + (key if type(key) == list else [key]))
