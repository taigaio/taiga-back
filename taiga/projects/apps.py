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
from django.db.models import signals


## Project Signals

def connect_projects_signals():
    from . import signals as handlers
    # On project object is created apply template.
    signals.post_save.connect(handlers.project_post_save,
                              sender=apps.get_model("projects", "Project"),
                              dispatch_uid='project_post_save')

    # Tags normalization after save a project
    signals.pre_save.connect(handlers.tags_normalization,
                             sender=apps.get_model("projects", "Project"),
                             dispatch_uid="tags_normalization_projects")
    signals.pre_save.connect(handlers.update_project_tags_when_create_or_edit_taggable_item,
                             sender=apps.get_model("projects", "Project"),
                             dispatch_uid="update_project_tags_when_create_or_edit_taggable_item_projects")


def disconnect_projects_signals():
    signals.post_save.disconnect(sender=apps.get_model("projects", "Project"),
                                 dispatch_uid='project_post_save')
    signals.pre_save.disconnect(sender=apps.get_model("projects", "Project"),
                                dispatch_uid="tags_normalization_projects")
    signals.pre_save.disconnect(sender=apps.get_model("projects", "Project"),
                                dispatch_uid="update_project_tags_when_create_or_edit_taggable_item_projects")


## Memberships Signals

def connect_memberships_signals():
    from . import signals as handlers
    # On membership object is deleted, update role-points relation.
    signals.pre_delete.connect(handlers.membership_post_delete,
                               sender=apps.get_model("projects", "Membership"),
                               dispatch_uid='membership_pre_delete')

    # On membership object is deleted, update notify policies of all objects relation.
    signals.post_save.connect(handlers.create_notify_policy,
                              sender=apps.get_model("projects", "Membership"),
                              dispatch_uid='create-notify-policy')

def disconnect_memberships_signals():
    signals.pre_delete.disconnect(sender=apps.get_model("projects", "Membership"),
                                  dispatch_uid='membership_pre_delete')
    signals.post_save.disconnect(sender=apps.get_model("projects", "Membership"),
                                 dispatch_uid='create-notify-policy')


## US Statuses Signals

def connect_us_status_signals():
    from . import signals as handlers
    signals.post_save.connect(handlers.try_to_close_or_open_user_stories_when_edit_us_status,
                              sender=apps.get_model("projects", "UserStoryStatus"),
                              dispatch_uid="try_to_close_or_open_user_stories_when_edit_us_status")


def disconnect_us_status_signals():
    signals.post_save.disconnect(sender=apps.get_model("projects", "UserStoryStatus"),
                                 dispatch_uid="try_to_close_or_open_user_stories_when_edit_us_status")



## Tasks Statuses Signals

def connect_task_status_signals():
    from . import signals as handlers
    signals.post_save.connect(handlers.try_to_close_or_open_user_stories_when_edit_task_status,
                              sender=apps.get_model("projects", "TaskStatus"),
                              dispatch_uid="try_to_close_or_open_user_stories_when_edit_task_status")


def disconnect_task_status_signals():
    signals.post_save.disconnect(sender=apps.get_model("projects", "TaskStatus"),
                                 dispatch_uid="try_to_close_or_open_user_stories_when_edit_task_status")



class ProjectsAppConfig(AppConfig):
    name = "taiga.projects"
    verbose_name = "Projects"

    def ready(self):
        connect_projects_signals()
        connect_memberships_signals()
        connect_us_status_signals()
        connect_task_status_signals()
