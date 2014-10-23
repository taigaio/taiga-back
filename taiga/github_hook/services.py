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

import uuid

from taiga.projects.models import ProjectModulesConfig
from taiga.users.models import User


def set_default_config(project):
    if hasattr(project, "modules_config"):
        if project.modules_config.config is None:
            project.modules_config.config = {"github": {"secret": uuid.uuid4().hex }}
        else:
            project.modules_config.config["github"] = {"secret": uuid.uuid4().hex }
    else:
        project.modules_config = ProjectModulesConfig(project=project, config={
            "github": {
                "secret": uuid.uuid4().hex
            }
        })
    project.modules_config.save()


def get_github_user(user_id):
    user = None

    if user_id:
        try:
            user = User.objects.get(github_id=user_id)
        except User.DoesNotExist:
            pass

    if user is None:
        user = User.objects.get(is_system=True, username__startswith="github")

    return user
