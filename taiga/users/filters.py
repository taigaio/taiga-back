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

from django.apps import apps

from taiga.base.filters import PermissionBasedFilterBackend
from . import services

class ContactsFilterBackend(PermissionBasedFilterBackend):
    def filter_queryset(self, user, request, queryset, view):
        qs = queryset.filter(is_active=True)
        project_ids = services.get_visible_project_ids(user, request.user)
        qs = qs.filter(memberships__project_id__in=project_ids)
        qs = qs.exclude(id=user.id)
        return qs.distinct()
