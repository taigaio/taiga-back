# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from settings.common import * # noqa, pylint: disable=unused-wildcard-import

DEBUG = True

ENABLE_TELEMETRY = False

SECRET_KEY = "not very secret in tests"

TEMPLATES[0]["OPTIONS"]['context_processors'] += "django.template.context_processors.debug"

CELERY_ENABLED = False

MEDIA_ROOT = "/tmp"

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
INSTALLED_APPS = INSTALLED_APPS + [
    "tests",
]

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon-write": None,
    "anon-read": None,
    "user-write": None,
    "user-read": None,
    "import-mode": None,
    "import-dump-mode": None,
    "create-memberships": None,
    "login-fail": None,
    "register-success": None,
    "user-detail": None,
    "user-update": None,
}


IMPORTERS['github']['active'] = True
IMPORTERS['jira']['active'] = True
IMPORTERS['asana']['active'] = True
IMPORTERS['trello']['active'] = True

FRONT_SITEMAP_ENABLED = True
FRONT_SITEMAP_CACHE_TIMEOUT = 1  # In second
FRONT_SITEMAP_PAGE_SIZE = 100

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'taiga',
        'USER': 'taiga',
        'PASSWORD': 'taiga',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# This is only for GitHubActions
if os.getenv('GITHUB_WORKFLOW'):
    DATABASES = {
        'default': {
            "ENGINE": "django.db.backends.postgresql",
            'NAME': 'taiga',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
