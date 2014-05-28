import pytest
import os.path
from functools import lru_cache

from django.conf import settings

from .fixtures import *


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", help="run slow tests")


def pytest_runtest_setup(item):
    if "slow" in item.keywords and not item.config.getoption("--runslow"):
        pytest.skip("need --runslow option to run")

@lru_cache(maxsize=4)
def _get_sql():
    path = os.path.join(settings.BASE_DIR, "sql", "tags.sql")
    with open(path, "r") as f:
        return f.read()


def on_db_connect(sender, connection, **kwargs):
    cursor = connection.cursor()
    cursor.execute(_get_sql())


from django.db.backends import signals
signals.connection_created.connect(on_db_connect)
