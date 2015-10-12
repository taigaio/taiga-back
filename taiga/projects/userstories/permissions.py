# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
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
                                        IsAuthenticated, IsProjectOwner,
                                        AllowAny, IsSuperUser)


class UserStoryPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_us')
    create_perms = HasProjectPerm('add_us_to_project') | HasProjectPerm('add_us')
    update_perms = HasProjectPerm('modify_us')
    partial_update_perms = HasProjectPerm('modify_us')
    destroy_perms = HasProjectPerm('delete_us')
    list_perms = AllowAny()
    filters_data_perms = AllowAny()
    csv_perms = AllowAny()
    bulk_create_perms = IsAuthenticated() & (HasProjectPerm('add_us_to_project') | HasProjectPerm('add_us'))
    bulk_update_order_perms = HasProjectPerm('modify_us')
    upvote_perms = IsAuthenticated() & HasProjectPerm('view_us')
    downvote_perms = IsAuthenticated() & HasProjectPerm('view_us')
    watch_perms = IsAuthenticated() & HasProjectPerm('view_us')
    unwatch_perms = IsAuthenticated() & HasProjectPerm('view_us')


class UserStoryVotersPermission(TaigaResourcePermission):
    enought_perms = IsProjectOwner() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_us')
    list_perms = HasProjectPerm('view_us')


class UserStoryWatchersPermission(TaigaResourcePermission):
    enought_perms = IsProjectOwner() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_us')
    list_perms = HasProjectPerm('view_us')
