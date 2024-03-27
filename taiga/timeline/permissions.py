# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
