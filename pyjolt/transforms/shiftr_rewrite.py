import operator
import re
from distutils.util import strtobool
from functools import reduce, partial, cmp_to_key
from queue import Queue
from typing import List, Match, Union

from exceptions import JoltException
from pyjolt.util import translate
from pyjolt.util.tree_manager import TreeManager, PropertyManager, PropertyHolder, ResultManager


def spec_key_comparator(key_a: str, key_b: str) -> int:
    if key_a == '*':
        return 1
    elif key_b == '*':
        return -1
    return key_a.__lt__(key_b)


def get_operator_value(tree: TreeManager, match: Match) -> str:
    if match.group()[0] == '&':
        return tree.current_key
    elif match.group()[0] == '@':
        return tree.value
    raise JoltException()


def literal_compare(spec_key: str, data_key: Union[str, bool]):
    if isinstance(data_key, bool):
        return strtobool(spec_key) == data_key
    return spec_key == data_key


def process_amp(data: TreeManager, spec: TreeManager, properties: PropertyManager, match: Match, lookup_offset=0) -> str:
    """
    Process Ampersand matches and replace the & expression with the resolved value

    match: is the regular expression match and groups should 3 match groups &{0} | &({0},{0})
    """
    if match.group()[0] == '[':
        ascend = int(re.match(r'\[#([0-9]+)\]', match.group()).groups()[0])
        # Use a default dict in the property class to return the index
        return properties[data.path[:-ascend + 1]].array_bind[data.current_key]

    ascend = int(match.groups()[0] or match.groups()[1] or 0) - lookup_offset
    descend = int(match.groups()[2] or 0) if (match.groups()[2] or '0').isnumeric() else match.groups()[2]

    # Return the processed &,@ pattern result by ascending and descending the data tree
    if isinstance(descend, int):
        if descend == 0:
            return get_operator_value(data.ascend(ascend), match)
        return properties[data.ascend(ascend).path].matches.groups()[descend - 1]
    elif isinstance(descend, str):
        return get_operator_value(data.ascend(ascend - 1)[descend], match)
    elif isinstance(descend, list):
        return reduce(operator.getitem, [data.ascend(ascend)] + descend)
    raise JoltException()


def match_re(spec_key: str, properties: PropertyHolder, key: str):
    if isinstance(key, str):
        match = re.match(translate(spec_key), key)
        if match:
            properties.matches = match
        return key if match else None
    return None


def process_sub_amp(data: TreeManager, spec: TreeManager, properties: PropertyManager, string: str, lookup_offset=0):
    matches = list(re.finditer(r'[&@]([0-9]*)(?!\()|[&@](?:\(([0-9]+)(?:, *([0-9a-zA-Z_]+))*\))?|^\[#[0-9]+\]$', string))
    if len(matches) == 1:
        return process_amp(data, spec, properties, matches[0], lookup_offset=lookup_offset)
    # TODO: this can probably be optimised by using matches instead of re.sub
    return re.sub(r'[&@]([0-9]*)(?!\()|[&@](?:\(([0-9]+)(?:, *([0-9a-zA-Z_]+))*\))?', partial(process_amp, data, spec, properties, lookup_offset=lookup_offset),
                  string)


def process_rhs_split(data: TreeManager, spec: TreeManager, properties: PropertyManager, lookup_offset=0) -> List[str]:
    # Process & and $
    # re.sub is used to replace Key[#2] with Key.[#2] for compatibility with Jolt protocol
    return [process_sub_amp(data, spec, properties, v, lookup_offset) for v in re.sub(r'(\[[^]]+\])', r'.\g<1>', spec.value).split('.')]


def process_rhs(data: TreeManager, spec: TreeManager, properties: PropertyManager, result: ResultManager, value, lookup_offset=0):
    """
    When the data runs and no more matches can be made against the data, then the rest of the spec is RHS spec.
    """
    # If this is a leaf node node process the RHS (leaf) spec and save the value in result
    result.assign(process_rhs_split(data, spec, properties, lookup_offset), value)


def shiftr(data: dict, spec: dict) -> dict:
    data_manager = TreeManager(data, [])
    spec_manager = TreeManager(spec, [])
    process_queue = Queue()

    result = ResultManager()

    # TODO: walk through data and spec
    process_queue.put((spec_manager, data_manager))

    properties = PropertyManager()

    while not process_queue.empty():
        spec, data = process_queue.get()  # type: TreeManager, TreeManager

        # if the data is not a leaf node then try match against the spec
        if (isinstance(spec.value, dict) and data.value is not None) or isinstance(data.value, dict):
            # Cache keys so that each matched key can be removed (for certain match cases)
            data_keys = set(data.keys())

            for spec_key in sorted(list(spec.keys()), key=cmp_to_key(spec_key_comparator)):
                # Match exact keys
                literal_matches = set(filter(partial(literal_compare, spec_key), data_keys))
                data_keys -= literal_matches

                # First process $ matches
                if spec_key == '$':
                    process_rhs(data, spec[spec_key], properties, result, data.current_key, lookup_offset=1)
                    continue
                if spec_key == '@':
                    process_rhs(data, spec[spec_key], properties, result, data.value, lookup_offset=1)
                    continue

                # Match wildcard keys and return match objects for property caching
                # Amp (&) resolution of the specification key will also occur here
                wildcard_matches = set(filter(None.__ne__, map(lambda x: match_re(spec_key, properties[tuple(data.path + [x])], x), data_keys)))
                data_keys -= wildcard_matches

                # Try transform & and match
                other_matches = set(filter(partial(literal_compare, process_sub_amp(data, spec, properties, spec_key)), data_keys))

                # Add next level of data that matched to be processed against the next level of the spec
                matches = literal_matches | wildcard_matches | other_matches
                if matches:
                    processors = [(spec[spec_key], data[key]) for key in matches]
                    list(map(process_queue.put, processors))
        else:
            # Catch special cases of the # that is allowed in the spec beyond the end of the data
            if isinstance(spec.value, dict):
                [process_rhs(data, spec[hash_key], properties, result, hash_key[1:]) for hash_key in spec.keys() if hash_key.startswith('#')]
            else:
                process_rhs(data, spec, properties, result, data.value)

    return result._data