# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.translation import gettext as _

from taiga.base.api import ModelCrudViewSet
from taiga.base import exceptions as exc

from . import models
from . import filters
from . import serializers
from . import validators
from . import permissions


class StorageEntriesViewSet(ModelCrudViewSet):
    model = models.StorageEntry
    filter_backends = (filters.StorageEntriesFilterBackend,)
    serializer_class = serializers.StorageEntrySerializer
    validator_class = validators.StorageEntryValidator
    permission_classes = [permissions.StorageEntriesPermission]
    lookup_field = "key"

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return self.model.objects.none()
        return self.request.user.storage_entries.all()

    def pre_save(self, obj):
        if self.request.user.is_authenticated:
            obj.owner = self.request.user

    def create(self, *args, **kwargs):
        key = self.request.DATA.get("key", None)
        if (key and self.request.user.is_authenticated and
                self.request.user.storage_entries.filter(key=key).exists()):
            raise exc.BadRequest(
                _("Duplicate key value violates unique constraint. "
                  "Key '{}' already exists.").format(key)
            )
        return super().create(*args, **kwargs)
