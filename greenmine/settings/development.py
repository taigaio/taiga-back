# -*- coding: utf-8 -*-

from .common import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG
USE_ETAGS = False

SESSION_ENGINE='django.contrib.sessions.backends.db'

TEMPLATE_CONTEXT_PROCESSORS += [
    "django.core.context_processors.debug",
]
