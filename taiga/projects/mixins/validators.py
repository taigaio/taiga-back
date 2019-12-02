from django.utils.translation import ugettext as _

from taiga.base.api import validators, serializers
from taiga.base.exceptions import ValidationError
from taiga.projects.models import Membership
from taiga.projects.validators import ProjectExistsValidator


class AssignedToValidator:
    def validate_assigned_to(self, attrs, source):
        assigned_to = attrs[source]
        project = (attrs.get("project", None) or
                   getattr(self.object, "project", None))

        if assigned_to and project:
            filters = {
                "project_id": project.id,
                "user_id": assigned_to.id
            }

            if not Membership.objects.filter(**filters).exists():
                raise ValidationError(_("The user must be a project member."))

        return attrs


class PromoteToUserStoryValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
