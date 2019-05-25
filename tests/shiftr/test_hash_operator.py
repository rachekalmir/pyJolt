import pytest
from pyjolt.transforms import shiftr


@pytest.mark.skip
def test_hash_default():
    #  jolt/jolt-core/src/test/resources/json/shiftr/hashDefault.json
    input_data = {
        "data": {
            "1234": {
                "clientId": "12",
                "hidden": True
            },
            "1235": {
                "clientId": "35",
                "hidden": False
            }
        }
    }
    spec = {
        "data": {
            "*": {
                "hidden": {
                    "true": {  # if hidden is true, then write the value disabled to the RHS output path
                        # Also @(3,clientId) means go up 3 levels, to the "1234" or "1235" level, then lookup / down the tree for the value of "clientId"
                        "#disabled": "clients.@(3,clientId)"
                    },
                    "false": {
                        "#enabled": "clients.@(3,clientId)"
                    }
                }
            }
        },
    }
    expected_output = {
        "clients": {
            "12": "disabled",
            "35": "enabled"
        }
    }

    factory = shiftr.shiftr_factory(spec=spec)
    output = factory.evaluate(data=input_data)

    assert expected_output == output


@pytest.mark.skip
def test_map_to_list1():
    #  jolt/jolt-core/src/test/resources/json/shiftr/mapToList.json
    input_data = {
        "ratings": {
            "primary": 5,
            "quality": 4
        }
    }
    spec = {
        "ratings": {
            "*": {
                # #2 means go two levels up the tree, and ask the "ratings" node, how many of its children have been matched
                #  this allows us to put the Name and the Value into the same object in the Ratings array
                "$": "Ratings[#2].Name",
                "@": "Ratings[#2].Value"
            }
        }
    }
    expected_output = {
        "Ratings": [
            {
                "Name": "primary",
                "Value": 5
            },
            {
                "Name": "quality",
                "Value": 4
            }
        ]
    }

    factory = shiftr.shiftr_factory(spec=spec)
    output = factory.evaluate(data=input_data)

    assert expected_output == output


@pytest.mark.skip
def test_map_to_list2():
    #  jolt/jolt-core/src/test/resources/json/shiftr/mapToList2.json
    input_data = {
        "cdvHisto": {
            "Expertise": {
                "Intermediate": 10
            },
            "HowLong": {
                "UpTo1Year": 4,
                "Under1Month": 3,
                "Over1Year": 3
            }
        }
    }
    spec = {
        "cdvHisto": {
            "*": {
                "$": ["ContextDataDistribution.&1.Id", "ContextDataDistribution.&1.Label"],
                "*": {
                    "@": "ContextDataDistribution.&2.Values.[#2].Count",
                    "$": "ContextDataDistribution.&2.Values.[#2].Value"
                }
            }
        }
    }
    expected_output = {
        "ContextDataDistribution": {
            "Expertise": {
                "Id": "Expertise",
                "Label": "Expertise",
                "Values": [
                    {
                        "Count": 10,
                        "Value": "Intermediate"
                    }
                ]
            },
            "HowLong": {
                "Id": "HowLong",
                "Label": "HowLong",
                "Values": [
                    {
                        "Count": 4,
                        "Value": "UpTo1Year"
                    },
                    {
                        "Count": 3,
                        "Value": "Under1Month"
                    },
                    {
                        "Count": 3,
                        "Value": "Over1Year"
                    }
                ]
            }
        }
    }

    factory = shiftr.shiftr_factory(spec=spec)
    output = factory.evaluate(data=input_data)

    assert expected_output == output
