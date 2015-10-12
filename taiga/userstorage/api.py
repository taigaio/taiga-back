# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
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
from django.db import IntegrityError

from taiga.base.api import ModelCrudViewSet
from taiga.base import exceptions as exc

from . import models
from . import filters
from . import serializers
from . import permissions


class StorageEntriesViewSet(ModelCrudViewSet):
    model = models.StorageEntry
    filter_backends = (filters.StorageEntriesFilterBackend,)
    serializer_class = serializers.StorageEntrySerializer
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
        try:
            return super().create(*args, **kwargs)
        except IntegrityError:
            key = self.request.DATA.get("key", None)
            raise exc.IntegrityError(_("Duplicate key value violates unique constraint. "
                                       "Key '{}' already exists.").format(key))
