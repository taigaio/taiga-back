# -*- coding: utf-8 -*-

from rest_framework import serializers

from reversion.models import Version
import reversion


class PickleField(serializers.WritableField):
    """
    Pickle objects serializer.
    """
    def to_native(self, obj):
        return obj

    def from_native(self, data):
        return data


class VersionSerializer(serializers.ModelSerializer):
    created_date = serializers.SerializerMethodField("get_created_date")
    content_type = serializers.SerializerMethodField("get_content_type")
    object_id = serializers.SerializerMethodField("get_object_id")
    type_name = serializers.SerializerMethodField("get_type")
    user = serializers.SerializerMethodField("get_user")
    comment = serializers.SerializerMethodField("get_comment")
    fields = serializers.SerializerMethodField("get_object_fields")
    changed_fields  = serializers.SerializerMethodField("get_changed_fields")

    class Meta:
        model = Version
        fields = ("id", "created_date", "content_type", "object_id", "type",
                  "type_name", "user", "comment", "fields", "changed_fields")
        read_only = fields

    def get_created_date(self, obj):
        return obj.revision.date_created

    def get_content_type(self, obj):
        return obj.content_type.model

    def get_object_id(self, obj):
        return obj.object_id_int

    def get_type(self, obj):
        return obj.get_type_display()

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
