# -*- coding: utf-8 -*-
from taiga.base.api.permissions import TaigaResourcePermission, AllowAny, IsSuperUser
from taiga.permissions.permissions import HasProjectPerm, IsProjectAdmin


class UserTimelinePermission(TaigaResourcePermission):
    enough_perms = IsSuperUser()
    global_perms = None
    retrieve_perms = AllowAny()


class ProjectTimelinePermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_project')
