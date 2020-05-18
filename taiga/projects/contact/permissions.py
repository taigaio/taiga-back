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

from taiga.base.api.permissions import PermissionComponent
from taiga.base.api.permissions import TaigaResourcePermission


class IsContactActivated(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        if not request.user.is_authenticated or not obj.project.is_contact_activated:
            return False

        if obj.project.is_private:
            return obj.project.cached_memberships_for_user(request.user)

        return True


class ContactPermission(TaigaResourcePermission):
    create_perms = IsContactActivated()
