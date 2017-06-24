from collections import defaultdict, Mapping
from fnmatch import fnmatch


def gen_defaultdict():
    return defaultdict(gen_defaultdict)


def update(base, update_dict):
    for key, value in update_dict.items():
        if isinstance(value, Mapping):
            r = update(base.get(key, {}), value)
            base[key] = r
        else:
            base[key] = update_dict[key]
    return base


def shift(spec, data):
    output = process_shift(spec, data)

    return output


def process_shift(spec: dict, data: dict, tree=None):
    result = gen_defaultdict()
    if tree is None:
        tree = []

    for key, value in spec.items():
        if type(value) is dict:
            # if there is a special character in the key, then find all the keys in the data where it matches
            if '*' in key:
                for inner_key in [k for k in set(data.keys()) - set(spec.keys()) if fnmatch(k, key)]:
                    result = update(result, process_shift(spec[key], data[inner_key], tree + [inner_key]))
            elif key in data:
                result = update(result, process_shift(spec[key], data[key], tree + [key]))
            else:
                # key doesn't exist in data, then ignore the spec
                pass
        else:
            p = result
            for ikey in value.split('.')[:-1]:
                if ikey.startswith('&'):
                    p = p[tree[-1]]
                else:
                    p = p[ikey]
            if key == '$':
                p[value.split('.')[-1]] = tree[-1]
            else:
                p[value.split('.')[-1]] = data[key]
    return result
