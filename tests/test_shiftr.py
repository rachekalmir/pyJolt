from pyJolt.transforms import shiftr


def test_basic_shiftr():
    base_data = {
        "rating": {
            "quality": {
                "value": 3,
                "max": 5
            }
        }
    }
    spec = {
        "rating": {
            "quality": {
                "value": "SecondaryRatings.quality.Value",  # copy 3 to "SecondaryRatings.quality.Value"
                "max": "SecondaryRatings.quality.RatingRange"  # copy 5 to "SecondaryRatings.quality.RatingRange"
            }
        }
    }
    expected_output = {
        "SecondaryRatings": {
            "quality": {
                "Value": 3,
                "RatingRange": 5
            }
        }
    }

    output = shiftr.shift(spec=spec, data=base_data)

    assert expected_output == output
