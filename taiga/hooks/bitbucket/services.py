# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import uuid

from django.contrib.auth import get_user_model
from django.urls import reverse
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
