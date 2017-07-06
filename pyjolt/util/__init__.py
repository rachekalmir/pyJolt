from collections import defaultdict


def recursive_dict():
    return defaultdict(recursive_dict)
