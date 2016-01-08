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

import warnings

from .services import take_snapshot
from taiga.projects.notifications import services as notifications_services

class HistoryResourceMixin(object):
    """
    Rest Framework resource mixin for resources
    susceptible to have models with history.
    """

    # This attribute will store the last history entry
    # created for this resource. It is mainly used for
    # notifications mixin.
    __last_history = None
    __object_saved = False

    def get_last_history(self):
        if not self.__object_saved:
            message = ("get_last_history() function called before any object are saved. "
                       "Seems you have a wrong mixing order on your resource.")
            warnings.warn(message, RuntimeWarning)
        return self.__last_history

    def get_object_for_snapshot(self, obj):
        """
        Method that returns a model instance ready to snapshot.
        It is by default noop, but should be overwrited when
        snapshot ready instance is found in one of foreign key
        fields.
        """
        return obj

    def persist_history_snapshot(self, obj=None, delete:bool=False):
        """
        Shortcut for resources with special save/persist
        logic.
        """

        user = self.request.user
        comment = self.request.DATA.get("comment", "")

        if obj is None:
            obj = self.get_object()

        sobj = self.get_object_for_snapshot(obj)
        if sobj != obj and delete:
            delete = False

        notifications_services.analize_object_for_watchers(obj, comment, user)

        self.__last_history = take_snapshot(sobj, comment=comment, user=user, delete=delete)
        self.__object_saved = True

    def post_save(self, obj, created=False):
        self.persist_history_snapshot(obj=obj)
        super().post_save(obj, created=created)

    def pre_delete(self, obj):
        self.persist_history_snapshot(obj, delete=True)
        super().pre_delete(obj)
