# -*- coding: utf-8 -*-
# Copyright (C) 2014-present Taiga Agile LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from settings.common import * # noqa, pylint: disable=unused-wildcard-import

DEBUG = True

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


ENABLE_TELEMETRY = False
