# Copyright (C) 2014-2019 Taiga Agile LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from taiga.base.api.permissions import TaigaResourcePermission, AllowAny, IsAuthenticated, IsSuperUser
from taiga.permissions.permissions import HasProjectPerm, IsProjectAdmin

from taiga.permissions.permissions import CommentAndOrUpdatePerm


class IssuePermission(TaigaResourcePermission):
    enought_perms = IsProjectAdmin() | IsSuperUser()
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
    enought_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_issues')
    list_perms = HasProjectPerm('view_issues')


class IssueWatchersPermission(TaigaResourcePermission):
    enought_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_issues')
    list_perms = HasProjectPerm('view_issues')
