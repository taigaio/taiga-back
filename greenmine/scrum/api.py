# -*- coding: utf-8 -*-

from django.db.models import Q

from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from greenmine.base.users.models import *
from greenmine.base.notifications.api import NotificationSenderMixin

from greenmine.scrum.serializers import *
from greenmine.scrum.models import *
from greenmine.scrum.permissions import *

# Generic viewset subclasses for this module

class ModelCrudViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                       mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                       mixins.DestroyModelMixin, viewsets.GenericViewSet):
    pass


class ModelListViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                                                viewsets.GenericViewSet):
    pass



# ViewSets definition

class ProjectViewSet(NotificationSenderMixin, ModelCrudViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticated, ProjectDetailPermission,)

    create_notification_template = "create_project_notification"
    update_notification_template = "update_project_notification"
    destroy_notification_template = "destroy_project_notification"

    def get_queryset(self):
        qs = super(ProjectViewSet, self).get_queryset()
        qs = qs.filter(Q(owner=self.request.user) |
                       Q(members=self.request.user))
        return qs.distinct()

    def pre_save(self, obj):
        super(ProjectViewSet, self).pre_save(obj)
        obj.owner = self.request.user



class MilestoneViewSet(NotificationSenderMixin, ModelCrudViewSet):
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    permission_classes = (IsAuthenticated, MilestoneDetailPermission,)
    create_notification_template = "create_milestone_notification"
    update_notification_template = "update_milestone_notification"
    destroy_notification_template = "destroy_milestone_notification"

    filter_fields = ('project',)

    def get_queryset(self):
        qs = super(MilestoneViewSet, self).get_queryset()
        return qs.filter(project__members=self.request.user).distinct()

    def pre_save(self, obj):
        super(MilestoneViewSet, self).pre_save(obj)
        obj.owner = self.request.user


class UserStoryViewSet(NotificationSenderMixin, ModelCrudViewSet):
    queryset = UserStory.objects.all()
    serializer_class = UserStorySerializer
    permission_classes = (IsAuthenticated, UserStoryDetailPermission,)

    create_notification_template = "create_user_story_notification"
    update_notification_template = "update_user_story_notification"
    destroy_notification_template = "destroy_user_story_notification"

    filter_fields = ['project', 'milestone', 'milestone__isnull']

    def get_queryset(self):
        qs = super(UserStoryViewSet, self).get_queryset()
        return qs.filter(project__members=self.request.user).distinct()

    def pre_save(self, obj):
        super(UserStoryViewSet, self).pre_save(obj)
        obj.owner = self.request.user

    def post_save(self, obj, created=False):
        with reversion.create_revision():
            if "comment" in self.request.DATA:
                # Update the comment in the last version
                reversion.set_comment(self.request.DATA['comment'])
        super(UserStoryViewSet, self).post_save(obj, created)




class IssuesAttachmentViewSet(ModelCrudViewSet):
    model = Attachment
    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated, AttachmentDetailPermission,)

    filter_fields = ["project", "object_id"]

    def get_queryset(self):
        ct = ContentType.objects.get_for_model(Issue)
        qs = super(IssuesAttachmentViewSet, self).get_queryset()

        qs = qs.filter(project__members=self.request.user)
        qs = qs.filter(content_type=ct)

        return qs.distinct()

    def pre_save(self, obj):
        super(IssuesAttachmentViewSet, self).pre_save(obj)
        obj.content_type = ContentType.objects.get_for_model(Issue)
        obj.owner = self.request.user


class TasksAttachmentViewSet(ModelCrudViewSet):
    model = Attachment
    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated, AttachmentDetailPermission,)
    filter_fields = ["project", "object_id"]

    def get_queryset(self):
        ct = ContentType.objects.get_for_model(Task)
        qs = super(TasksAttachmentViewSet, self).get_queryset()

        qs = qs.filter(project__members=self.request.user)
        qs = qs.filter(content_type=ct)

        return qs.distinct()

    def pre_save(self, obj):
        super(TasksAttachmentViewSet, self).pre_save(obj)
        obj.content_type = ContentType.objects.get_for_model(Task)
        obj.owner = self.request.user


class TaskViewSet(NotificationSenderMixin, ModelCrudViewSet):
    queryset = Task.objects.all()

    serializer_class = TaskSerializer
    permission_classes = (IsAuthenticated, TaskDetailPermission,)

    create_notification_template = "create_task_notification"
    update_notification_template = "update_task_notification"
    destroy_notification_template = "destroy_task_notification"
    filter_fields = ['user_story', 'milestone', 'project']

    def get_queryset(self):
        qs = super(TaskViewSet, self).get_queryset()
        qs = qs.filter(project__members=self.request.user)
        return qs.distinct()

    def pre_save(self, obj):
        super(TaskViewSet, self).pre_save(obj)
        obj.owner = self.request.user
        obj.milestone = obj.user_story.milestone

    def post_save(self, obj, created=False):
        with reversion.create_revision():
            if "comment" in self.request.DATA:
                # Update the comment in the last version
                reversion.set_comment(self.request.DATA['comment'])
        super(TaskViewSet, self).post_save(obj, created)



class IssueViewSet(NotificationSenderMixin, ModelCrudViewSet):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    permission_classes = (IsAuthenticated, IssueDetailPermission,)

    create_notification_template = "create_issue_notification"
    update_notification_template = "update_issue_notification"
    destroy_notification_template = "destroy_issue_notification"

    filter_fields = ('project',)

    def pre_save(self, obj):
        super(IssueViewSet, self).pre_save(obj)
        obj.owner = self.request.user

    def post_save(self, obj, created=False):
        with reversion.create_revision():
            if "comment" in self.request.DATA:
                # Update the comment in the last version
                reversion.set_comment(self.request.DATA['comment'])
        super(IssueViewSet, self).post_save(obj, created)

    def get_queryset(self):
        qs = super(IssueViewSet, self).get_queryset()
        qs = qs.filter(project__members=self.request.user)
        return qs.distinct()


class SeverityViewSet(ModelListViewSet):
    queryset = Severity.objects.all()
    serializer_class = SeveritySerializer
    permission_classes = (IsAuthenticated,)
    filter_fields = ('project',)

    def get_queryset(self):
        qs = super(SeverityViewSet, self).get_queryset()
        qs = qs.filter(project__members=self.request.user)
        return qs.distinct()


#class SeverityDetail(generics.RetrieveUpdateDestroyAPIView):
#    model = Severity
#    serializer_class = SeveritySerializer
#    permission_classes = (IsAuthenticated, SeverityDetailPermission,)

class IssueStatusViewSet(ModelListViewSet):
    queryset = IssueStatus.objects.all()

    serializer_class = IssueStatusSerializer
    filter_fields = ('project',)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        qs = super(IssueStatusViewSet, self).get_queryset()
        qs = qs.filter(project__members=self.request.user)
        return qs.distinct()


class TaskStatusViewSet(ModelListViewSet):
    model = TaskStatus
    serializer_class = TaskStatusSerializer
    permission_classes = (IsAuthenticated,)
    filter_fields = ('project',)

    def get_queryset(self):
        qs = super(TaskStatusViewSet, self).get_queryset()
        qs = qs.filter(project__members=self.request.user)
        return qs.distinct()


#class TaskStatusDetail(generics.RetrieveUpdateDestroyAPIView):
#    model = TaskStatus
#    serializer_class = TaskStatusSerializer
#    permission_classes = (IsAuthenticated, TaskStatusDetailPermission,)


class UserStoryStatusViewSet(ModelListViewSet):
    model = UserStoryStatus
    serializer_class = UserStoryStatusSerializer
    permission_classes = (IsAuthenticated,)
    filter_fields = ('project',)

    def get_queryset(self):
        qs = super(UserStoryStatusViewSet, self).get_queryset()
        qs = qs.filter(project__members=self.request.user)
        return qs.distinct()


#class UserStoryStatusDetail(generics.RetrieveUpdateDestroyAPIView):
#    model = UserStoryStatus
#    serializer_class = UserStoryStatusSerializer
#    permission_classes = (IsAuthenticated, UserStoryStatusDetailPermission,)


class PriorityViewSet(ModelListViewSet):
    model = Priority
    serializer_class = PrioritySerializer
    permission_classes = (IsAuthenticated,)
    filter_fields = ('project',)

    def get_queryset(self):
        qs = super(PriorityViewSet, self).get_queryset()
        qs = qs.filter(project__members=self.request.user)
        return qs.distinct()


#class PriorityDetail(generics.RetrieveUpdateDestroyAPIView):
#    model = Priority
#    serializer_class = PrioritySerializer
#    permission_classes = (IsAuthenticated, PriorityDetailPermission,)


class IssueTypeViewSet(ModelListViewSet):
    model = IssueType
    serializer_class = IssueTypeSerializer
    permission_classes = (IsAuthenticated,)
    filter_fields = ('project',)

    def get_queryset(self):
        qs = super(IssueTypeViewSet, self).get_queryset()
        qs = qs.filter(project__members=self.request.user)
        return qs.distinct()

#class IssueTypeDetail(generics.RetrieveUpdateDestroyAPIView):
#    model = IssueType
#    serializer_class = IssueTypeSerializer
#    permission_classes = (IsAuthenticated, IssueTypeDetailPermission,)


class PointsViewSet(ModelListViewSet):
    model = Points
    serializer_class = PointsSerializer
    permission_classes = (IsAuthenticated,)
    filter_fields = ('project',)

    def get_queryset(self):
        qs = super(PointsViewSet, self).get_queryset()
        qs = qs.filter(project__members=self.request.user)
        return qs.distinct()


#class PointsDetail(generics.RetrieveUpdateDestroyAPIView):
#    model = Points
#    serializer_class = PointsSerializer
#    permission_classes = (IsAuthenticated, PointsDetailPermission,)
