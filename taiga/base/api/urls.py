# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
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

"""
Login and logout views for the browsable API.

Add these to your root URLconf if you're using the browsable API and
your API requires authentication.

The urls must be namespaced as 'api', and you should make sure
your authentication settings include `SessionAuthentication`.

    urlpatterns = patterns('',
        ...
        url(r'^auth', include('taiga.base.api.urls', namespace='api'))
    )
"""
from django.conf.urls import patterns
from django.conf.urls import url


template_name = {"template_name": "api/login.html"}

urlpatterns = patterns("django.contrib.auth.views",
    url(r"^login/$", "login", template_name, name="login"),
    url(r"^logout/$", "logout", template_name, name="logout"),
)
