# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import list_route, action
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from greenmine.base import filters
from greenmine.base import exceptions as exc
from greenmine.base.permissions import has_project_perm
from greenmine.base.api import ModelCrudViewSet
from greenmine.base.notifications.api import NotificationSenderMixin
from greenmine.projects.permissions import AttachmentPermission
from greenmine.projects.serializers import AttachmentSerializer
from greenmine.projects.models import Attachment
from greenmine.projects.models import Project

from . import serializers
from . import models
from . import permissions

import reversion



class UserStoryAttachmentViewSet(ModelCrudViewSet):
    model = Attachment
    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated, AttachmentPermission,)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ["project", "object_id"]

    def get_queryset(self):
        ct = ContentType.objects.get_for_model(models.UserStory)
        qs = super().get_queryset()
        qs = qs.filter(content_type=ct)
        return qs.distinct()

    def pre_save(self, obj):
        if not obj.id:
            obj.content_type = ContentType.objects.get_for_model(models.UserStory)
            obj.owner = self.request.user

        super().pre_save(obj)

    def pre_conditions_on_save(self, obj):
        super().pre_conditions_on_save(obj)

        if (obj.project.owner != self.request.user and
                obj.project.memberships.filter(user=self.request.user).count() == 0):
            raise exc.PreconditionError("You must not add a new user story attachment "
                                        "to this project.")


class UserStoryViewSet(NotificationSenderMixin, ModelCrudViewSet):
    model = models.UserStory
    serializer_class = serializers.UserStorySerializer
    permission_classes = (IsAuthenticated, permissions.UserStoryPermission)
    filter_backends = (filters.IsProjectMemberFilterBackend,)
    filter_fields = ['project', 'milestone', 'milestone__isnull']

    create_notification_template = "create_userstory_notification"
    update_notification_template = "update_userstory_notification"
    destroy_notification_template = "destroy_userstory_notification"

    @list_route(methods=["POST"])
    def bulk_create(self, request):
        bulk_stories = request.DATA.get('bulkStories', None)
        if bulk_stories is None:
            raise ParseError(detail='You need bulkStories data')

        project_id = request.DATA.get('projectId', None)
        if project_id is None:
            raise ParseError(detail='You need projectId data')

        project = get_object_or_404(Project, id=project_id)

        if not has_project_perm(request.user, project, 'add_userstory'):
            raise PermissionDenied("You don't have permision to create user stories")

        result_stories = []
        bulk_stories = bulk_stories.split("\n")
        for bulk_story in bulk_stories:
            bulk_story = bulk_story.strip()
            if len(bulk_story) > 0:
                result_stories.append(models.UserStory.objects.create(subject=bulk_story,
                                                                      project=project,
                                                                      owner=request.user,
                                                                      status=project.default_us_status))

        data = map(lambda x: serializers.UserStorySerializer(x).data, result_stories)
        return Response(data)

    def pre_save(self, obj):
        if not obj.id:
            obj.owner = self.request.user

        super().pre_save(obj)

    def pre_conditions_on_save(self, obj):
        super().pre_conditions_on_save(obj)

        if (obj.project.owner != self.request.user and
                obj.project.memberships.filter(user=self.request.user).count() == 0):
            raise exc.PreconditionError("You must not add a new user story to this "
                                        "project.")

        if obj.milestone and obj.milestone.project != obj.project:
            raise exc.PreconditionError("You must not add a new user story to this "
                                        "milestone.")

        if obj.status and obj.status.project != obj.project:
            raise exc.PreconditionError("You must not use a status from other project.")

    def post_save(self, obj, created=False):
        with reversion.create_revision():
            if "comment" in self.request.DATA:
                # Update the comment in the last version
                reversion.set_comment(self.request.DATA['comment'])

        super().post_save(obj, created)
