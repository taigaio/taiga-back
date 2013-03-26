# myapp/api.py
from tastypie.resources import ModelResource
from tastypie.authentication import SessionAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie import fields

from greenmine.scrum import models


class ProjectResource(ModelResource):
    class Meta:
        queryset = models.Project.objects.all()
        resource_name = 'project'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class MilestoneResource(ModelResource):
    class Meta:
        queryset = models.Milestone.objects.all()
        resource_name = 'milestone'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class UserStoryResource(ModelResource):
    class Meta:
        queryset = models.UserStory.objects.all()
        resource_name = 'userstory'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class ChangeResource(ModelResource):
    class Meta:
        queryset = models.Change.objects.all()
        resource_name = 'change'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class ChangeAttachmentResource(ModelResource):
    class Meta:
        queryset = models.ChangeAttachment.objects.all()
        resource_name = 'changeattachment'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class TaskResource(ModelResource):
    class Meta:
        queryset = models.Task.objects.all()
        resource_name = 'task'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class SeverityResource(ModelResource):
    class Meta:
        queryset = models.Severity.objects.all()
        resource_name = 'choices/severity'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class IssueStatusResource(ModelResource):
    class Meta:
        queryset = models.IssueStatus.objects.all()
        resource_name = 'choices/issue-status'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()

from tastypie.constants import ALL, ALL_WITH_RELATIONS

class TaskStatusResource(ModelResource):
    project = fields.ForeignKey(ProjectResource, 'project')

    class Meta:
        queryset = models.TaskStatus.objects.all()
        resource_name = 'choices/task-status'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()
        filtering = {
            "project": ALL_WITH_RELATIONS,
        }

class UserStoryStatusResource(ModelResource):
    class Meta:
        queryset = models.UserStoryStatus.objects.all()
        resource_name = 'choices/us-status'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()

class PriorityResource(ModelResource):
    class Meta:
        queryset = models.Priority.objects.all()
        resource_name = 'choices/priority'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class IssueTypeResource(ModelResource):
    class Meta:
        queryset = models.IssueType.objects.all()
        resource_name = 'choices/issue-type'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()


class PointsResource(ModelResource):
    class Meta:
        queryset = models.Points.objects.all()
        resource_name = 'choices/story-points'
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()
