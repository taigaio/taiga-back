# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from taiga.base.api.permissions import TaigaResourcePermission, AllowAny, IsAuthenticated, IsSuperUser
from taiga.permissions.permissions import HasProjectPerm, IsProjectAdmin

from taiga.permissions.permissions import CommentAndOrUpdatePerm


class TaskPermission(TaigaResourcePermission):
    enought_perms = IsProjectAdmin() | IsSuperUser()
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
    enought_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_tasks')
    list_perms = HasProjectPerm('view_tasks')


class TaskWatchersPermission(TaigaResourcePermission):
    enought_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_tasks')
    list_perms = HasProjectPerm('view_tasks')
