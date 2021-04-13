# -*- coding: utf-8 -*-
from ..utils import disconnect_signals


def pytest_runtest_setup(item):
    disconnect_signals()
