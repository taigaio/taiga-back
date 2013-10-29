# -*- coding: utf-8 -*-

from django.conf import settings
import django_sites as sites

from django_jinja import library


URLS = {
    "home": "/",
    "backlog": "/#/project/{0}/backlog/",
    "taskboard": "/#/project/{0}/taskboard/{1}",
    "userstory": "/#/project/{0}/user-story/{1}",
    "task": "/#/project/{0}/tasks/{1}",
    "issue": "/#/project/{0}/issues/{1}",
    "project-admin": "/#/project/{0}/admin",
    "change-password": "/#/change-password/{0}",
}


lib = library.Library()

def get_current_site():
    current_site_id = getattr(settings, "SITE_ID")
    front_sites = getattr(settings, "SITES_FRONT")
    return sites.Site(front_sites[current_site_id])


@lib.global_function(name="resolve_front_url")
def resolve(type, *args):
    site = get_current_site()
    url_tmpl = "{scheme}//{domain}{url}"

    scheme = site.scheme and "{0}:".format(site.scheme) or ""
    url = URLS[type].format(*args)
    return url_tmpl.format(scheme=scheme, domain=site.domain, url=url)
