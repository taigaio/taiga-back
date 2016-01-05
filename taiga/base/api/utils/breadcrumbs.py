# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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

# This code is partially taken from django-rest-framework:
# Copyright (c) 2011-2014, Tom Christie

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
