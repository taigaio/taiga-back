# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.conf import settings

from taiga.base import routers

from . import api


router = routers.DefaultRouter(trailing_slash=False)

if settings.STATS_ENABLED:
    router.register(r"stats/system", api.SystemStatsViewSet, base_name="system-stats")

router.register(r"stats/discover", api.DiscoverStatsViewSet, base_name="discover-stats")
