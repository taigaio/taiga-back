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

from django.db.models.loading import get_model
from taiga.domains import get_active_domain


def create_project(id, owner, save=True):
    model = get_model("projects", "Project")

    instance = model(
       name="Project {0}".format(id),
       description="This is a test project",
       owner=owner,
       total_story_points=id,
       domain=get_active_domain()
    )

    if save:
        instance.save()
    return instance


def add_membership(project, user, role_slug="back"):
    model = get_model("users", "Role")
    role = model.objects.get(slug=role_slug, project=project)

    model = get_model("projects", "Membership")
    instance = model.objects.create(
        project=project,
        user=user,
        role=role
    )
    return instance
