from pyjolt import Jolt
from tests.shiftr import assert_shiftr


def test_wildcard():
    input_data = {
        "foo": 1,
        "bar": 2,
        "baz": 3,
        "tuna": 4,
        "tuna-1": 11,
        "tuna-2": 12,
        "tuna-3": 13,
        "tuna_2-1": 21,
        "tuna_2-2": 22,
        "tuna.3-1-1": 311,
        "tuna.3-1-2": 312
    }
    spec = {
        "foo": "a.b.c",
        "bar|baz": "a.b.d",
        "tuna": "a.b.e",

        "tuna.*-*-*": "a.b.3Star",
        "tuna_*-*": "a.b.2Star",
        "tuna-*": "a.b.1Star"
    }
    expected_output = {
        "a": {
            "b": {
                "c": 1,
                "d": [2, 3],
                "e": 4,
                "3Star": [311, 312],
                "2Star": [21, 22],
                "1Star": [11, 12, 13]

            }
        }
    }
    assert_shiftr(expected_output, Jolt(input_data).shift(spec).data)


def test_wildcard_self_and_ref():
    input_data = {
        "tag-Pro": ["Beautiful", "easy to apply"],
        "tag-Con": ["none"],

        "cdv-Fafa": "Groundhog",
        "cdv-Mario": "Red American"
    }
    spec = {
        "tag-*": {
            "@": ["TagDimensions.&(0,1).Values", "TagDimensions.&(1,1).Values-canonical1"],
            "$(0,1)": ["TagDimensions.&.Id", "TagDimensions.&(0,0).Id-canonical0", "TagDimensions.&0.Id-sugar0", "TagDimensions.&(1,1).Id-upref"]
        },

        "cdv-*": ["ContextDataValues.&(0,1).Value", "ContextDataValues.&(0,1).Value-sugar"]
    }
    expected_output = {
        "TagDimensions": {
            "Pro": {
                "Values": ["Beautiful", "easy to apply"],
                "Values-canonical1": ["Beautiful", "easy to apply"],

                "Id": "Pro",
                "Id-canonical0": "Pro",
                "Id-sugar0": "Pro",
                "Id-upref": "Pro"
            },
            "Con": {
                "Values": ["none"],
                "Values-canonical1": ["none"],

                "Id": "Con",
                "Id-canonical0": "Con",
                "Id-sugar0": "Con",
                "Id-upref": "Con"
            }
        },
        "ContextDataValues": {
            "Fafa": {
                "Value": "Groundhog",
                "Value-sugar": "Groundhog"
            },
            "Mario": {
                "Value": "Red American",
                "Value-sugar": "Red American"
            }
        }
    }
    assert_shiftr(expected_output, Jolt(input_data).shift(spec).data)
