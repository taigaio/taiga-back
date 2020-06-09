# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2017 Anler Hernández <hello@anler.me>
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

import ipaddress
import socket
from urllib.parse import urlparse

import django_sites as sites
from django.urls import reverse as django_reverse
from django.utils.translation import ugettext as _

URL_TEMPLATE = "{scheme}://{domain}/{path}"


def build_url(path, scheme="http", domain="localhost"):
    return URL_TEMPLATE.format(scheme=scheme, domain=domain, path=path.lstrip("/"))


def is_absolute_url(path):
    """Test wether or not `path` is absolute url."""
    return path.startswith("http")


def get_absolute_url(path):
    """Return a path as an absolute url."""
    if is_absolute_url(path):
        return path
    site = sites.get_current()
    return build_url(path, scheme=site.scheme, domain=site.domain)


def reverse(viewname, *args, **kwargs):
    """Same behavior as django's reverse but uses django_sites to compute absolute url."""
    return get_absolute_url(django_reverse(viewname, *args, **kwargs))


class HostnameException(Exception):
    pass


class IpAddresValueError(ValueError):
    pass


def validate_private_url(url):
    host = urlparse(url).hostname
    port = urlparse(url).port

    try:
        socket_args, *others = socket.getaddrinfo(host, port)
    except Exception:
        raise HostnameException(_("Host access error"))

    destination_address = socket_args[4][0]
    try:
        ipa = ipaddress.ip_address(destination_address)
    except ValueError:
        raise IpAddresValueError(_("IP Address error"))
    if ipa.is_private:
        raise IpAddresValueError("Private IP Address not allowed")
