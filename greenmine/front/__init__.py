# -*- coding: utf-8 -*-

from django.conf import settings
from django_jinja import library

from greenmine.base import sites


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
    site = sites.get_active_site()
    url_tmpl = "{scheme}//{domain}{url}"

    scheme = site.scheme and "{0}:".format(site.scheme) or ""
    url = URLS[type].format(*args)
    return url_tmpl.format(scheme=scheme, domain=site.domain, url=url)
