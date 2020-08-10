# Copyright (C) 2014-2019 Taiga Agile LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from taiga.base import response
from taiga.base.api.utils import get_object_or_404
from taiga.base.decorators import detail_route
from taiga.projects.models import Project
from taiga.projects.tasks.models import Task
from taiga.projects.services.promote import promote_to_us

from . import validators


class PromoteToUserStoryMixin:
    """
    Promote an instance to User Story.
    """

    @detail_route(methods=["POST"])
    def promote_to_user_story(self, request, pk=None):
        validator = validators.PromoteToUserStoryValidator(data=request.DATA)
        if not validator.is_valid():
            return response.BadRequest(validator.errors)

        data = validator.data
        project = get_object_or_404(Project, pk=data["project_id"])
        self.check_permissions(request, 'promote_to_us', project)

        obj = self.get_object()
        ret = promote_to_us(obj)
        self.persist_history_snapshot(obj=obj)

        # delete source task if required
        if isinstance(obj, Task):
            obj.delete()

        return response.Ok(ret)
