# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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

from functools import partial
from operator import is_not

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from taiga.projects.notifications import services


class WatchedResourceMixin(object):
    """
    Rest Framework resource mixin for resources susceptible
    to be notifiable about their changes.

    NOTE: this mixin has hard dependency on HistoryMixin
    defined on history app and should be located always
    after it on inheritance definition.
    """

    _not_notify = False

    def send_notifications(self, obj, history=None):
        """
        Shortcut method for resources with special save
        cases on actions methods that not uses standard
        `post_save` hook of drf resources.
        """
        if history is None:
            history = self.get_last_history()

        # If not history found, or it is empty. Do notthing.
        if not history:
            return

        if self._not_notify:
            return

        obj = self.get_object_for_snapshot(obj)

        # Process that analizes the corresponding diff and
        # some text fields for extract mentions and add them
        # to watchers before obtain a complete list of
        # notifiable users.
        services.analize_object_for_watchers(obj, history)

        # Get a complete list of notifiable users for current
        # object and send the change notification to them.
        services.send_notifications(obj, history=history)

    def post_save(self, obj, created=False):
        self.send_notifications(obj)
        super().post_save(obj, created)

    def pre_delete(self, obj):
        self.send_notifications(obj)
        super().pre_delete(obj)


class WatchedModelMixin(models.Model):
    """
    Generic model mixin that makes model compatible
    with notification system.

    NOTE: is mandatory extend your model class with
    this mixin if you want send notifications about
    your model class.
    """
    watchers = models.ManyToManyField(settings.AUTH_USER_MODEL, null=True, blank=True,
                                      related_name="%(app_label)s_%(class)s+",
                                      verbose_name=_("watchers"))
    class Meta:
        abstract = True

    def get_project(self) -> object:
        """
        Default implementation method for obtain a project
        instance from current object.

        It comes with generic default implementation
        that should works in almost all cases.
        """
        return self.project

    def get_watchers(self) -> frozenset:
        """
        Default implementation method for obtain a list of
        watchers for current instance.

        NOTE: the default implementation returns frozen
        set of all watchers if "watchers" attribute exists
        in a model.

        WARNING: it returns a full evaluated set and in
        future, for project with 1000k watchers it can be
        very inefficient way for obtain watchers but at
        this momment is the simplest way.
        """
        return frozenset(self.watchers.all())

    def get_owner(self) -> object:
        """
        Default implementation for obtain the owner of
        current instance.
        """
        return self.owner

    def get_assigned_to(self) -> object:
        """
        Default implementation for obtain the assigned
        user.
        """
        if hasattr(self, "assigned_to"):
            return self.assigned_to
        return None

    def get_participants(self) -> frozenset:
        """
        Default implementation for obtain the list
        of participans. It is mainly the owner and
        assigned user.
        """
        participants = (self.get_assigned_to(),
                        self.get_owner(),)
        is_not_none = partial(is_not, None)
        return frozenset(filter(is_not_none, participants))
