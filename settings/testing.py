# -*- coding: utf-8 -*-
from .development import *

SKIP_SOUTH_TESTS = True
SOUTH_TESTS_MIGRATE = False

INSTALLED_APPS += [
    "taiga.projects.mixins.blocked.tests.foo",
]
