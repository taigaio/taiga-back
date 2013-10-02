# -*- coding: utf-8 -*-

from rest_framework import serializers

from greenmine.base.serializers import PickleField

from . import models


class AttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField("get_url")

    def get_url(self, obj):
        # FIXME: add sites or correct url.
        if obj.attached_file:
            return "http://localhost:8000{0}".format(obj.attached_file.url)
        return None

    class Meta:
        model = Attachment
        fields = ("id", "project", "owner", "attached_file",
                  "created_date", "object_id", "url")
        read_only_fields = ("owner",)
        fields = ()


class ProjectSerializer(serializers.ModelSerializer):
    tags = PickleField()
    list_of_milestones = serializers.Field(source="list_of_milestones")

    class Meta:
        model = Project
