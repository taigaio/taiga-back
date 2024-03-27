# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api.permissions import TaigaResourcePermission, AllowAny, IsAuthenticated, IsSuperUser
from taiga.permissions.permissions import HasProjectPerm, IsProjectAdmin

from taiga.permissions.permissions import CommentAndOrUpdatePerm


class TaskPermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_tasks')
    create_perms = HasProjectPerm('add_task')
    update_perms = CommentAndOrUpdatePerm('modify_task', 'comment_task')
    partial_update_perms = CommentAndOrUpdatePerm('modify_task', 'comment_task')
    destroy_perms = HasProjectPerm('delete_task')
    list_perms = AllowAny()
    filters_data_perms = AllowAny()
    csv_perms = AllowAny()
    bulk_create_perms = HasProjectPerm('add_task')
    bulk_update_order_perms = HasProjectPerm('modify_task')
    bulk_update_milestone_perms = HasProjectPerm('modify_task')
    upvote_perms = IsAuthenticated() & HasProjectPerm('view_tasks')
    downvote_perms = IsAuthenticated() & HasProjectPerm('view_tasks')
    watch_perms = IsAuthenticated() & HasProjectPerm('view_tasks')
    unwatch_perms = IsAuthenticated() & HasProjectPerm('view_tasks')
    promote_to_us_perms = IsAuthenticated() & HasProjectPerm('view_tasks')


class TaskVotersPermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_tasks')
    list_perms = HasProjectPerm('view_tasks')


class TaskWatchersPermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_tasks')
    list_perms = HasProjectPerm('view_tasks')
