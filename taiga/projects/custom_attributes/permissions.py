# Copyright (C) 2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2015 David Barragán <bameda@dbarragan.com>
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

from taiga.base.api.permissions import TaigaResourcePermission
from taiga.base.api.permissions import HasProjectPerm
from taiga.base.api.permissions import IsProjectOwner
from taiga.base.api.permissions import AllowAny
from taiga.base.api.permissions import IsSuperUser


######################################################
# Custom Attribute Permissions
#######################################################

class UserStoryCustomAttributePermission(TaigaResourcePermission):
    enought_perms = IsProjectOwner() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    partial_update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectOwner()


class TaskCustomAttributePermission(TaigaResourcePermission):
    enought_perms = IsProjectOwner() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    partial_update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectOwner()


class IssueCustomAttributePermission(TaigaResourcePermission):
    enought_perms = IsProjectOwner() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    partial_update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectOwner()


######################################################
# Custom Attributes Values Permissions
#######################################################

class UserStoryCustomAttributesValuesPermission(TaigaResourcePermission):
    enought_perms = IsProjectOwner() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_us')
    update_perms = HasProjectPerm('modify_us')
    partial_update_perms = HasProjectPerm('modify_us')


class TaskCustomAttributesValuesPermission(TaigaResourcePermission):
    enought_perms = IsProjectOwner() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_tasks')
    update_perms = HasProjectPerm('modify_task')
    partial_update_perms = HasProjectPerm('modify_task')


class IssueCustomAttributesValuesPermission(TaigaResourcePermission):
    enought_perms = IsProjectOwner() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_issues')
    update_perms = HasProjectPerm('modify_issue')
    partial_update_perms = HasProjectPerm('modify_issue')
