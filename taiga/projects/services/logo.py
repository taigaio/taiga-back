# -*- coding: utf-8 -*-
from django.conf import settings

from taiga.base.utils.thumbnails import get_thumbnail_url


def get_logo_small_thumbnail_url(project):
    if project.logo:
        return get_thumbnail_url(project.logo, settings.THN_LOGO_SMALL)
    return None


def get_logo_big_thumbnail_url(project):
    if project.logo:
        return get_thumbnail_url(project.logo, settings.THN_LOGO_BIG)
    return None
