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

from taiga.base.api import serializers
from taiga.base.fields import JsonField, I18NJsonField

from taiga.users.services import get_photo_or_gravatar_url

from . import models


HISTORY_ENTRY_I18N_FIELDS=("points", "status", "severity", "priority", "type")


class HistoryEntrySerializer(serializers.ModelSerializer):
    diff = JsonField()
    snapshot = JsonField()
    values = I18NJsonField(i18n_fields=HISTORY_ENTRY_I18N_FIELDS)
    values_diff = I18NJsonField(i18n_fields=HISTORY_ENTRY_I18N_FIELDS)
    user = serializers.SerializerMethodField("get_user")
    delete_comment_user = JsonField()

    class Meta:
        model = models.HistoryEntry

    def get_user(self, entry):
        user = {"pk": None, "username": None, "name": None, "photo": None, "is_active": False}
        user.update(entry.user)
        user["photo"] = get_photo_or_gravatar_url(entry.owner)

        if entry.owner:
            user["is_active"] = entry.owner.is_active

            if entry.owner.is_active or entry.owner.is_system:
                user["name"] = entry.owner.get_full_name()
                user["username"] = entry.owner.username

        return user
