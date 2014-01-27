# -*- coding: utf-8 -*-

from django.conf import settings
from django_jinja import library

from taiga.base import domains


URLS = {
    "home": "/",
    "backlog": "/#/project/{0}/backlog/",
    "taskboard": "/#/project/{0}/taskboard/{1}",
    "userstory": "/#/project/{0}/user-story/{1}",
    "task": "/#/project/{0}/tasks/{1}",
    "issue": "/#/project/{0}/issues/{1}",
    "project-admin": "/#/project/{0}/admin",
    "change-password": "/#/change-password/{0}",
    "invitation": "/#/invitation/{0}",
}


lib = library.Library()


@lib.global_function(name="resolve_front_url")
def resolve(type, *args):
    domain = domains.get_active_domain()
    url_tmpl = "{scheme}//{domain}{url}"

    scheme = domain.scheme and "{0}:".format(domain.scheme) or ""
    url = URLS[type].format(*args)
    return url_tmpl.format(scheme=scheme, domain=domain.domain, url=url)
