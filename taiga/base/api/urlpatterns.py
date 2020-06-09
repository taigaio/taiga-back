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

# The code is partially taken (and modified) from django rest framework
# that is licensed under the following terms:
#
# Copyright (c) 2011-2014, Tom Christie
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
# Redistributions in binary form must reproduce the above copyright notice, this
# list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


from django.urls import URLResolver
from django.conf.urls import url, include

from .settings import api_settings


def apply_suffix_patterns(urlpatterns, suffix_pattern, suffix_required):
    ret = []
    for urlpattern in urlpatterns:
        if isinstance(urlpattern, URLResolver):
            # Set of included URL patterns
            regex = urlpattern.pattern.regex.pattern
            namespace = urlpattern.namespace
            app_name = urlpattern.app_name
            kwargs = urlpattern.default_kwargs
            # Add in the included patterns, after applying the suffixes
            patterns = apply_suffix_patterns(urlpattern.url_patterns,
                                             suffix_pattern,
                                             suffix_required)
            ret.append(url(regex, include(patterns, namespace, app_name), kwargs))

        else:
            # Regular URL pattern
            regex = urlpattern.pattern.regex.pattern.rstrip("$") + suffix_pattern
            view = urlpattern.callback
            kwargs = urlpattern.default_args
            name = urlpattern.name
            # Add in both the existing and the new urlpattern
            if not suffix_required:
                ret.append(urlpattern)
            ret.append(url(regex, view, kwargs, name))

    return ret


def format_suffix_patterns(urlpatterns, suffix_required=False, allowed=None):
    """
    Supplement existing urlpatterns with corresponding patterns that also
    include a ".format" suffix.  Retains urlpattern ordering.

    urlpatterns:
        A list of URL patterns.

    suffix_required:
        If `True`, only suffixed URLs will be generated, and non-suffixed
        URLs will not be used.  Defaults to `False`.

    allowed:
        An optional tuple/list of allowed suffixes.  eg ["json", "api"]
        Defaults to `None`, which allows any suffix.
    """
    suffix_kwarg = api_settings.FORMAT_SUFFIX_KWARG
    if allowed:
        if len(allowed) == 1:
            allowed_pattern = allowed[0]
        else:
            allowed_pattern = "(%s)" % "|".join(allowed)
        suffix_pattern = r"\.(?P<%s>%s)$" % (suffix_kwarg, allowed_pattern)
    else:
        suffix_pattern = r"\.(?P<%s>[a-z0-9]+)$" % suffix_kwarg

    return apply_suffix_patterns(urlpatterns, suffix_pattern, suffix_required)
