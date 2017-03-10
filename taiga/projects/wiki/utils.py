# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2017 Anler Hernández <hello@anler.me>
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

from taiga.projects.notifications.utils import attach_watchers_to_queryset
from taiga.projects.notifications.utils import attach_total_watchers_to_queryset
from taiga.projects.notifications.utils import attach_is_watcher_to_queryset


def attach_extra_info(queryset, user=None, include_attachments=False):
    queryset = attach_watchers_to_queryset(queryset)
    queryset = attach_total_watchers_to_queryset(queryset)
    queryset = attach_is_watcher_to_queryset(queryset, user)
    return queryset
