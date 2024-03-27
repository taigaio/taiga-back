# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
