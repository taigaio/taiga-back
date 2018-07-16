# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

import datetime as dt

from django_jinja import library
from django_sites import get_by_id as get_site_by_id

from taiga.front.urls import urls


@library.global_function(name="resolve_front_url")
def resolve(type, *args):
    site = get_site_by_id("front")
    url_tmpl = "{scheme}//{domain}{url}"

    scheme = site.scheme and "{0}:".format(site.scheme) or ""
    url = urls[type].format(*args)
    return url_tmpl.format(scheme=scheme, domain=site.domain, url=url)


@library.filter(name="parse_and_format_date")
def parse_and_format_date(value, *args):
    date_value = dt.datetime.strptime(value, '%Y-%m-%d')
    return date_value.strftime('%d %b %Y')
