# -*- coding: utf-8 -*-
from .development import *

SKIP_SOUTH_TESTS = True
SOUTH_TESTS_MIGRATE = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'greenmine',
        'USERNAME': 'postgres',
    }
}
