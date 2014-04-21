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

from django.conf import settings
from django_jinja import library

from taiga import domains

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
