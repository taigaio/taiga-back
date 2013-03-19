# -*- coding: utf-8 -*-

from .common import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG
USE_ETAGS = True

MIDDLEWARE_CLASSES += [
    'django.middleware.http.ConditionalGetMiddleware',
    'django.middleware.gzip.GZipMiddleware',
]

LOGGING['loggers']['django.db.backends']['handlers'] = ['null']
LOGGING['loggers']['django.request']['handlers'] = ['mail_admins']
