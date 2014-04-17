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

from taiga.projects.models import UserStoryStatus


class ProjectTemplateManager(object):
    def apply(self, template, project):
        if not hasattr(self, "template"):
            return False
        template = getattr(self, "template")
        template(project)

    def legal(self, project):
        pass

    def pure_kanban(self, project):
        project.is_backlog_activated = False
        project.is_kanban_activated = True
        project.is_wiki_activated = False
        project.is_issues_activated = False
        project.save()

        us_status = project.us_statuses.get(order=1)
        us_status.name = "To do"
        us_status.color = "#999999"
        us_status.save()

        us_status = project.us_statuses.get(order=2)
        us_status.name = "Doing"
        us_status.color = "#ff9900"
        us_status.is_closed = False
        us_status.save()

        us_status = UserStoryStatus()
        us_status.order = 3
        us_status.name = "Done"
        us_status.color = "#ffcc00"
        us_status.project = project
        us_status.is_closed = True
        us_status.save()
