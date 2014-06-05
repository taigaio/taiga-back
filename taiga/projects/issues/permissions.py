# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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


from taiga.base.api.permissions import (ResourcePermission, HasProjectPerm,
                                        IsProjectOwner, PermissionComponent,
                                        AllowAny, IsAuthenticated)


class IssuePermission(ResourcePermission):
    enought_perms = IsProjectOwner()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_issues')
    create_perms = HasProjectPerm('add_issue')
    update_perms = HasProjectPerm('modify_issue')
    destroy_perms = HasProjectPerm('delete_issue')
    list_perms = AllowAny()
    upvote_perms = IsAuthenticated() & HasProjectPerm('vote_issues')
    downvote_perms = IsAuthenticated() & HasProjectPerm('vote_issues')


class HasIssueIdUrlParam(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        param = view.kwargs.get('issue_id', None)
        if param:
            return True
        return False


class IssueVotersPermission(ResourcePermission):
    enought_perms = IsProjectOwner()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_issues')
    create_perms = HasProjectPerm('add_issue')
    update_perms = HasProjectPerm('modify_issue')
    destroy_perms = HasProjectPerm('delete_issue')
    list_perms = HasProjectPerm('view_issues')
