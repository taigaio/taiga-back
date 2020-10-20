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


from django.db import transaction as tx
from django.utils.translation import ugettext as _

from taiga.base import exceptions as exc
from taiga.base.api.utils import get_object_or_404
from taiga.projects.services.bulk_update_order import update_order_and_swimlane


#############################################
# ViewSets
#############################################

class MoveOnDestroyMixin:
    @tx.atomic
    def destroy(self, request, *args, **kwargs):
        move_to = self.request.QUERY_PARAMS.get('moveTo', None)
        if move_to is None:
            return super().destroy(request, *args, **kwargs)

        obj = self.get_object_or_none()
        move_item = get_object_or_404(self.model, id=move_to)

        self.check_permissions(request, 'destroy', obj)

        qs = self.move_on_destroy_related_class.objects.filter(**{self.move_on_destroy_related_field: obj})
        qs.update(**{self.move_on_destroy_related_field: move_item})

        if getattr(obj.project, self.move_on_destroy_project_default_field) == obj:
            setattr(obj.project, self.move_on_destroy_project_default_field, move_item)
            obj.project.save()

        return super().destroy(request, *args, **kwargs)


class MoveOnDestroySwimlaneMixin:
    @tx.atomic
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object_or_none()
        self.check_permissions(request, 'destroy', obj)

        move_to = self.request.DATA.get('moveTo', None)
        if move_to is None:
            total_elements = obj.project.swimlanes.count()
            # you cannot set swimlane=None if there are more swimlanes available
            if total_elements > 1:
                raise exc.BadRequest(_("Cannot set swimlane to None if there are available swimlanes"))

            # but if it was the last swimlane,
            # it can be deleted and all uss have now swimlane=None
            obj.user_stories.update(swimlane_id=None)
        else:
            move_item = get_object_or_404(self.model, id=move_to)
            update_order_and_swimlane(obj, move_item)

        return super().destroy(request, *args, **kwargs)
