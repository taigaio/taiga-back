# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api.permissions import TaigaResourcePermission
from taiga.base.api.permissions import HasProjectPerm
from taiga.base.api.permissions import IsProjectAdmin
from taiga.base.api.permissions import AllowAny
from taiga.base.api.permissions import IsSuperUser


######################################################
# Custom Attribute Permissions
#######################################################

class EpicCustomAttributePermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectAdmin()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectAdmin()


class UserStoryCustomAttributePermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectAdmin()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectAdmin()


class TaskCustomAttributePermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectAdmin()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectAdmin()


class IssueCustomAttributePermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectAdmin()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectAdmin()


######################################################
# Custom Attributes Values Permissions
#######################################################

class EpicCustomAttributesValuesPermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_us')
    update_perms = HasProjectPerm('modify_us')
    partial_update_perms = HasProjectPerm('modify_us')


class UserStoryCustomAttributesValuesPermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_us')
    update_perms = HasProjectPerm('modify_us')
    partial_update_perms = HasProjectPerm('modify_us')


class TaskCustomAttributesValuesPermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_tasks')
    update_perms = HasProjectPerm('modify_task')
    partial_update_perms = HasProjectPerm('modify_task')


class IssueCustomAttributesValuesPermission(TaigaResourcePermission):
    enough_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_issues')
    update_perms = HasProjectPerm('modify_issue')
    partial_update_perms = HasProjectPerm('modify_issue')
