# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
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

import hashlib
import copy

from urllib.parse import urlencode

from django.conf import settings
from django.templatetags.static import static

GRAVATAR_BASE_URL = "//www.gravatar.com/avatar/{}?{}"


def get_gravatar_url(email: str, **options) -> str:
    """Get the gravatar url associated to an email.

    :param options: Additional options to gravatar.
    - `default` defines what image url to show if no gravatar exists
    - `size` defines the size of the avatar.

    :return: Gravatar url.
    """

    params = copy.copy(options)

    default_avatar = getattr(settings, "GRAVATAR_DEFAULT_AVATAR", None)
    default_size = getattr(settings, "GRAVATAR_AVATAR_SIZE", None)

    avatar = options.get("default", None)
    size = options.get("size", None)

    if avatar:
        params["default"] = avatar
    elif default_avatar:
        params["default"] = static(default_avatar)

    if size:
        params["size"] = size
    elif default_size:
        params["size"] = default_size

    email_hash = hashlib.md5(email.lower().encode()).hexdigest()
    url = GRAVATAR_BASE_URL.format(email_hash, urlencode(params))

    return url
