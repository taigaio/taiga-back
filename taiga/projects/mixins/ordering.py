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


from django.utils.translation import ugettext as _

from taiga.base import response
from taiga.base import exceptions as exc
from taiga.base.api.utils import get_object_or_404
from taiga.base.decorators import list_route

from taiga.projects.models import Project


#############################################
# ViewSets
#############################################

class BulkUpdateOrderMixin:
    """
    This mixin need three fields in the child class:

    - bulk_update_param: that the name of the field of the data received from
      the cliente that contains the pairs (id, order) to sort the objects.
    - bulk_update_perm: that containts the codename of the permission needed to sort.
    - bulk_update_order: method with bulk update order logic
    """

    @list_route(methods=["POST"])
    def bulk_update_order(self, request, **kwargs):
        bulk_data = request.DATA.get(self.bulk_update_param, None)

        if bulk_data is None:
            raise exc.BadRequest(_("'{param}' parameter is mandatory".format(param=self.bulk_update_param)))

        project_id = request.DATA.get('project', None)
        if project_id is None:
            raise exc.BadRequest(_("'project' parameter is mandatory"))

        project = get_object_or_404(Project, id=project_id)

        self.check_permissions(request, 'bulk_update_order', project)

        self.__class__.bulk_update_order_action(project, request.user, bulk_data)
        return response.NoContent(data=None)
