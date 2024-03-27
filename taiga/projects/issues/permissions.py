# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

#
from taiga.base.api.permissions import TaigaResourcePermission, AllowAny, IsAuthenticated, IsSuperUser
from taiga.permissions.permissions import HasProjectPerm, IsProjectAdmin

from taiga.permissions.permissions import CommentAndOrUpdatePerm


class IssuePermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_issues')
    create_perms = HasProjectPerm('add_issue')
    update_perms = CommentAndOrUpdatePerm('modify_issue', 'comment_issue')
    partial_update_perms = CommentAndOrUpdatePerm('modify_issue', 'comment_issue')
    destroy_perms = HasProjectPerm('delete_issue')
    list_perms = AllowAny()
    filters_data_perms = AllowAny()
    csv_perms = AllowAny()
    bulk_create_perms = HasProjectPerm('add_issue')
    bulk_update_milestone_perms = HasProjectPerm('modify_issue')
    delete_comment_perms= HasProjectPerm('modify_issue')
    upvote_perms = IsAuthenticated() & HasProjectPerm('view_issues')
    downvote_perms = IsAuthenticated() & HasProjectPerm('view_issues')
    watch_perms = IsAuthenticated() & HasProjectPerm('view_issues')
    unwatch_perms = IsAuthenticated() & HasProjectPerm('view_issues')
    promote_to_us_perms = IsAuthenticated() & HasProjectPerm('add_us')


class IssueVotersPermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_issues')
    list_perms = HasProjectPerm('view_issues')


class IssueWatchersPermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_issues')
    list_perms = HasProjectPerm('view_issues')
