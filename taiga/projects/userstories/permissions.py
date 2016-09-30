# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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


class UserStoryPermission(TaigaResourcePermission):
    enought_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_us')
    by_ref_perms = HasProjectPerm('view_us')
    create_perms = HasProjectPerm('add_us_to_project') | HasProjectPerm('add_us')
    update_perms = CommentAndOrUpdatePerm('modify_us', 'comment_us')
    partial_update_perms = CommentAndOrUpdatePerm('modify_us', 'comment_us')
    destroy_perms = HasProjectPerm('delete_us')
    list_perms = AllowAny()
    filters_data_perms = AllowAny()
    csv_perms = AllowAny()
    bulk_create_perms = IsAuthenticated() & (HasProjectPerm('add_us_to_project') | HasProjectPerm('add_us'))
    bulk_update_order_perms = HasProjectPerm('modify_us')
    bulk_update_milestone_perms = HasProjectPerm('modify_us')
    upvote_perms = IsAuthenticated() & HasProjectPerm('view_us')
    downvote_perms = IsAuthenticated() & HasProjectPerm('view_us')
    watch_perms = IsAuthenticated() & HasProjectPerm('view_us')
    unwatch_perms = IsAuthenticated() & HasProjectPerm('view_us')


class UserStoryVotersPermission(TaigaResourcePermission):
    enought_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_us')
    list_perms = HasProjectPerm('view_us')


class UserStoryWatchersPermission(TaigaResourcePermission):
    enought_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_us')
    list_perms = HasProjectPerm('view_us')
