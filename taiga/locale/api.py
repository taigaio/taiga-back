# -*- coding: utf-8 -*-
from django.conf import settings

from taiga.base import response
from taiga.base.api.viewsets import ReadOnlyListViewSet

from . import permissions


class LocalesViewSet(ReadOnlyListViewSet):
    permission_classes = (permissions.LocalesPermission,)

    def list(self, request, *args, **kwargs):
        locales = [{"code": c, "name": n, "bidi": c in settings.LANGUAGES_BIDI} for c, n in settings.LANGUAGES]
        return response.Ok(locales)
