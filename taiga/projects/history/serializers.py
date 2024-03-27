# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api import serializers
from taiga.base.fields import I18NJSONField, Field, MethodField

from taiga.users.services import get_user_photo_url
from taiga.users.gravatar import get_user_gravatar_id


HISTORY_ENTRY_I18N_FIELDS = ("points", "status", "severity", "priority", "type")


class HistoryEntrySerializer(serializers.LightSerializer):
    id = Field()
    user = MethodField()
    created_at = Field()
    type = Field()
    key = Field()
    diff = Field()
    snapshot = Field()
    values = Field()
    values_diff = I18NJSONField()
    comment = I18NJSONField()
    comment_html = Field()
    delete_comment_date = Field()
    delete_comment_user = Field()
    edit_comment_date = Field()
    is_hidden = Field()
    is_snapshot = Field()

    def get_user(self, entry):
        user = {"pk": None, "username": None, "name": None, "photo": None, "is_active": False}
        user.update(entry.user)
        user["photo"] = get_user_photo_url(entry.owner)
        user["gravatar_id"] = get_user_gravatar_id(entry.owner)

        if entry.owner:
            user["is_active"] = entry.owner.is_active

            if entry.owner.is_active or entry.owner.is_system:
                user["name"] = entry.owner.get_full_name()
                user["username"] = entry.owner.username

        return user
