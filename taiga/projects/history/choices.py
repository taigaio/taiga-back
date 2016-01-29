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


import enum

from django.utils.translation import ugettext_lazy as _


class HistoryType(enum.IntEnum):
    change = 1
    create = 2
    delete = 3


HISTORY_TYPE_CHOICES = ((HistoryType.change, _("Change")),
                        (HistoryType.create, _("Create")),
                        (HistoryType.delete, _("Delete")))
