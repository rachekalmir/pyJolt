from pyjolt import Jolt
from tests.shiftr import assert_shiftr


def test_array_mismatch():
    # Context: Shiftr will only operate if / when it finds matches
    # Purpose: Verify that Shiftr operates even when it is faced with array mismatches
    input_data = {
        "id": "reviewId",
        "text": "This is a review.",
        "rating": 5,

        "statistics": {
            "id": "statsId",
            "feedbackCount": "10"
        },
        "author": [
            {
                "id": "authorId",
                "name": "Author Name"
            }
        ]
    }
    spec = {
        "id": "Id",
        "text": "ReviewText",
        "rating": "Rating",

        "statistics": {
            "0": {
                "feedbackCount": "FeedbackCount"
            }
        },
        "author": {
            "id": "AuthorId",
            "name": "AuthorName"
        }
    }
    expected_output = {

        "Id": "reviewId",
        "ReviewText": "This is a review.",
        "Rating": 5
    }
    assert_shiftr(expected_output, Jolt(input_data).shift(spec).data)


def test_array_example():
    input_data = {
        "Photos": [
            {
                "Id": "1234",
                "Caption": "photo 1",
                "Sizes": {
                    "thumbnail": {
                        "Url": "http://test.com/0001/1234/photoThumb.jpg",
                        "Id": "thumbnail"
                    },
                    "normal": {
                        "Url": "http://test.com/0001/1234/photo.jpg",
                        "Id": "normal"
                    }
                },
                "SizesOrder": [
                    "thumbnail",
                    "normal"
                ]
            },
            {
                "Id": "5678",
                "Caption": "photo 2",
                "Sizes": {
                    "thumbnail": {
                        "Url": "http://test.com/0001/5678/photoThumb.jpg",
                        "Id": "thumbnail"
                    },
                    "normal": {
                        "Url": "http://test.com/0001/5678/photo.jpg",
                        "Id": "normal"
                    }
                },
                "SizesOrder": [
                    "thumbnail",
                    "normal"
                ]
            }
        ]
    }
    # We aren't radically transforming the data here, just changing the case of the keys.
    # This illustrates the usage of the '[]' and '&' operators, to put all the content in the right place, aka maintain order
    spec = {
        "Photos": {
            "*": {
                "Id": "photos[&1].id",
                "Caption": "photos[&1].caption",
                "Sizes": {
                    "*": {
                        "Url": "photos[&3].sizes.&1"
                    }
                },
                "SizesOrder": "photos[&1].sizesOrder"
            }
        }
    }
    expected_output = {
        "photos": [
            {
                "id": "1234",
                "caption": "photo 1",
                "sizes": {
                    "thumbnail": "http://test.com/0001/1234/photoThumb.jpg",
                    "normal": "http://test.com/0001/1234/photo.jpg"
                },
                "sizesOrder": [
                    "thumbnail",
                    "normal"
                ]
            },
            {
                "id": "5678",
                "caption": "photo 2",
                "sizes": {
                    "thumbnail": "http://test.com/0001/5678/photoThumb.jpg",
                    "normal": "http://test.com/0001/5678/photo.jpg"
                },
                "sizesOrder": [
                    "thumbnail",
                    "normal"
                ]
            }
        ]
    }
    assert_shiftr(expected_output, Jolt(input_data).shift(spec).data)
