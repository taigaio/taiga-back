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

from django.apps import AppConfig
from django.apps import apps
from django.db.models import signals

from . import signals as handlers


class ProjectsAppConfig(AppConfig):
    name = "taiga.projects"
    verbose_name = "Projects"

    def ready(self):
        # On membership object is deleted, update role-points relation.
        signals.pre_delete.connect(handlers.membership_post_delete,
                                   sender=apps.get_model("projects", "Membership"),
                                   dispatch_uid='membership_pre_delete')

        # On membership object is deleted, update watchers of all objects relation.
        signals.post_delete.connect(handlers.update_watchers_on_membership_post_delete,
                                    sender=apps.get_model("projects", "Membership"),
                                    dispatch_uid='update_watchers_on_membership_post_delete')

        # On membership object is deleted, update watchers of all objects relation.
        signals.post_save.connect(handlers.create_notify_policy,
                                  sender=apps.get_model("projects", "Membership"),
                                  dispatch_uid='create-notify-policy')

        # On project object is created apply template.
        signals.post_save.connect(handlers.project_post_save,
                                  sender=apps.get_model("projects", "Project"),
                                  dispatch_uid='project_post_save')
