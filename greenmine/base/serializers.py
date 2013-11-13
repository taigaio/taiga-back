# -*- coding: utf-8 -*-

from rest_framework import serializers

from reversion.models import Version


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
    user = serializers.SerializerMethodField("get_user")
    comment = serializers.SerializerMethodField("get_comment")
    fields = serializers.SerializerMethodField("get_object_fields")

    class Meta:
        model = Version
        fields = ("id", "created_date", "content_type", "object_id", "user", "comment",
                  "fields")
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
