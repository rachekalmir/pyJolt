import os
from json import JSONDecodeError

import jsoncomment

from tests.test_transformations import JoltTestObject


def read_file(path: str) -> str:
    with open(path) as f:
        return f.read()


def pytest_generate_tests(metafunc):
    if "test_shiftr" == metafunc.definition.name:
        jsc = jsoncomment.JsonComment()
        os_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'shiftr_tests_disabled')
        lst = []
        ids = []
        for json_file in os.listdir(os_path):
            try:
                js = jsc.loads(read_file(os.path.join(os_path, json_file)))
                lst.append(JoltTestObject(json_file, js['input'], js['spec'], js['expected']))
                ids.append(json_file)
            except JSONDecodeError:
                pass
        metafunc.parametrize("shiftr_test", lst, ids=ids)
