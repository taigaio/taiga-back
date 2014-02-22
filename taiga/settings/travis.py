# -*- coding: utf-8 -*-
from .testing import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'taiga',
        'USERNAME': 'postgres',
    }
}
