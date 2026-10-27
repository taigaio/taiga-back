# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.conf import settings

from .models import InstanceDefaults


def allowed_languages():
    """Configured API locales, optionally narrowed to a deployed UI set."""
    deployed = getattr(settings, "INSTANCE_AVAILABLE_LANGUAGES", None)
    codes = {code for code, _name in settings.LANGUAGES}
    if deployed is not None:
        codes.intersection_update(deployed)
    return [(code, name) for code, name in settings.LANGUAGES if code in codes]


def allowed_themes():
    return tuple(getattr(settings, "INSTANCE_AVAILABLE_THEMES", ("taiga",)))


def deployment_language():
    return settings.LANGUAGE_CODE.lower().replace("_", "-")


def get_defaults():
    # A missing row or unavailable database is an error. Silent fallback could
    # change the language of a user-visible response or outgoing email.
    return InstanceDefaults.objects.get(pk=1)


def effective_language(defaults=None):
    defaults = defaults or get_defaults()
    allowed = {code for code, _name in allowed_languages()}
    if defaults.default_language in allowed:
        return defaults.default_language
    return deployment_language()


def effective_theme(defaults=None):
    defaults = defaults or get_defaults()
    if defaults.default_theme in allowed_themes():
        return defaults.default_theme
    return "taiga"


def recipient_language(user=None, defaults=None, project_language=None):
    allowed = {code for code, _name in allowed_languages()}
    explicit = getattr(user, "lang", None)
    if explicit and explicit in allowed:
        return explicit
    if project_language and project_language in allowed:
        return project_language
    return effective_language(defaults)
