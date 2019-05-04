import re
from collections import defaultdict


class UnsortedList(list):
    def __init__(self, data=None):
        super().__init__(data if data is not None else [])

    def __eq__(self, other):
        return sorted(self) == sorted(other)


def recursive_dict():
    return defaultdict(recursive_dict)


def translate(pat):
    """Translate a shell PATTERN to a regular expression.

    There is no way to quote meta-characters.

    Adapted from the Python3 standard library (fnmatch) to add capturing groups around matches.
    """

    i, n = 0, len(pat)
    res = ''
    while i < n:
        c = pat[i]
        i = i + 1
        if c == '*':
            res = res + '(.*)'
        elif c == '?':
            res = res + '.'
        elif c == '[':
            j = i
            if j < n and pat[j] == '!':
                j = j + 1
            if j < n and pat[j] == ']':
                j = j + 1
            while j < n and pat[j] != ']':
                j = j + 1
            if j >= n:
                res = res + '\\['
            else:
                stuff = pat[i:j].replace('\\', '\\\\')
                i = j + 1
                if stuff[0] == '!':
                    stuff = '^' + stuff[1:]
                elif stuff[0] == '^':
                    stuff = '\\' + stuff
                res = '%s[%s]' % (res, stuff)
        else:
            res = res + re.escape(c)
    return '(?ms)' + res + r'\Z'
