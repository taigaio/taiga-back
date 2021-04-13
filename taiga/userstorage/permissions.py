# -*- coding: utf-8 -*-
from taiga.base.api.permissions import TaigaResourcePermission, IsAuthenticated, DenyAll


class StorageEntriesPermission(TaigaResourcePermission):
    enough_perms = IsAuthenticated()
    global_perms = DenyAll()
