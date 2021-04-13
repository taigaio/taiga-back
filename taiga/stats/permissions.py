# -*- coding: utf-8 -*-
from taiga.base.api import permissions


class SystemStatsPermission(permissions.TaigaResourcePermission):
    global_perms = permissions.AllowAny()


class DiscoverStatsPermission(permissions.TaigaResourcePermission):
    global_perms = permissions.AllowAny()
