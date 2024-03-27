# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.translation import gettext as _

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

    - bulk_update_param: the name of the field of the data received from
      the client that contains the pairs (id, order) to sort the objects.
    - bulk_update_perm: the codename of the permission needed to sort.
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
        if project.blocked_code is not None:
            raise exc.Blocked(_("Blocked element"))

        self.__class__.bulk_update_order_action(project, request.user, bulk_data)
        return response.NoContent(data=None)
