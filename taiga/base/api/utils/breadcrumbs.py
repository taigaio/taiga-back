# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from django.core.urlresolvers import resolve, get_script_prefix


def get_breadcrumbs(url):
    """
    Given a url returns a list of breadcrumbs, which are each a
    tuple of (name, url).
    """

    from taiga.base.api.settings import api_settings
    from taiga.base.api.views import APIView

    view_name_func = api_settings.VIEW_NAME_FUNCTION

    def breadcrumbs_recursive(url, breadcrumbs_list, prefix, seen):
        """
        Add tuples of (name, url) to the breadcrumbs list,
        progressively chomping off parts of the url.
        """

        try:
            (view, unused_args, unused_kwargs) = resolve(url)
        except Exception:
            pass
        else:
            # Check if this is a REST framework view,
            # and if so add it to the breadcrumbs
            cls = getattr(view, "cls", None)
            if cls is not None and issubclass(cls, APIView):
                # Don't list the same view twice in a row.
                # Probably an optional trailing slash.
                if not seen or seen[-1] != view:
                    suffix = getattr(view, "suffix", None)
                    name = view_name_func(cls, suffix)
                    breadcrumbs_list.insert(0, (name, prefix + url))
                    seen.append(view)

        if url == "":
            # All done
            return breadcrumbs_list

        elif url.endswith("/"):
            # Drop trailing slash off the end and continue to try to
            # resolve more breadcrumbs
            url = url.rstrip("/")
            return breadcrumbs_recursive(url, breadcrumbs_list, prefix, seen)

        # Drop trailing non-slash off the end and continue to try to
        # resolve more breadcrumbs
        url = url[:url.rfind("/") + 1]
        return breadcrumbs_recursive(url, breadcrumbs_list, prefix, seen)

    prefix = get_script_prefix().rstrip("/")
    url = url[len(prefix):]
    return breadcrumbs_recursive(url, [], prefix, [])
