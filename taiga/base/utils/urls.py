# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import ipaddress
import socket
from urllib.parse import urlparse

import django_sites as sites
from django.urls import reverse as django_reverse
from django.utils.translation import gettext as _

URL_TEMPLATE = "{scheme}://{domain}/{path}"

# Schemes that execute code when used as an href. Everything else is allowed:
# app schemes (obsidian://, vscode://, zotero://...) are legitimate links and no
# allowlist can enumerate them.
HARMFUL_URL_SCHEMES = frozenset(("javascript", "data", "vbscript"))


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


def has_harmful_scheme(url):
    """Test whether `url` uses a scheme that executes code in an href."""
    # Browsers ignore control characters and spaces inside the scheme, so
    # "java\tscript:alert(1)" still runs; drop them before reading it.
    scheme, separator, _ = "".join(c for c in url if ord(c) > 0x20).lower().partition(":")
    return bool(separator) and scheme in HARMFUL_URL_SCHEMES


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
