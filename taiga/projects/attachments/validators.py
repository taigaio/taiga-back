# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos Ventures SL

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
