# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from .common import *
import os

#########################################
## GENERIC
#########################################

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST'),
        'PORT': '5432',
    }
}

SECRET_KEY = os.getenv('TAIGA_SECRET_KEY')
MEDIA_URL = f"{ os.getenv('TAIGA_SITES_SCHEME') }://{ os.getenv('TAIGA_SITES_DOMAIN') }/media/"
STATIC_URL = f"{ os.getenv('TAIGA_SITES_SCHEME') }://{ os.getenv('TAIGA_SITES_DOMAIN') }/static/"
SITES["api"] = {
    "domain": f"{ os.getenv('TAIGA_SITES_DOMAIN') }",
    "scheme": f"{ os.getenv('TAIGA_SITES_SCHEME') }",
    "name": "api"
}

#########################################
## EVENTS
#########################################
EVENTS_PUSH_BACKEND = "taiga.events.backends.rabbitmq.EventsPushBackend"
EVENTS_PUSH_BACKEND_OPTIONS = {
    "url": f"amqp://{ os.getenv('RABBITMQ_USER') }:{ os.getenv('RABBITMQ_PASS') }@taiga-rabbitmq:5672/taiga"
}

#########################################
## CONTRIBS
#########################################
INSTALLED_APPS += [
    "taiga_contrib_slack",
    "taiga_contrib_github_auth",
    "taiga_contrib_gitlab_auth"
]

GITHUB_API_CLIENT_ID = os.getenv('GITHUB_API_CLIENT_ID')
GITHUB_API_CLIENT_SECRET = os.getenv('GITHUB_API_CLIENT_SECRET')

GITLAB_API_CLIENT_ID = os.getenv('GITLAB_API_CLIENT_ID')
GITLAB_API_CLIENT_SECRET = os.getenv('GITLAB_API_CLIENT_SECRET')
GITLAB_URL = os.getenv('GITLAB_URL')
