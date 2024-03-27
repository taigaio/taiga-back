# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api.permissions import (TaigaResourcePermission, HasProjectPerm,
                                        IsAuthenticated, IsProjectAdmin, AllowAny,
                                        IsSuperUser)


class MilestonePermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_milestones')
    create_perms = HasProjectPerm('add_milestone')
    update_perms = HasProjectPerm('modify_milestone')
    partial_update_perms = HasProjectPerm('modify_milestone')
    destroy_perms = HasProjectPerm('delete_milestone')
    list_perms = AllowAny()
    stats_perms = HasProjectPerm('view_milestones')
    watch_perms = IsAuthenticated() & HasProjectPerm('view_milestones')
    unwatch_perms = IsAuthenticated() & HasProjectPerm('view_milestones')
    move_related_items_perms = HasProjectPerm('modify_milestone')
    move_uss_to_sprint_perms = HasProjectPerm('modify_us')
    move_tasks_to_sprint_perms = HasProjectPerm('modify_task')
    move_issues_to_sprint_perms = HasProjectPerm('modify_issue')


class MilestoneWatchersPermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_milestones')
    list_perms = HasProjectPerm('view_milestones')
