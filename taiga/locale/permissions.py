# -*- coding: utf-8 -*-
from taiga.base.api.permissions import TaigaResourcePermission, AllowAny


class LocalesPermission(TaigaResourcePermission):
    global_perms = AllowAny()
