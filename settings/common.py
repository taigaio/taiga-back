# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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

import os.path, sys, os
from django.utils.translation import ugettext_lazy as _

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

OUT_BASE_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..")
)

APPEND_SLASH = False
ALLOWED_HOSTS = ["*"]

ADMINS = (
    ("Admin", "example@example.com"),
)

LANGUAGES = (
    ("en", _("English")),
    ("es", _("Spanish")),
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "taiga",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake"
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

# Default configuration for reverse proxy
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTOCOL", "https")

# Errors report configuration
SEND_BROKEN_LINK_EMAILS = True
IGNORABLE_404_ENDS = (".php", ".cgi")
IGNORABLE_404_STARTS = ("/phpmyadmin/",)


# Default django tz/i18n config
ATOMIC_REQUESTS = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en"
USE_I18N = True
USE_L10N = True
LOGIN_URL="/auth/login/"
USE_TZ = True

SITES = {
    1: {"domain": "localhost:8000", "scheme": "http"},
}

DOMAIN_ID = 1
SITE_ID = 1

# Session configuration (only used for admin)
SESSION_ENGINE="django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 1209600 # (2 weeks)

# MAIL OPTIONS
DEFAULT_FROM_EMAIL = "john@doe.com"
EMAIL_BACKEND = "djmail.backends.default.EmailBackend"

DJMAIL_REAL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DJMAIL_SEND_ASYNC = True
DJMAIL_MAX_RETRY_NUMBER = 3
DJMAIL_TEMPLATE_EXTENSION = "jinja"

# Events backend
EVENTS_PUSH_BACKEND = "taiga.events.backends.postgresql.EventsPushBackend"

# Message System
MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

# Static configuration.
MEDIA_ROOT = os.path.join(OUT_BASE_DIR, "media")
MEDIA_URL = "/media/"
STATIC_ROOT = os.path.join(OUT_BASE_DIR, "static")
STATIC_URL = "/static/"
ADMIN_MEDIA_PREFIX = "/static/admin/"

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Don't forget to use absolute paths, not relative paths.
)


# Defautl storage
DEFAULT_FILE_STORAGE = "taiga.base.storage.FileSystemStorage"


LOCALE_PATHS = (
    os.path.join(BASE_DIR, "locale"),
)

SECRET_KEY = "aw3+t2r(8(0kkrhg8)gx6i96v5^kv%6cfep9wxfom0%7dy0m9e"

TEMPLATE_LOADERS = [
    "django_jinja.loaders.AppLoader",
    "django_jinja.loaders.FileSystemLoader",
]

MIDDLEWARE_CLASSES = [
    "taiga.base.middleware.cors.CoorsMiddleware",
    "taiga.domains.middleware.DomainsMiddleware",
    "taiga.events.middleware.SessionIDMiddleware",

    # Common middlewares
    "django.middleware.common.CommonMiddleware",
    "django.middleware.locale.LocaleMiddleware",

    # Only needed by django admin
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

TEMPLATE_CONTEXT_PROCESSORS = [
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.request",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
]

ROOT_URLCONF = "taiga.urls"

TEMPLATE_DIRS = [
    os.path.join(BASE_DIR, "templates"),
]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.admin",
    "django.contrib.staticfiles",

    "taiga.base",
    "taiga.base.searches",
    "taiga.events",
    "taiga.domains",
    "taiga.front",
    "taiga.users",
    "taiga.projects",
    "taiga.projects.attachments",
    "taiga.projects.milestones",
    "taiga.projects.userstories",
    "taiga.projects.tasks",
    "taiga.projects.issues",
    "taiga.projects.wiki",
    "taiga.projects.history",
    "taiga.projects.notifications",

    "south",
    "reversion",
    "rest_framework",
    "djmail",
]

WSGI_APPLICATION = "taiga.wsgi.application"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse"
        }
    },
    "formatters": {
        "complete": {
            "format": "%(levelname)s:%(asctime)s:%(module)s %(message)s"
        },
        "simple": {
            "format": "%(levelname)s:%(asctime)s: %(message)s"
        },
        "null": {
            "format": "%(message)s",
        },
    },
    "handlers": {
        "null": {
            "level":"DEBUG",
            "class":"django.utils.log.NullHandler",
        },
        "console":{
            "level":"DEBUG",
            "class":"logging.StreamHandler",
            "formatter": "simple",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        }
    },
    "loggers": {
        "django": {
            "handlers":["null"],
            "propagate": True,
            "level":"INFO",
        },
        "django.request": {
            "handlers": ["mail_admins", "console"],
            "level": "ERROR",
            "propagate": False,
        },
        "taiga": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "taiga.domains": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    }
}


AUTH_USER_MODEL = "users.User"
FORMAT_MODULE_PATH = "taiga.base.formats"
DATE_INPUT_FORMATS = (
    "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%b %d %Y",
    "%b %d, %Y", "%d %b %Y", "%d %b, %Y", "%B %d %Y",
    "%B %d, %Y", "%d %B %Y", "%d %B, %Y"
)

# Authentication settings (only for django admin)
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend", # default
)

ANONYMOUS_USER_ID = -1
GRAPPELLI_INDEX_DASHBOARD = "taiga.dashboard.CustomIndexDashboard"

MAX_SEARCH_RESULTS = 100

# FIXME: this seems not be used by any module
API_LIMIT_PER_PAGE = 0

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        # Mainly used by taiga-front
        "taiga.auth.backends.Token",

        # Mainly used for api debug.
        "taiga.auth.backends.Session",
    ),
    "FILTER_BACKEND": "taiga.base.filters.FilterBackend",
    "EXCEPTION_HANDLER": "taiga.base.exceptions.exception_handler",
    "PAGINATE_BY": 30,
    "PAGINATE_BY_PARAM": "page_size",
    "MAX_PAGINATE_BY": 1000,
}

DEFAULT_PROJECT_TEMPLATE = "scrum"

# NOTE: DON'T INSERT MORE SETTINGS AFTER THIS LINE

TEST_RUNNER="django.test.runner.DiscoverRunner"

# Test conditions
if "test" in sys.argv:
    if "settings" not in ",".join(sys.argv):
        print ("\033[1;91mNot settings specified.\033[0m")
        print ("Try: \033[1;33mpython manage.py test --settings="
               "settings.testing -v2 taiga\033[0m")
        sys.exit(0)
