# -*- coding: utf-8 -*-
from taiga.base.api import serializers
from taiga.base.api import validators

from . import models


class AttachmentValidator(validators.ModelValidator):
    attached_file = serializers.FileField(required=True)

    class Meta:
        model = models.Attachment
        fields = ("id", "project", "owner", "name", "attached_file", "size",
                  "description", "is_deprecated", "created_date",
                  "modified_date", "object_id", "order", "sha1", "from_comment")
        read_only_fields = ("owner", "created_date", "modified_date", "sha1")
