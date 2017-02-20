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

from taiga.base import status
from taiga.base.api.mixins import CreateModelMixin, BlockedByProjectMixin
from taiga.base.api.viewsets import GenericViewSet

from . import models
from . import permissions
from . import services
from . import validators

from django.conf import settings


class ContactViewSet(BlockedByProjectMixin, CreateModelMixin, GenericViewSet):
    permission_classes = (permissions.ContactPermission,)
    validator_class = validators.ContactEntryValidator
    model = models.ContactEntry

    def create(self, *args, **kwargs):
        response = super().create(*args, **kwargs)

        if response.status_code == status.HTTP_201_CREATED:
            if settings.CELERY_ENABLED:
                services.send_contact_email.delay(self.object.id)
            else:
                services.send_contact_email(self.object.id)

        return response

    def pre_save(self, obj):
        obj.user = self.request.user
        super().pre_save(obj)
