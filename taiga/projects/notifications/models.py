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



class WatcherMixin(models.Model):
    NOTIFY_LEVEL_CHOICES = (
        ("all_owned_projects", _(u"All events on my projects")),
        ("only_assigned", _(u"Only events for objects assigned to me")),
        ("only_owner", _(u"Only events for objects owned by me")),
        ("no_events", _(u"No events")),
    )

    notify_level = models.CharField(max_length=32, null=False, blank=False,
                                    default="all_owned_projects",
                                    choices=NOTIFY_LEVEL_CHOICES,
                                    verbose_name=_(u"notify level"))
    notify_changes_by_me = models.BooleanField(blank=True, default=False,
                                               verbose_name=_(u"notify changes by me"))

    class Meta:
        abstract = True

    def allow_notify_owned(self):
        return (self.notify_level in [
            "only_owner",
            "only_assigned",
            "only_watching",
            "all_owned_projects",
        ])

    def allow_notify_assigned_to(self):
        return (self.notify_level in [
            "only_assigned",
            "only_watching",
            "all_owned_projects",
        ])

    def allow_notify_suscribed(self):
        return (self.notify_level in [
            "only_watching",
            "all_owned_projects",
        ])

    def allow_notify_project(self, project):
        return self.notify_level == "all_owned_projects"


class WatchedMixin(object):
    def get_watchers_to_notify(self, changer):
        watchers_to_notify = set()
        watchers_by_role = self._get_watchers_by_role()

        owner = watchers_by_role.get("owner", None)
        if owner and owner.allow_notify_owned():
            watchers_to_notify.add(owner)

        assigned_to = watchers_by_role.get("assigned_to", None)
        if assigned_to and assigned_to.allow_notify_assigned_to():
            watchers_to_notify.add(assigned_to)

        suscribed_watchers = watchers_by_role.get("suscribed_watchers", None)
        if suscribed_watchers:
            for suscribed_watcher in suscribed_watchers:
                if suscribed_watcher and suscribed_watcher.allow_notify_suscribed():
                    watchers_to_notify.add(suscribed_watcher)

        project = watchers_by_role.get("project", None)
        if project:
            for member in project.members.all():
                if member and member.allow_notify_project(project):
                    watchers_to_notify.add(member)

        if changer.notify_changes_by_me:
            watchers_to_notify.add(changer)
        else:
            if changer in watchers_to_notify:
                watchers_to_notify.remove(changer)

        return watchers_to_notify

    def _get_watchers_by_role(self):
        """
        Return the actual instances of watchers of this object, classified by role.
        For example:

           return {
               "owner": self.owner,
               "assigned_to": self.assigned_to,
               "suscribed_watchers": self.watchers.all(),
               "project_owner": (self.project, self.project.owner),
           }
        """
        raise NotImplementedError("You must subclass WatchedMixin and provide "
                                  "_get_watchers_by_role method")
