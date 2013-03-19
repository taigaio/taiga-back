# myapp/api.py
from tastypie.resources import ModelResource
from greenmine.scrum.models import *

class ProjectResource(ModelResource):
    class Meta:
        queryset = Project.objects.all()
        resource_name = 'project'

class ProjectUserRoleResource(ModelResource):
    class Meta:
        queryset = ProjectUserRole.objects.all()
        resource_name = 'projectuserrole'

class MilestoneResource(ModelResource):
    class Meta:
        queryset = Milestone.objects.all()
        resource_name = 'milestone'

class UserStoryResource(ModelResource):
    class Meta:
        queryset = UserStory.objects.all()
        resource_name = 'userstory'

class ChangeResource(ModelResource):
    class Meta:
        queryset = Change.objects.all()
        resource_name = 'change'

class ChangeAttachmentResource(ModelResource):
    class Meta:
        queryset = ChangeAttachment.objects.all()
        resource_name = 'changeattachment'

class TaskResource(ModelResource):
    class Meta:
        queryset = Task.objects.all()
        resource_name = 'task'
