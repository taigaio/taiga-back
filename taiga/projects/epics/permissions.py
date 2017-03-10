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

from taiga.base.api.permissions import TaigaResourcePermission, AllowAny, IsAuthenticated
from taiga.base.api.permissions import IsSuperUser, HasProjectPerm, IsProjectAdmin

from taiga.permissions.permissions import CommentAndOrUpdatePerm


class EpicPermission(TaigaResourcePermission):
    enought_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_epics')
    create_perms = HasProjectPerm('add_epic')
    update_perms = CommentAndOrUpdatePerm('modify_epic', 'comment_epic')
    partial_update_perms = CommentAndOrUpdatePerm('modify_epic', 'comment_epic')
    destroy_perms = HasProjectPerm('delete_epic')
    list_perms = AllowAny()
    filters_data_perms = AllowAny()
    csv_perms = AllowAny()
    bulk_create_perms = HasProjectPerm('add_epic')
    upvote_perms = IsAuthenticated() & HasProjectPerm('view_epics')
    downvote_perms = IsAuthenticated() & HasProjectPerm('view_epics')
    watch_perms = IsAuthenticated() & HasProjectPerm('view_epics')
    unwatch_perms = IsAuthenticated() & HasProjectPerm('view_epics')


class EpicRelatedUserStoryPermission(TaigaResourcePermission):
    enought_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_epics')
    create_perms = HasProjectPerm('modify_epic')
    update_perms = HasProjectPerm('modify_epic')
    partial_update_perms = HasProjectPerm('modify_epic')
    destroy_perms = HasProjectPerm('modify_epic')
    list_perms = AllowAny()
    bulk_create_perms = HasProjectPerm('modify_epic')


class EpicVotersPermission(TaigaResourcePermission):
    enought_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_epics')
    list_perms = HasProjectPerm('view_epics')


class EpicWatchersPermission(TaigaResourcePermission):
    enought_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_epics')
    list_perms = HasProjectPerm('view_epics')
