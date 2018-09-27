# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

import enum
from django.utils.translation import ugettext_lazy as _


class NotifyLevel(enum.IntEnum):
    involved = 1
    all = 2
    none = 3


NOTIFY_LEVEL_CHOICES = (
    (NotifyLevel.involved, _("Involved")),
    (NotifyLevel.all, _("All")),
    (NotifyLevel.none, _("None")),
)


class WebNotificationType(enum.IntEnum):
    assigned = 1
    mentioned = 2
    added_as_watcher = 3
    added_as_member = 4
    comment = 5
    mentioned_in_comment = 6


WEB_NOTIFICATION_TYPE_CHOICES = (
    (WebNotificationType.assigned, _("Assigned")),
    (WebNotificationType.mentioned, _("Mentioned")),
    (WebNotificationType.added_as_watcher, _("Added as watcher")),
    (WebNotificationType.added_as_member, _("Added as member")),
    (WebNotificationType.comment, _("Comment")),
    (WebNotificationType.mentioned_in_comment, _("Mentioned in comment")),
)
