# -*- coding: utf-8 -*-
import pytest
import django
from .fixtures import *


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", help="run slow tests")


def pytest_runtest_setup(item):
    if "slow" in item.keywords and not item.config.getoption("--runslow"):
        pytest.skip("need --runslow option to run")


def pytest_configure(config):
    django.setup()
    from taiga.celery import app
    app.conf.task_always_eager = True
