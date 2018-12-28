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

from taiga.base.api.permissions import (TaigaResourcePermission, HasProjectPerm,
                                        IsAuthenticated, IsProjectAdmin, AllowAny,
                                        IsSuperUser)


class MilestonePermission(TaigaResourcePermission):
    enought_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_milestones')
    create_perms = HasProjectPerm('add_milestone')
    update_perms = HasProjectPerm('modify_milestone')
    partial_update_perms = HasProjectPerm('modify_milestone')
    destroy_perms = HasProjectPerm('delete_milestone')
    list_perms = AllowAny()
    stats_perms = HasProjectPerm('view_milestones')
    watch_perms = IsAuthenticated() & HasProjectPerm('view_milestones')
    unwatch_perms = IsAuthenticated() & HasProjectPerm('view_milestones')
    move_related_items_perms = HasProjectPerm('modify_milestone')
    move_uss_to_sprint_perms = HasProjectPerm('modify_us')
    move_tasks_to_sprint_perms = HasProjectPerm('modify_task')
    move_issues_to_sprint_perms = HasProjectPerm('modify_issue')


class MilestoneWatchersPermission(TaigaResourcePermission):
    enought_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_milestones')
    list_perms = HasProjectPerm('view_milestones')
