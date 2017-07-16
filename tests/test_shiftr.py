from pyjolt.transforms import shiftr


def test_basic_shiftr():
    base_data = {
        "rating": {
            "quality": {
                "value": 3,
                "max": 5,
            },
        },
    }
    spec = {
        "rating": {
            "quality": {
                "value": "SecondaryRatings.quality.Value",  # copy 3 to "SecondaryRatings.quality.Value"
                "max": "SecondaryRatings.quality.RatingRange",  # copy 5 to "SecondaryRatings.quality.RatingRange"
            },
        },
    }
    expected_output = {
        "SecondaryRatings": {
            "quality": {
                "Value": 3,
                "RatingRange": 5,
            },
        },
    }

    factory = shiftr.shiftr_factory(spec=spec)
    output = factory.process(data=base_data, tree=[])

    assert expected_output == output


def test_amp_subkey_shiftr():
    base_data = {
        "foo": {
            "bar": {
                "baz": 0,  # & 0 = baz, & 1 = bar, & 2 = foo
                "bar": 2,
            },
        },
        "test-FOO-BAR": 1,
        "or1": 3,
        "or2": 4,
    }
    spec = {
        "foo": {
            "bar": {
                "baz": "&0-&1-&2",
                "&": "Spec",
            },
        },
        "test-*-*": "&(0,1)-&(0,2)",
        "or1|or2": "or",
    }
    expected_output = {
        "baz-bar-foo": 0,
        "FOO-BAR": 1,
        "Spec": 2,
        "or": [3, 4],
    }

    factory = shiftr.shiftr_factory(spec=spec)
    output = factory.process(data=base_data, tree=[])

    assert expected_output == output


def test_wildcard_multi_shiftr():
    base_data = {
        "rating": {
            "primary": {
                "value": 3,  # want this value to goto output path "Rating"
                "max": 5,  # want this value to goto output path "RatingRange"
            },
            "quality": {  # want output path "SecondaryRatings.quality.Id" = "quality", aka we want the value of the key to be used
                "value": 3,  # want this value to goto output path "SecondaryRatings.quality.Value"
                "max": 5,  # want this value to goto output path "SecondaryRatings.quality.Range"
            },
            "sharpness": {  # want output path "SecondaryRatings.sharpness.Id" = "sharpness"
                "value": 7,  # want this value to goto output path "SecondaryRatings.sharpness.Value"
                "max": 10,  # want this value to goto output path "SecondaryRatings.sharpness.Range"
            },
        },
    }
    spec = {
        "rating": {
            "primary": {
                "value": "Rating",  # output -> "Rating" : 3
                "max": "RatingRange",  # output -> "RatingRange" : 5
            },
            "*": {  # match input data like "rating.[anything-other-than-primary]"
                "value": "SecondaryRatings.&1.Value",  # the data at "rating.*.value" goes to "SecondaryRatings.*.Value"
                # the "&1" means use the value one level up the tree ( "quality" or "sharpness" )
                # output -> "SecondaryRatings.quality.Value" : 3 AND
                #           "SecondaryRatings.sharpness.Value" : 7

                "max": "SecondaryRatings.&1.Range",  # the data at "rating.*.max" goes to "SecondaryRatings.*.Range"
                # the "&1" means use the value one level up the tree ( "quality" or "sharpness" )
                # output -> "SecondaryRatings.quality.Range" : 5 AND
                #           "SecondaryRatings.sharpness.Range" : 10

                "$": "SecondaryRatings.&1.Id",
                # Special operator $ means, use the value of the input key itself as the data
                # output -> "SecondaryRatings.quality.Id" : "quality"
                # output -> "SecondaryRatings.sharpness.Id" : "sharpness"
            },
        },
    }
    expected_output = {
        "Rating": 3,
        "RatingRange": 5,
        "SecondaryRatings": {
            "quality": {
                "Range": 5,
                "Value": 3,
                "Id": "quality",
                # the special $ operator allows us to use input key the text value of "quality", as the "Id" of the output
            },
            "sharpness": {
                "Range": 10,
                "Value": 7,
                "Id": "sharpness",
                # the special $ operator allows us to use input key the text value of "sharpness", as the "Id" of the output
            },
        },
    }

    factory = shiftr.shiftr_factory(spec=spec)
    output = factory.process(data=base_data, tree=[])

    assert expected_output == output
