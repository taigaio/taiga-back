# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
