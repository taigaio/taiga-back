# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api.permissions import TaigaResourcePermission, IsAuthenticated


class ImporterPermission(TaigaResourcePermission):
    enough_perms = IsAuthenticated()
    global_perms = None
    auth_url_perms = IsAuthenticated()
    authorize_perms = IsAuthenticated()
    list_users_perms = IsAuthenticated()
    list_projects_perms = IsAuthenticated()
    import_project_perms = IsAuthenticated()
