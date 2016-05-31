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

from django.apps import AppConfig
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.models import signals


class TimelineAppConfig(AppConfig):
    name = "taiga.timeline"
    verbose_name = "Timeline"

    def ready(self):
        from . import signals as handlers

        signals.post_save.connect(handlers.on_new_history_entry,
                                  sender=apps.get_model("history", "HistoryEntry"),
                                  dispatch_uid="timeline")
        signals.post_save.connect(handlers.create_membership_push_to_timeline,
                                                 sender=apps.get_model("projects", "Membership"))
        signals.pre_delete.connect(handlers.delete_membership_push_to_timeline,
                                                sender=apps.get_model("projects", "Membership"))
        signals.post_save.connect(handlers.create_user_push_to_timeline,
                                                 sender=get_user_model())
