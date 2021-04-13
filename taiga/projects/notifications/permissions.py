# -*- coding: utf-8 -*-
from taiga.base.api.permissions import (TaigaResourcePermission, IsAuthenticated)


class NotifyPolicyPermission(TaigaResourcePermission):
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsAuthenticated()
