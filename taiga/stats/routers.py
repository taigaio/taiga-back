# -*- coding: utf-8 -*-
from django.conf import settings

from taiga.base import routers

from . import api


router = routers.DefaultRouter(trailing_slash=False)

if settings.STATS_ENABLED:
    router.register(r"stats/system", api.SystemStatsViewSet, base_name="system-stats")

router.register(r"stats/discover", api.DiscoverStatsViewSet, base_name="discover-stats")
