# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
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

from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.functional import cached_property
from django_pgjson.fields import JsonField

from taiga.mdrender.service import get_diff_of_htmls

from .choices import HistoryType
from .choices import HISTORY_TYPE_CHOICES

from taiga.base.utils.diff import make_diff as make_diff_from_dicts

# This keys has been removed from freeze_impl so we can have objects where the
# previous diff has value for the attribute and we want to prevent their propagation
IGNORE_DIFF_FIELDS = [ "watchers", "description_diff", "content_diff", "blocked_note_diff"]

def _generate_uuid():
    return str(uuid.uuid1())


class HistoryEntry(models.Model):
    """
    Domain model that represents a history
    entry storage table.

    It is used for store object changes and
    comments.
    """
    id = models.CharField(primary_key=True, max_length=255, unique=True,
                          editable=False, default=_generate_uuid)

    user = JsonField(null=True, blank=True, default=None)
    created_at = models.DateTimeField(default=timezone.now)
    type = models.SmallIntegerField(choices=HISTORY_TYPE_CHOICES)
    key = models.CharField(max_length=255, null=True, default=None, blank=True, db_index=True)

    # Stores the last diff
    diff = JsonField(null=True, blank=True, default=None)

    # Stores the last complete frozen object snapshot
    snapshot = JsonField(null=True, blank=True, default=None)

    # Stores a values of all identifiers used in
    values = JsonField(null=True, blank=True, default=None)

    # Stores a comment
    comment = models.TextField(blank=True)
    comment_html = models.TextField(blank=True)

    delete_comment_date = models.DateTimeField(null=True, blank=True, default=None)
    delete_comment_user = JsonField(null=True, blank=True, default=None)

    # Flag for mark some history entries as
    # hidden. Hidden history entries are important
    # for save but not important to preview.
    # Order fields are the good example of this fields.
    is_hidden = models.BooleanField(default=False)

    # Flag for mark some history entries as complete
    # snapshot. The rest are partial snapshot.
    is_snapshot = models.BooleanField(default=False)

    _importing = None

    @cached_property
    def is_change(self):
      return self.type == HistoryType.change

    @cached_property
    def is_create(self):
      return self.type == HistoryType.create

    @cached_property
    def is_delete(self):
      return self.type == HistoryType.delete

    @cached_property
    def owner(self):
        pk = self.user["pk"]
        model = get_user_model()
        try:
            return model.objects.get(pk=pk)
        except model.DoesNotExist:
            return None

    @cached_property
    def values_diff(self):
        result = {}
        users_keys = ["assigned_to", "owner"]

        def resolve_diff_value(key):
            value = None
            diff = get_diff_of_htmls(
                self.diff[key][0] or "",
                self.diff[key][1] or ""
            )

            if diff:
                key = "{}_diff".format(key)
                value = (None, diff)

            return (key, value)

        def resolve_value(field, key):
            data = self.values[field]
            key = str(key)

            if key not in data:
                return None
            return data[key]

        for key in self.diff:
            value = None
            if key in IGNORE_DIFF_FIELDS:
                continue
            elif key in["description", "content", "blocked_note"]:
                (key, value) = resolve_diff_value(key)
            elif key in users_keys:
                value = [resolve_value("users", x) for x in self.diff[key]]
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
                        changes = make_diff_from_dicts(oldattachs[aid], newattachs[aid],
                                                       excluded_keys=("filename", "url", "thumb_url"))

                        if changes:
                            change = {
                                "filename": newattachs.get(aid, {}).get("filename", ""),
                                "url": newattachs.get(aid, {}).get("url", ""),
                                "thumb_url": newattachs.get(aid, {}).get("thumb_url", ""),
                                "changes": changes
                            }
                            attachments["changed"].append(change)
                    elif aid in oldattachs and aid not in newattachs:
                        attachments["deleted"].append(oldattachs[aid])
                    elif aid not in oldattachs and aid in newattachs:
                        attachments["new"].append(newattachs[aid])

                if attachments["new"] or attachments["changed"] or attachments["deleted"]:
                    value = attachments

            elif key == "custom_attributes":
                custom_attributes = {
                    "new": [],
                    "changed": [],
                    "deleted": [],
                }

                oldcustattrs = {x["id"]:x for x in self.diff["custom_attributes"][0] or []}
                newcustattrs = {x["id"]:x for x in self.diff["custom_attributes"][1] or []}

                for aid in set(tuple(oldcustattrs.keys()) + tuple(newcustattrs.keys())):
                    if aid in oldcustattrs and aid in newcustattrs:
                        changes = make_diff_from_dicts(oldcustattrs[aid], newcustattrs[aid],
                                                       excluded_keys=("name"))

                        if changes:
                            change = {
                                "name": newcustattrs.get(aid, {}).get("name", ""),
                                "changes": changes
                            }
                            custom_attributes["changed"].append(change)
                    elif aid in oldcustattrs and aid not in newcustattrs:
                        custom_attributes["deleted"].append(oldcustattrs[aid])
                    elif aid not in oldcustattrs and aid in newcustattrs:
                        custom_attributes["new"].append(newcustattrs[aid])

                if custom_attributes["new"] or custom_attributes["changed"] or custom_attributes["deleted"]:
                    value = custom_attributes

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
