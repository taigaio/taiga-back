#
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
