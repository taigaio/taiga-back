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
from . import signals as handlers


class IssuesAppConfig(AppConfig):
    name = "taiga.projects.issues"
    verbose_name = "Issues"

    def ready(self):
        # Finished date
        signals.pre_save.connect(handlers.set_finished_date_when_edit_issue,
                                 sender=apps.get_model("issues", "Issue"),
                                 dispatch_uid="set_finished_date_when_edit_issue")

        # Tags
        signals.pre_save.connect(generic_handlers.tags_normalization,
                                 sender=apps.get_model("issues", "Issue"))
        signals.post_save.connect(generic_handlers.update_project_tags_when_create_or_edit_taggable_item,
                                  sender=apps.get_model("issues", "Issue"))
        signals.post_delete.connect(generic_handlers.update_project_tags_when_delete_taggable_item,
                                    sender=apps.get_model("issues", "Issue"))
