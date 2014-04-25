# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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

from rest_framework import serializers

from reversion.models import Version
import reversion

from taiga.domains.base import get_active_domain
from taiga.domains.models import Domain


class PickleField(serializers.WritableField):
    """
    Pickle objects serializer.
    """
    def to_native(self, obj):
        return obj

    def from_native(self, data):
        return data


class JsonField(serializers.WritableField):
    """
    Json objects serializer.
    """
    def to_native(self, obj):
        return obj

    def from_native(self, data):
        return data

class AutoDomainField(serializers.WritableField):
    """
    Automatically set domain field serializer.
    """
    def to_native(self, obj):
        if obj:
            return obj.id
        return obj

    def from_native(self, data):
        domain = get_active_domain()
        return domain

class VersionSerializer(serializers.ModelSerializer):
    created_date = serializers.SerializerMethodField("get_created_date")
    content_type = serializers.SerializerMethodField("get_content_type")
    object_id = serializers.SerializerMethodField("get_object_id")
    user = serializers.SerializerMethodField("get_user")
    comment = serializers.SerializerMethodField("get_comment")
    fields = serializers.SerializerMethodField("get_object_fields")
    changed_fields  = serializers.SerializerMethodField("get_changed_fields")

    class Meta:
        model = Version
        fields = ("id", "created_date", "content_type", "object_id", "user", "comment",
                  "fields", "changed_fields")
        read_only = fields

    def get_created_date(self, obj):
        return obj.revision.date_created

    def get_content_type(self, obj):
        return obj.content_type.model

    def get_object_id(self, obj):
        return obj.object_id_int

    def get_object_fields(self, obj):
        return obj.field_dict

    def get_user(self, obj):
        return obj.revision.user.id if obj.revision.user else None

    def get_comment(self, obj):
        return obj.revision.comment

    def get_object_old_fields(self, obj):
        versions = reversion.get_unique_for_object(obj.object)
        try:
            return versions[versions.index(obj) + 1].field_dict
        except IndexError:
            return {}

    def get_changed_fields(self, obj):
        new_fields = self.get_object_fields(obj)
        old_fields = self.get_object_old_fields(obj)

        changed_fields = {}
        for key in new_fields.keys() | old_fields.keys():
            if key == "modified_date":
                continue

            if old_fields.get(key, "") == new_fields.get(key, ""):
                continue

            changed_fields[key] = {
                 "name": obj.object.__class__._meta.get_field_by_name(
                                                   key)[0].verbose_name,
                 "old": old_fields.get(key, None),
                 "new": new_fields.get(key, None),
              }

        return changed_fields


class NeighborsSerializerMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["neighbors"] = serializers.SerializerMethodField("get_neighbors")

    def serialize_neighbor(self, neighbor):
        raise NotImplementedError

    def get_neighbors(self, obj):
        view, request = self.context.get("view", None), self.context.get("request", None)
        if view and request:
            queryset = view.filter_queryset(view.get_queryset(), True)
            previous, next = obj.get_neighbors(queryset)

            return {"previous": self.serialize_neighbor(previous),
                    "next": self.serialize_neighbor(next)}
        return {"previous": None, "next": None}
