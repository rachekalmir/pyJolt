import operator
import re
from functools import reduce, partial
from queue import Queue
from typing import List, Tuple, Match

from pyjolt.util import translate
from pyjolt.util.tree_manager import TreeManager, recursive_dict, PropertyManager, PropertyHolder


class JoltException(Exception):
    pass


def process_amp(data: TreeManager, spec: TreeManager, properties: PropertyManager, match: Match) -> str:
    """
    Process Ampersand matches and replace the & expression with the resolved value

    match: is the regular expression match and groups should 3 match groups &{0} | &({0},{0})
    """
    ascend = int(match.groups()[0] or match.groups()[1] or 0)
    descend = int(match.groups()[2] or 0) if (match.groups()[2] or '0').isnumeric() else match.groups()[2]

    # return the processed pattern result
    if isinstance(descend, int):
        if descend == 0:
            return data.ascend(ascend).path[-1]
        return properties[data.ascend(ascend).path].matches.groups()[descend-1]
    elif isinstance(descend, str):
        return data.ascend(ascend)[descend]
    elif isinstance(descend, list):
        return reduce(operator.getitem, [data.ascend(ascend)] + descend)
    raise JoltException()


def match_re(spec_key: str, properties: PropertyHolder, key: str):
    match = re.match(translate(spec_key), key)
    if match:
        properties.matches = match
    return key if match else None


def process_sub_amp(data: TreeManager, spec: TreeManager, properties: PropertyManager, v: str):
    return re.sub(r'&([0-9]*)(?!\()|&(?:\(([0-9]+)(?:, ?([0-9]+))*\))?', partial(process_amp, data, spec, properties), v)


def process_spec_rhs(data: TreeManager, spec: TreeManager, properties: PropertyManager) -> List[str]:
    # Process Ampersand (&)
    matches = [process_sub_amp(data, spec, properties, v) for v in spec.value.split('.')]
    return matches


def shiftr(data: dict, spec: dict) -> dict:
    data_manager = TreeManager(data, [])
    spec_manager = TreeManager(spec, [])
    process_queue = Queue()

    result = recursive_dict()

    # TODO: walk through data and spec
    process_queue.put((spec_manager, data_manager))

    properties = PropertyManager()

    while not process_queue.empty():
        spec, data = process_queue.get()

        # if the data is not a leaf node then try match against the spec
        if isinstance(data.value, dict):
            for spec_key in spec.keys():
                # Cache keys so that each matched key can be removed (for certain match cases)
                data_keys = set(data.keys())

                # Match exact keys
                matches = set(filter(spec_key.__eq__, data_keys))
                data_keys -= matches

                # Match wildcard keys and return match objects for property caching
                # Amp (&) resolution of the specification key will also occur here
                wildcard_matches = set(filter(None.__ne__, map(lambda x: match_re(spec_key, properties[tuple(data.path + [x])], x), data_keys)))
                matches |= wildcard_matches
                data_keys -= wildcard_matches

                # Try transform & and match
                other_matches = set(filter(process_sub_amp(data, spec, properties, spec_key).__eq__, data_keys))
                matches |= other_matches

                # Add next level of data that matched to be processed against the next level of the spec
                if matches:
                    list(map(process_queue.put, [(spec[spec_key], data[key]) for key in matches]))
        else:
            # if this is a leaf node node process the RHS (leaf) spec and save the value in result
            spec_value_split = process_spec_rhs(data, spec, properties)
            v = reduce(operator.getitem, [result] + spec_value_split[:-1])

            # If a second key maps to the same final key then turn it into an array
            t = v.get(spec_value_split[-1])
            if t is None:
                v[spec_value_split[-1]] = data.value
            elif isinstance(t, list):
                v[spec_value_split[-1]] += [data.value]
            else:
                v[spec_value_split[-1]] = [t, data.value]

    return result
