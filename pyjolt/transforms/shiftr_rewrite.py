import operator
import re
from distutils.util import strtobool
from functools import reduce, partial, cmp_to_key
from queue import Queue
from typing import List, Match, Union

from pyjolt.exceptions import JoltException
from pyjolt.util import translate
from pyjolt.util.tree_manager import TreeManager, PropertyManager, PropertyHolder, ResultManager


def spec_key_comparator(key_a: str, key_b: str) -> int:
    """
    Comparator to sort spec keys putting the '*' key last.
    """
    if key_a == '*':
        return 1
    elif key_b == '*':
        return -1
    return key_a.__lt__(key_b)


def get_operator_value(data: TreeManager, spec: TreeManager, properties: PropertyManager, match: Match) -> str:
    if match.group()[0] == '&':
        property_holder = properties[tuple(data.path), tuple(spec.path)] or properties[tuple(data.path), tuple(spec.path)]
        return property_holder.matches[0] if len(property_holder.matches) > 0 else data.current_key
    elif match.group()[0] == '@':
        return data.value
    elif match.group()[0] == '$':
        return data.current_key
    raise JoltException()


def literal_compare(spec_key: str, data_key: Union[str, bool]):
    # If data_key is a boolean then compare by converting spec_key to a boolean also
    if isinstance(data_key, bool):
        return strtobool(spec_key) == data_key
    # Otherwise compare spec_key and data_key directly after replacing Jolt operators @,$,&,[]
    return re.sub(r'\\([$@&[\]*#])', r'\g<1>', spec_key) == data_key


def process_amp(data: TreeManager, spec: TreeManager, properties: PropertyManager, match: Match, lookup_offset=0) -> str:
    """
    Process Ampersand matches and replace the & expression with the resolved value

    match: is the regular expression match and groups should 3 match groups &{0} | &({0},{0})
    """
    if match.group()[0] == '[':
        ascend = int(re.match(r'\[#([0-9]+)\]', match.group()).groups()[0])
        # Use a default dict in the property class to return the index
        return properties[data.path[:-ascend + 1]].array_bind[data.current_key]
    elif match.group()[0] == '\\':
        # Catch the case where \ is used to escape an operator []@#$& or \ itself
        return match.group()[1:]

    ascend = int(match.groups()[0] or match.groups()[1] or 0) - lookup_offset
    descend = int(match.groups()[2] or 0) if (match.groups()[2] or '0').isnumeric() else match.groups()[2]

    # Return the processed &,@ pattern result by ascending and descending the data tree
    if isinstance(descend, int):
        if descend == 0:
            return get_operator_value(data.ascend(ascend), spec.ascend(ascend), properties, match)
        return properties[data.ascend(ascend).path].matches[descend]
    elif isinstance(descend, str):
        # Spec is not defined for string key descent
        return get_operator_value(data.ascend(ascend - 1)[descend], None, properties, match)
    elif isinstance(descend, list):
        return reduce(operator.getitem, [data.ascend(ascend)] + descend)
    raise JoltException()


def match_re(spec_key: str, property_holder: PropertyHolder, key: str):
    """
    Translate wildcards in the spec_key into a regular expression and return the match if one is found

    :param spec_key: specification key to translate and use to match
    :param property_holder: property holder object to store matches in
    :param key: the key to match against
    :return: key if there is a match otherwise None
    """
    if isinstance(key, str):
        match = re.match(translate(spec_key), key)
        if match:
            property_holder.matches = [key] + list(match.groups())
            return key
    return None


def process_sub_amp(data: TreeManager, spec: TreeManager, properties: PropertyManager, string: str, lookup_offset=0):
    """
    Process @,$,&,[] operator expressions and return the relevant string or object

    :param data:
    :param spec:
    :param properties:
    :param string:
    :param lookup_offset:
    :return:
    """
    matches = list(re.finditer(r'(?<!\\)[&@$](?:([0-9]*)(?!\()|(?:\(([0-9]+)(?:, *([0-9a-zA-Z_]+))*\))?)|^\[#[0-9]+\]$', string))
    if len(matches) == 1:
        return process_amp(data, spec, properties, matches[0], lookup_offset=lookup_offset)
    # TODO: this can probably be optimised by using matches instead of re.sub
    return re.sub(r'(?<!\\)[&@$](?:([0-9]*)(?!\()|(?:\(([0-9]+)(?:, *([0-9a-zA-Z_]+))*\))?)|(?<!\\)\\[\[\]@#$&*]',
                  partial(process_amp, data, spec, properties, lookup_offset=lookup_offset),
                  string)


def process_rhs_split(data: TreeManager, spec: TreeManager, properties: PropertyManager, lookup_offset=0) -> List[str]:
    """
    Split spec.value using '.', process each split using process_sub_amp
    :param data:
    :param spec:
    :param properties:
    :param lookup_offset:
    :return:
    """
    # Process & and $
    # re.sub is used to replace Key[#2] with Key.[#2] for compatibility with Jolt protocol
    return [process_sub_amp(data, spec, properties, v, lookup_offset) for v in re.sub(r'(?<![.\\])(\[[^]]+\])', r'.\g<1>', spec.value).split('.')]


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

    # Walk through data and spec
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

                # First process LHS $ and @ matches
                # $ - use current data key as value and place into result
                # @ - use current data value as value and place into result
                if spec_key.startswith(('$', '@')):
                    # If the spec is a list of target values then process each one in turn
                    for spec_process in spec[spec_key] if isinstance(spec[spec_key].value, list) else [spec[spec_key]]:
                        if spec_key.startswith('$'):
                            properties[tuple(data.path), tuple(spec.path)].matches = [process_sub_amp(data, spec_process, properties, spec_key)]
                            # properties[tuple(data.path)].matches = [data.current_key, process_sub_amp(data, spec_process, properties, spec_key)]
                            value = process_sub_amp(data, spec_process, properties, spec_key)
                        else:
                            value = data.value
                        process_rhs(data, spec_process, properties, result, value, lookup_offset=1)
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
                    list(map(process_queue.put, [(spec[spec_key], data[key]) for key in matches]))
        else:
            # Catch special cases of the # that is allowed in the spec beyond the end of the data
            if isinstance(spec.value, dict):
                [process_rhs(data, spec[hash_key], properties, result, hash_key[1:]) for hash_key in spec.keys() if hash_key.startswith('#')]
            else:
                for spec_enum in spec if isinstance(spec.value, list) else [spec]:
                    process_rhs(data, spec_enum, properties, result, data.value)

    return result._data
