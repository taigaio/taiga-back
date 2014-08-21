# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
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

import uuid

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.db import models
from django.db.models.loading import get_model
from django.utils.functional import cached_property
from django_pgjson.fields import JsonField

from .choices import HistoryType
from .choices import HISTORY_TYPE_CHOICES


class HistoryEntry(models.Model):
    """
    Domain model that represents a history
    entry storage table.

    It is used for store object changes and
    comments.
    """
    id = models.CharField(primary_key=True, max_length=255, unique=True,
                          editable=False, default=lambda: str(uuid.uuid1()))

    user = JsonField(blank=True, default=None, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    type = models.SmallIntegerField(choices=HISTORY_TYPE_CHOICES)
    is_snapshot = models.BooleanField(default=False)

    key = models.CharField(max_length=255, null=True, default=None, blank=True)

    # Stores the last diff
    diff = JsonField(null=True, default=None)

    # Stores the last complete frozen object snapshot
    snapshot = JsonField(null=True, default=None)

    # Stores a values of all identifiers used in
    values = JsonField(null=True, default=None)

    # Stores a comment
    comment = models.TextField(blank=True)
    comment_html = models.TextField(blank=True)

    @cached_property
    def is_comment(self):
        return self.type == HistoryType.comment

    @cached_property
    def owner(self):
        pk = self.user["pk"]
        model = get_model("users", "User")
        return model.objects.get(pk=pk)

    @cached_property
    def values_diff(self):
        result = {}
        users_keys = ["assigned_to", "owner"]

        def resolve_value(field, key):
            data = self.values[field]
            key = str(key)

            if key not in data:
                return None
            return data[key]

        for key in self.diff:
            value = None

            if key in users_keys:
                value = [resolve_value("users", x) for x in self.diff[key]]
            elif key == "watchers":
                value = [[resolve_value("users", x) for x in self.diff[key][0]],
                         [resolve_value("users", x) for x in self.diff[key][1]]]
            elif key == "points":
                points = {}

                pointsold = self.diff["points"][0]
                pointsnew = self.diff["points"][1]
                # pointsold = pointsnew

                if pointsold is None:
                    for role_id, point_id in pointsnew.items():
                        role_name = resolve_value("roles", role_id)
                        points[role_name] = [None, resolve_value("points", point_id)]

                else:
                    for role_id, point_id in pointsnew.items():
                        role_name = resolve_value("roles", role_id)
                        oldpoint_id = pointsold.get(role_id, None)
                        points[role_name] = [resolve_value("points", oldpoint_id),
                                           resolve_value("points", point_id)]

                # Process that removes points entries with
                # duplicate value.
                for role in dict(points):
                    values = points[role]
                    if values[1] == values[0]:
                        del points[role]

                if points:
                    value = points

            elif key == "attachments":
                attachments = {
                    "new": [],
                    "changed": [],
                    "deleted": [],
                }

                oldattachs = {x["id"]:x for x in self.diff["attachments"][0]}
                newattachs = {x["id"]:x for x in self.diff["attachments"][1]}

                for aid in set(tuple(oldattachs.keys()) + tuple(newattachs.keys())):
                    if aid in oldattachs and aid in newattachs:
                        if oldattachs[aid] != newattachs[aid]:
                            attachments["changed"].append([oldattachs[aid],newattachs[aid]])
                    elif aid in oldattachs and aid not in newattachs:
                        attachments["deleted"].append(oldattachs[aid])
                    elif aid not in oldattachs and aid in newattachs:
                        attachments["new"].append(newattachs[aid])

                if attachments["new"] or attachments["changed"] or attachments["deleted"]:
                    value = attachments

            elif key in self.values:
                value = [resolve_value(key, x) for x in self.diff[key]]
            else:
                value = self.diff[key]

            if not value:
                continue

            result[key] = value

        return result

    class Meta:
        ordering = ["created_at"]

