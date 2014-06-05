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

from django.db import transaction
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from taiga.base import filters
from taiga.base import exceptions as exc
from taiga.base.decorators import list_route
from taiga.base.decorators import action
from taiga.base.permissions import has_project_perm
from taiga.base.api import ModelCrudViewSet

from taiga.projects.notifications import WatchedResourceMixin
from taiga.projects.history import HistoryResourceMixin

from taiga.projects.models import Project
from taiga.projects.history.services import take_snapshot

from . import models
from . import permissions
from . import serializers
from . import services


class UserStoryViewSet(HistoryResourceMixin, WatchedResourceMixin, ModelCrudViewSet):
    model = models.UserStory
    serializer_class = serializers.UserStoryNeighborsSerializer
    list_serializer_class = serializers.UserStorySerializer
    permission_classes = (IsAuthenticated, permissions.UserStoryPermission)

    filter_backends = (filters.IsProjectMemberFilterBackend, filters.TagsFilter)
    retrieve_exclude_filters = (filters.TagsFilter,)
    filter_fields = ['project', 'milestone', 'milestone__isnull', 'status']

    # Specific filter used for filtering neighbor user stories
    _neighbor_tags_filter = filters.TagsFilter('neighbor_tags')

    def get_queryset(self):
        qs = self.model.objects.all()
        qs = qs.prefetch_related("points",
                                 "role_points",
                                 "role_points__points",
                                 "role_points__role")
        qs = qs.select_related("milestone", "project")
        return qs

    @list_route(methods=["POST"])
    def bulk_create(self, request, **kwargs):
        bulk_stories = request.DATA.get('bulkStories', None)
        if bulk_stories is None:
            raise exc.BadRequest(_('bulkStories parameter is mandatory'))

        project_id = request.DATA.get('projectId', None)
        if project_id is None:
            raise exc.BadRequest(_('projectId parameter is mandatory'))

        project = get_object_or_404(Project, id=project_id)

        if request.user != project.owner and not has_project_perm(request.user, project, 'add_userstory'):
            raise exc.PermissionDenied(_("You don't have permisions to create user stories."))

        service = services.UserStoriesService()
        user_stories = service.bulk_insert(project, request.user, bulk_stories,
                            callback_on_success=self.post_save)

        user_stories_serialized = self.serializer_class(user_stories, many=True)
        return Response(data=user_stories_serialized.data)

    @list_route(methods=["POST"])
    def bulk_update_order(self, request, **kwargs):
        # bulkStories should be:
        # [[1,1],[23, 2], ...]

        # TODO: Generate the histoy snaptshot when change the uss order in the backlog.
        #       Implement order with linked lists \o/.
        bulk_stories = request.DATA.get("bulkStories", None)

        if bulk_stories is None:
            raise exc.BadRequest(_("bulkStories parameter is mandatory"))

        project_id = request.DATA.get('projectId', None)
        if project_id is None:
            raise exc.BadRequest(_("projectId parameter ir mandatory"))

        project = get_object_or_404(Project, id=project_id)

        if request.user != project.owner and not has_project_perm(request.user, project, 'change_userstory'):
            raise exc.PermissionDenied(_("You don't have permisions to create user stories."))

        service = services.UserStoriesService()
        service.bulk_update_order(project, request.user, bulk_stories)

        return Response(data=None, status=status.HTTP_204_NO_CONTENT)

    @transaction.atomic
    def create(self, *args, **kwargs):
        response = super().create(*args, **kwargs)

        # Added comment to the origin (issue)
        if response.status_code == status.HTTP_201_CREATED and self.object.generated_from_issue:
            self.object.generated_from_issue.save()

            comment = _("Generate the user story [US #{ref} - "
                        "{subject}](:us:{ref} \"US #{ref} - {subject}\")")
            comment = comment.format(ref=self.object.ref, subject=self.object.subject)
            history = take_snapshot(self.object.generated_from_issue,
                                    comment=comment,
                                    user=self.request.user)

            self.send_notifications(self.object.generated_from_issue, history)

        return response

    def pre_save(self, obj):
        if not obj.id:
            obj.owner = self.request.user

        super().pre_save(obj)

    def pre_conditions_on_save(self, obj):
        super().pre_conditions_on_save(obj)

        if (obj.project.owner != self.request.user and
                obj.project.memberships.filter(user=self.request.user).count() == 0):
            raise exc.PermissionDenied(_("You don't have permissions for add/modify this user story"))

        if obj.milestone and obj.milestone.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions for add/modify this user story"))

        if obj.status and obj.status.project != obj.project:
            raise exc.PermissionDenied(_("You don't have permissions for add/modify this user story"))
