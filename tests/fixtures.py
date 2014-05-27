import pytest


class Object:
    pass


@pytest.fixture
def object():
    return Object()


@pytest.fixture
def client():
    from testclient_extensions import Client

    return Client()
