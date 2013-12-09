# -*- coding: utf-8 -*-

import logging
from threading import local

from django.db.models import get_model
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _

from .. import exceptions as exc


_local = local()
log = logging.getLogger("greenmine.domains")


class DomainNotFound(exc.BaseException):
    pass


def get_default_domain():
    from django.conf import settings
    try:
        sid = settings.SITE_ID
    except AttributeError:
        raise ImproperlyConfigured("You're using the \"domains framework\" without having "
                                   "set the DOMAIN_ID setting. Create a domain in your database "
                                   "and set the DOMAIN_ID setting to fix this error.")

    model_cls = get_model("domains", "Domain")
    cached = getattr(_local, "default_domain", None)
    if cached is None:
        try:
            cached = _local.default_domain = model_cls.objects.get(pk=sid)
        except model_cls.DoesNotExist:
            raise ImproperlyConfigured("default domain not found on database.")

    return cached


def get_domain_for_domain_name(domain):
    log.debug("Trying activate domain for domain name: {}".format(domain))
    cache = getattr(_local, "cache", {})

    if domain in cache:
        return cache[domain]

    model_cls = get_model("domains", "Domain")

    try:
        domain = model_cls.objects.get(domain=domain)
    except model_cls.DoesNotExist:
        log.warning("Domain does not exist for domain: {}".format(domain))
        raise DomainNotFound(_("domain not found"))
    else:
        cache[domain] = domain

    return domain


def activate(domain):
    log.debug("Activating domain: {}".format(domain))
    _local.active_domain = domain


def deactivate():
    if hasattr(_local, "active_domain"):
        log.debug("Deactivating domain: {}".format(_local.active_domain))
        del _local.active_domain


def get_active_domain():
    active_domain = getattr(_local, "active_domain", None)
    if active_domain is None:
        return get_default_domain()
    return active_domain

def clear_domain_cache(**kwargs):
    if hasattr(_local, "default_domain"):
        del _local.default_domain

    if hasattr(_local, "cache"):
        del _local.cache
