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

from django.apps import apps
from django.db.models import Q

from taiga.base.filters import PermissionBasedFilterBackend

class ContactsFilterBackend(PermissionBasedFilterBackend):
    permission = "view_project"

    def filter_queryset(self, user, request, queryset, view):
        qs = queryset.filter(is_active=True)
        Membership = apps.get_model('projects', 'Membership')
        memberships_qs = Membership.objects.filter(user=user)

        # Authenticated
        if request.user.is_authenticated():
            # if super user we don't need to filter anything
            if not request.user.is_superuser:
                memberships_qs = memberships_qs.filter(Q(role__permissions__contains=[self.permission]) |
                                                       Q(is_owner=True))

        # Anonymous
        else:
            memberships_qs = memberships_qs.filter(project__anon_permissions__contains=[self.permission])

        projects_list = [membership.project_id for membership in memberships_qs]
        qs = qs.filter(memberships__project_id__in=projects_list)
        qs = qs.exclude(id=user.id)
        return qs.distinct()
