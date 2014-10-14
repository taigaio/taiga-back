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

from django_jinja import library
from django_sites import get_by_id as get_site_by_id


urls = {
    "home": "/",

    "login": "/login",
    "change-password": "/change-password/{0}",
    "change-email": "/change-email/{0}",
    "cancel-account": "/cancel-account/{0}",
    "invitation": "/invitation/{0}",

    "project": "/project/{0}",

    "backlog": "/project/{0}/backlog/",
    "taskboard": "/project/{0}/taskboard/{1}",
    "kanban": "/project/{0}/kanban/",
    "userstory": "/project/{0}/us/{1}",
    "task": "/project/{0}/task/{1}",

    "issues": "/project/{0}/issues",
    "issue": "/project/{0}/issue/{1}",

    "wiki": "/project/{0}/wiki/{1}",

    "project-admin": "/project/{0}/admin/project-profile/details",
}


@library.global_function(name="resolve_front_url")
def resolve(type, *args):
    site = get_site_by_id("front")
    url_tmpl = "{scheme}//{domain}{url}"

    scheme = site.scheme and "{0}:".format(site.scheme) or ""
    url = urls[type].format(*args)
    return url_tmpl.format(scheme=scheme, domain=site.domain, url=url)
