# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db import transaction as tx
from django.utils.translation import gettext as _

from taiga.base import exceptions as exc
from taiga.base.api.utils import get_object_or_404
from taiga.base import response
from taiga.projects.services.bulk_update_order import update_order_and_swimlane


#############################################
# ViewSets
#############################################

class MoveOnDestroyMixin:
    move_on_destroy_post_destroy_signal = None

    def move_on_destroy_reorder_after_moved(self, moved_to_obj, moved_objs_queryset):
        pass

    @tx.atomic
    def destroy(self, request, *args, **kwargs):
        # moveTo is needed
        move_to = self.request.QUERY_PARAMS.get('moveTo', None)
        if move_to is None:
            raise exc.BadRequest(_("Query param 'moveTo' is required"))

        # check permisions over moveTo object
        move_item = get_object_or_404(self.model, id=move_to)
        self.check_permissions(request, 'update', move_item)

        obj = self.get_object_or_none()

        qs = self.move_on_destroy_related_class.objects.filter(**{self.move_on_destroy_related_field: obj})
        # Reorder after moved
        self.move_on_destroy_reorder_after_moved(move_item, qs)
        # move related objects to the new one.
        # (we need to do this befero to prevent some deletes-on-cascade behaivors)
        qs.update(**{self.move_on_destroy_related_field: move_item})

        # change default project value if is needed
        if getattr(obj.project, self.move_on_destroy_project_default_field) == obj:
            setattr(obj.project, self.move_on_destroy_project_default_field, move_item)
            obj.project.save()
            changed_default_value = True

        # destroy object
        res = super().destroy(request, *args, **kwargs)

        # if the object is not deleted
        if not isinstance(res, response.NoContent):
            # Restart status (roolback) if we can't delete the object
            qs.update(**{self.move_on_destroy_related_field: obj})

            # Restart default value
            if changed_default_value:
                setattr(obj.project, self.move_on_destroy_project_default_field, obj)
                obj.project.save()
        else:
            if self.move_on_destroy_post_destroy_signal:
                # throw  post delete signal
                self.move_on_destroy_post_destroy_signal.send(obj.__class__, deleted=obj, moved=move_item)

        return res


class MoveOnDestroySwimlaneMixin:
    @tx.atomic
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object_or_none()
        self.check_permissions(request, 'destroy', obj)

        move_to = self.request.QUERY_PARAMS.get('moveTo', None)
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

            # check permisions over moveTo object
            self.check_permissions(request, 'destroy', move_item)

            update_order_and_swimlane(obj, move_item)

        return super().destroy(request, *args, **kwargs)
