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
                 tree=None,  # type: list
                 match_group=None,  # type: list
                 ):
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

    def tree(self):
        # type: (...) -> list
        return list(iter(self._tree))

    def match_group(self, number: int):
        # type: (...) -> list
        if number == 0:
            return self._tree[-1]
        else:
            return self._match_group[-1][1 - number]

    def ascend(self,
               levels  # type: int
               ):
        # type: (...) -> DictWalker
        if levels == 0:
            return self
        if levels < 0:
            pass
            # TODO raise exception here
        return DictWalker(self._dictionary, self._tree[:-levels], self._match_group[:-levels])

    def descend(self,
                key,  # type: Union[str, list]
                match_group=None,  # type: Union[list, tuple]
                ):
        # type: (...) -> DictWalker
        return DictWalker(self._dictionary,
                          self._tree + (key if isinstance(key, list) else [key]),
                          self._match_group + [match_group if match_group is not None else ()])
