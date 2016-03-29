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

import uuid

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.conf import settings

from taiga.base.utils.urls import get_absolute_url


# Set this in settings.PROJECT_MODULES_CONFIGURATORS["bitbucket"]
def get_or_generate_config(project):
    config = project.modules_config.config
    if config and "bitbucket" in config:
        g_config = project.modules_config.config["bitbucket"]
    else:
        g_config = {
            "secret": uuid.uuid4().hex,
            "valid_origin_ips": settings.BITBUCKET_VALID_ORIGIN_IPS,
        }

    url = reverse("bitbucket-hook-list")
    url = get_absolute_url(url)
    url = "%s?project=%s&key=%s" % (url, project.id, g_config["secret"])
    g_config["webhooks_url"] = url
    return g_config


def get_bitbucket_user(user_id):
    return get_user_model().objects.get(is_system=True, username__startswith="bitbucket")
