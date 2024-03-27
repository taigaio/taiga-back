# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api.permissions import TaigaResourcePermission, AllowAny, IsAuthenticated
from taiga.base.api.permissions import IsSuperUser, HasProjectPerm, IsProjectAdmin

from taiga.permissions.permissions import CommentAndOrUpdatePerm


class EpicPermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
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
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_epics')
    create_perms = HasProjectPerm('modify_epic')
    update_perms = HasProjectPerm('modify_epic')
    partial_update_perms = HasProjectPerm('modify_epic')
    destroy_perms = HasProjectPerm('modify_epic')
    list_perms = AllowAny()
    bulk_create_perms = HasProjectPerm('modify_epic')


class EpicVotersPermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_epics')
    list_perms = HasProjectPerm('view_epics')


class EpicWatchersPermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_epics')
    list_perms = HasProjectPerm('view_epics')
