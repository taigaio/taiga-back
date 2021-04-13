# -*- coding: utf-8 -*-
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
