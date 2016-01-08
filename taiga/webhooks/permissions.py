# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from taiga.base.api.permissions import (TaigaResourcePermission, IsProjectOwner,
                                        AllowAny, PermissionComponent)

from taiga.permissions.service import is_project_owner


class IsWebhookProjectOwner(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        return is_project_owner(request.user, obj.webhook.project)


class WebhookPermission(TaigaResourcePermission):
    retrieve_perms = IsProjectOwner()
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    partial_update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    test_perms = IsProjectOwner()


class WebhookLogPermission(TaigaResourcePermission):
    retrieve_perms = IsWebhookProjectOwner()
    list_perms = AllowAny()
    resend_perms = IsWebhookProjectOwner()
