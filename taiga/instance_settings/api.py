# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.db import transaction

from taiga.auth.authentication import JWTAuthentication
from taiga.base import response
from taiga.base.api.views import APIView

from .models import InstanceDefaults, InstanceDefaultsAudit
from . import services


def no_store(result):
    result["Cache-Control"] = "no-store"
    return result


def admin_allowed(request):
    user = request.user
    return user.is_authenticated and user.is_active and user.is_superuser


class PublicInstanceDefaultsView(APIView):
    """Small, public bootstrap payload; no administrator or environment data."""

    def get(self, request):
        defaults = services.get_defaults()
        available_languages = {code for code, _name in services.allowed_languages()}
        return no_store(response.Ok({
            "default_language": (defaults.default_language
                                 if defaults.default_language in available_languages
                                 else None),
            "default_theme": (defaults.default_theme
                              if defaults.default_theme in services.allowed_themes()
                              else None),
            "revision": defaults.revision,
        }))


class AdminInstanceDefaultsView(APIView):
    """Read and update instance defaults as an authenticated superuser."""

    def describe(self, defaults):
        return {
            "default_language": defaults.default_language or None,
            "default_theme": defaults.default_theme or None,
            "revision": defaults.revision,
            "effective_language": services.effective_language(defaults),
            "effective_theme": services.effective_theme(defaults),
            "deployment_language": services.deployment_language(),
            "deployment_theme": "taiga",
            "languages": [{"code": code, "name": name}
                          for code, name in services.allowed_languages()],
            "themes": services.allowed_themes(),
        }

    def get(self, request):
        if not admin_allowed(request):
            return response.Forbidden({"detail": "Instance administrator required"})
        return no_store(response.Ok(self.describe(services.get_defaults())))

    def patch(self, request):
        if not admin_allowed(request):
            return response.Forbidden({"detail": "Instance administrator required"})
        # Taiga's optional API session authenticator skips CSRF. Writes require
        # the same bearer authentication used by the frontend application.
        if not isinstance(request.successful_authenticator, JWTAuthentication):
            return response.Forbidden({"detail": "Bearer authentication required"})

        data = request.DATA
        if not isinstance(data, dict) or set(data) != {
                "default_language", "default_theme", "revision"}:
            return response.BadRequest({"detail": "Expected default_language, default_theme, and revision"})
        revision = data["revision"]
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
            return response.BadRequest({"detail": "Invalid revision"})
        language = "" if data["default_language"] is None else data["default_language"]
        theme = "" if data["default_theme"] is None else data["default_theme"]
        if not isinstance(language, str) or not isinstance(theme, str):
            return response.BadRequest({"detail": "Defaults must be strings or null"})
        if language and language not in {code for code, _name in services.allowed_languages()}:
            return response.BadRequest({"detail": "Unsupported language"})
        if theme and theme not in services.allowed_themes():
            return response.BadRequest({"detail": "Unavailable theme"})

        with transaction.atomic():
            defaults = InstanceDefaults.objects.select_for_update().get(pk=1)
            if defaults.revision != revision:
                return no_store(response.Response(
                    {"detail": "Instance defaults changed; reload before saving"}, status=409))
            if (defaults.default_language, defaults.default_theme) != (language, theme):
                old_language, old_theme = defaults.default_language, defaults.default_theme
                defaults.default_language = language
                defaults.default_theme = theme
                defaults.revision += 1
                defaults.save(update_fields=["default_language", "default_theme", "revision"])
                InstanceDefaultsAudit.objects.create(
                    actor=request.user, old_language=old_language, new_language=language,
                    old_theme=old_theme, new_theme=theme, revision=defaults.revision)
        return no_store(response.Ok(self.describe(defaults)))
