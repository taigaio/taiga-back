# -*- coding: utf-8 -*-
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
        if self.request.user.is_anonymous():
            return self.model.objects.none()
        return self.request.user.storage_entries.all()

    def pre_save(self, obj):
        if self.request.user.is_authenticated():
            obj.owner = self.request.user

    def create(self, *args, **kwargs):
        key = self.request.DATA.get("key", None)
        if (key and self.request.user.is_authenticated() and
                self.request.user.storage_entries.filter(key=key).exists()):
            raise exc.BadRequest(
                _("Duplicate key value violates unique constraint. "
                  "Key '{}' already exists.").format(key)
            )
        return super().create(*args, **kwargs)
