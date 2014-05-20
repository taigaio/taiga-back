from collections import namedtuple

import pytest


class Object:
    pass


@pytest.fixture
def object():
    return Object()
