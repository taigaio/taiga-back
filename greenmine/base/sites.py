# -*- coding: utf-8 -*-

import logging
from threading import local

from django.db.models import get_model
from django.core.exceptions import ImproperlyConfigured

from . import exceptions as exc


_local = local()
log = logging.getLogger("greenmine.sites")


class SiteNotFound(exc.BaseException):
    pass


def get_default_site():
    from django.conf import settings
    try:
        sid = settings.SITE_ID
    except AttributeError:
        raise ImproperlyConfigured("You're using the \"sites framework\" without having "
                                   "set the SITE_ID setting. Create a site in your database "
                                   "and set the SITE_ID setting to fix this error.")

    model_cls = get_model("base", "Site")
    cached = getattr(_local, "default_site", None)
    if cached is None:
        try:
            cached = _local.default_site = model_cls.objects.get(pk=sid)
        except model_cls.DoesNotExist:
            raise ImproperlyConfigured("default site not found on database.")

    return cached


def get_site_for_domain(domain):
    log.debug("Trying activate site for domain: {}".format(domain))
    cache = getattr(_local, "cache", {})

    if domain in cache:
        return cache[domain]

    model_cls = get_model("base", "Site")

    try:
        site = model_cls.objects.get(domain=domain)
    except model_cls.DoesNotExist:
        log.warning("Site does not exist for domain: {}".format(domain))
        raise SiteNotFound("site not found")
    else:
        cache[domain] = site

    return site


def activate(site):
    log.debug("Activating site: {}".format(site))
    _local.active_site = site


def deactivate():
    if hasattr(_local, "active_site"):
        log.debug("Deactivating site: {}".format(_local.active_site))
        del _local.active_site


def get_active_site():
    active_site = getattr(_local, "active_site", None)
    if active_site is None:
        return get_default_site()
    return active_site

def clear_site_cache(**kwargs):
    if hasattr(_local, "default_site"):
        del _local.default_site

    if hasattr(_local, "cache"):
        del _local.cache
