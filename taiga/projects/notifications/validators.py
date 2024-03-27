# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.translation import gettext as _

from taiga.base.exceptions import ValidationError


class WatchersValidator:
    def validate_watchers(self, attrs, source):
        users = attrs.get(source, [])

        # Try obtain a valid project
        if self.object is None and "project" in attrs:
            project = attrs["project"]
        elif self.object:
            project = self.object.project
        else:
            project = None

        # If project is empty in all conditions, continue
        # without errors, because other validator should
        # validate the empty project field.
        if not project:
            return attrs

        # Check if incoming watchers are contained
        # in project members list
        member_ids = project.members.values_list("id", flat=True)
        existing_watcher_ids = project.get_watchers().values_list("id", flat=True)
        result = set(users).difference(member_ids).difference(existing_watcher_ids)
        if result:
            raise ValidationError(_("Watchers contains invalid users"))

        return attrs
