# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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
                                        IsAuthenticated, IsProjectOwner, AllowAny,
                                        IsSuperUser)


class MilestonePermission(TaigaResourcePermission):
    enought_perms = IsProjectOwner() | IsSuperUser()
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

class MilestoneWatchersPermission(TaigaResourcePermission):
    enought_perms = IsProjectOwner() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_milestones')
    list_perms = HasProjectPerm('view_milestones')
