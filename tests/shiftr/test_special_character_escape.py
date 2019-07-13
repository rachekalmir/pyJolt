from pyjolt import Jolt
from tests.shiftr import assert_shiftr


def test_basic_special_character_escape():
    input_data = {
        "@context": "atSymbol",
        "$name": "Mojito",
        "&ingredient": "mint",
        "[yield": "open array",
        "[]yield": "full array",
        "]yield": "back array",
        "*": "star",
        "#": "hash",
        "(": "left paren"
    }
    spec = {
        # TEST escaping all the things when they are the first char(s) of the spec LHS and RHS
        "\\@context": "\\@A",
        "\\$name": "\\$B",
        "\\&ingredient": "\\&C",
        "\\[yield": "\\[D",
        "\\[\\]yield": "\\[\\]E",
        "\\]yield": "\\]F",
        "\\*": "\\*G",
        "\\#": "\\#H"
    }
    expected_output = {
        "@A": "atSymbol",
        "$B": "Mojito",
        "&C": "mint",
        "[D": "open array",
        "[]E": "full array",
        "]F": "back array",
        "*G": "star",
        "#H": "hash"
    }
    assert_shiftr(expected_output, Jolt(input_data).shift(spec).data)


def test_advanced_special_character_escape():
    input_data = {
        "aaa@context": "atSymbol",
        "bbb$name": "Mojito",
        "ccc&ingredient": "mint",
        "ddd[yield": "open array",
        "eee[]yield": "full array",
        "fff]yield": "back array",
        "ggg*": "star",
        "hhh#": "hash",
        "yyy(": "left paren"
    }
    spec = {
        # TEST escaping all the things when they are in the middle of the LHS and RHS keys
        "aaa\\@context": "aaa\\@A",
        "bbb\\$name": "bbb\\$B",
        "ccc\\&ingredient": "ccc\\&C",
        "ddd\\[yield": "ddd\\[D",
        "eee\\[\\]yield": "eee\\[\\]E",
        "fff\\]yield": "fff\\]F",
        "ggg\\*": "ggg\\*G",
        "hhh\\#": "hhh\\#H"
    }
    expected_output = {
        "aaa@A": "atSymbol",
        "bbb$B": "Mojito",
        "ccc&C": "mint",
        "ddd[D": "open array",
        "eee[]E": "full array",
        "fff]F": "back array",
        "ggg*G": "star",
        "hhh#H": "hash"
    }
    assert_shiftr(expected_output, Jolt(input_data).shift(spec).data)
