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

from taiga.projects import signals as generic_handlers
from taiga.projects.custom_attributes import signals as custom_attributes_handlers
from . import signals as handlers


class TasksAppConfig(AppConfig):
    name = "taiga.projects.tasks"
    verbose_name = "Tasks"

    def ready(self):
        # Cached prev object version
        signals.pre_save.connect(handlers.cached_prev_task,
                                 sender=apps.get_model("tasks", "Task"))

        # Open/Close US and Milestone
        signals.post_save.connect(handlers.try_to_close_or_open_us_and_milestone_when_create_or_edit_task,
                                 sender=apps.get_model("tasks", "Task"))
        signals.post_delete.connect(handlers.try_to_close_or_open_us_and_milestone_when_delete_task,
                                    sender=apps.get_model("tasks", "Task"))

        # Tags
        signals.pre_save.connect(generic_handlers.tags_normalization,
                                 sender=apps.get_model("tasks", "Task"))
        signals.post_save.connect(generic_handlers.update_project_tags_when_create_or_edit_taggable_item,
                                  sender=apps.get_model("tasks", "Task"))
        signals.post_delete.connect(generic_handlers.update_project_tags_when_delete_taggable_item,
                                    sender=apps.get_model("tasks", "Task"))

        # Custom Attributes
        signals.post_save.connect(custom_attributes_handlers.create_custom_attribute_value_when_create_task,
                                  sender=apps.get_model("tasks", "Task"),
                                  dispatch_uid="create_custom_attribute_value_when_create_task")
