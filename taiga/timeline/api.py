# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from taiga.base import response
from taiga.base.api import ReadOnlyListViewSet

from . import serializers
from . import service
from . import permissions


class TimelineViewSet(ReadOnlyListViewSet):
    serializer_class = serializers.TimelineSerializer

    content_type = None

    def get_content_type(self):
        app_name, model = self.content_type.split(".", 1)
        return ContentType.objects.get_by_natural_key(app_name, model)

    def get_queryset(self):
        ct = self.get_content_type()
        model_cls = ct.model_class()

        qs = model_cls.objects.all()
        filtered_qs = self.filter_queryset(qs)
        return filtered_qs

    def response_for_queryset(self, queryset):
        # Switch between paginated or standard style responses
        page = self.paginate_queryset(queryset)
        if page is not None:
            user_ids = list(set([obj.data.get("user", {}).get("id", None) for obj in page.object_list]))
            User = get_user_model()
            users = {u.id: u for u in User.objects.filter(id__in=user_ids)}

            for obj in page.object_list:
                user_id = obj.data.get("user", {}).get("id", None)
                obj._prefetched_user = users.get(user_id, None)

            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(queryset, many=True)

        return response.Ok(serializer.data)

    # Just for restframework! Because it raises
    # 404 on main api root if this method not exists.
    def list(self, request):
        return response.NotFound()

    def get_timeline(self, obj):
        raise NotImplementedError

    def retrieve(self, request, pk):
        obj = self.get_object()
        self.check_permissions(request, "retrieve", obj)

        qs = self.get_timeline(obj)

        if request.GET.get("only_relevant", None) is not None:
            qs = qs.exclude(Q(event_type=["issues.issue.change",
                                          "tasks.task.change",
                                          "userstories.userstory.change",
                                          "epics.epic.change",
                                          "wiki.wikipage.change"]),
                            Q(data__values_diff={}) |
                            Q(data__values_diff__attachments__new=[]))

            qs = qs.exclude(event_type__in=["issues.issue.delete",
                                            "tasks.task.delete",
                                            "userstories.userstory.delete",
                                            "epics.epic.delete",
                                            "wiki.wikipage.delete",
                                            "projects.project.change"])

        return self.response_for_queryset(qs)


class ProfileTimeline(TimelineViewSet):
    content_type = settings.AUTH_USER_MODEL.lower()
    permission_classes = (permissions.UserTimelinePermission,)

    def get_timeline(self, user):
        return service.get_profile_timeline(user, accessing_user=self.request.user)


class UserTimeline(TimelineViewSet):
    content_type = settings.AUTH_USER_MODEL.lower()
    permission_classes = (permissions.UserTimelinePermission,)

    def get_timeline(self, user):
        return service.get_user_timeline(user, accessing_user=self.request.user)


class ProjectTimeline(TimelineViewSet):
    content_type = "projects.project"
    permission_classes = (permissions.ProjectTimelinePermission,)

    def get_timeline(self, project):
        return service.get_project_timeline(project, accessing_user=self.request.user)
