# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
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

import logging
import functools
import threading

from django.db.models import get_model
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _

from taiga.base import exceptions as exc
log = logging.getLogger("taiga.domains")

_local = threading.local()


class DomainNotFound(exc.BaseException):
    pass


@functools.lru_cache(maxsize=1)
def get_default_domain():
    from django.conf import settings
    try:
        sid = settings.DOMAIN_ID
    except AttributeError:
        raise ImproperlyConfigured("You're using the \"domains framework\" without having "
                                   "set the DOMAIN_ID setting. Create a domain in your database "
                                   "and set the DOMAIN_ID setting to fix this error.")

    model_cls = get_model("domains", "Domain")
    try:
        return model_cls.objects.get(pk=sid)
    except model_cls.DoesNotExist:
        raise ImproperlyConfigured("default domain not found on database.")

@functools.lru_cache(maxsize=100, typed=True)
def get_domain_for_domain_name(domain:str, follow_alias:bool=True):
    log.debug("Trying activate domain for domain name: {}".format(domain))

    model_cls = get_model("domains", "Domain")

    try:
        domain = model_cls.objects.get(domain=domain)
    except model_cls.DoesNotExist:
        log.warning("Domain does not exist for domain: {}".format(domain))
        raise DomainNotFound(_("domain not found"))

    # Use `alias_of_id` instead of simple `alias_of` for performace reasons.
    if domain.alias_of_id is None or not follow_alias:
        return domain

    return domain.alias_of

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
    get_default_domain.cache_clear()
    get_domain_for_domain_name.cache_clear()
