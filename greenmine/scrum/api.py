# myapp/api.py
from tastypie.resources import ModelResource
from tastypie.authentication import SessionAuthentication
from tastypie.authorization import DjangoAuthorization

from greenmine.scrum.models import Project, ProjectUserRole, \
    Milestone, UserStory, Change, ChangeAttachment, Task


class ProjectResource(ModelResource):
    class Meta:
        queryset = Project.objects.all()
        resource_name = 'project'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class ProjectUserRoleResource(ModelResource):
    class Meta:
        queryset = ProjectUserRole.objects.all()
        resource_name = 'projectuserrole'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class MilestoneResource(ModelResource):
    class Meta:
        queryset = Milestone.objects.all()
        resource_name = 'milestone'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class UserStoryResource(ModelResource):
    class Meta:
        queryset = UserStory.objects.all()
        resource_name = 'userstory'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class ChangeResource(ModelResource):
    class Meta:
        queryset = Change.objects.all()
        resource_name = 'change'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class ChangeAttachmentResource(ModelResource):
    class Meta:
        queryset = ChangeAttachment.objects.all()
        resource_name = 'changeattachment'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class TaskResource(ModelResource):
    class Meta:
        queryset = Task.objects.all()
        resource_name = 'task'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()
