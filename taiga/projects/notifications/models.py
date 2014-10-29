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

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from .choices import NOTIFY_LEVEL_CHOICES
from taiga.projects.history.choices import HISTORY_TYPE_CHOICES

class NotifyPolicy(models.Model):
    """
    This class represents a persistence for
    project user notifications preference.
    """
    project = models.ForeignKey("projects.Project", related_name="notify_policies")
    user = models.ForeignKey("users.User", related_name="notify_policies")
    notify_level = models.SmallIntegerField(choices=NOTIFY_LEVEL_CHOICES)

    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField()
    _importing = None

    class Meta:
        unique_together = ("project", "user",)
        ordering = ["created_at"]

    def save(self, *args, **kwargs):
        if not self._importing or not self.modified_date:
            self.modified_at = timezone.now()

        return super().save(*args, **kwargs)


class HistoryChangeNotification(models.Model):
    """
    This class controls the pending notifications for an object, it should be instantiated
    or updated when an object requires notifications.
    """
    key = models.CharField(max_length=255, unique=False, editable=False)
    owner = models.ForeignKey("users.User", null=False, blank=False,
                              verbose_name="owner",related_name="+")
    created_datetime = models.DateTimeField(null=False, blank=False, auto_now_add=True,
                                            verbose_name=_("created date time"))
    updated_datetime = models.DateTimeField(null=False, blank=False, auto_now_add=True,
                                            verbose_name=_("updated date time"))
    history_entries = models.ManyToManyField("history.HistoryEntry", null=True, blank=True,
                                             verbose_name="history entries",
                                             related_name="+")
    notify_users = models.ManyToManyField("users.User", null=True, blank=True,
                                             verbose_name="notify users",
                                             related_name="+")
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                verbose_name="project",related_name="+")

    history_type = models.SmallIntegerField(choices=HISTORY_TYPE_CHOICES)

    class Meta:
        unique_together = ("key", "owner", "project", "history_type")
