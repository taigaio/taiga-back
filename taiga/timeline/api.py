# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
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

from django.contrib.contenttypes.models import ContentType

from taiga.base import response
from taiga.base.api.utils import get_object_or_404
from taiga.base.api import ReadOnlyListViewSet

from . import serializers
from . import service
from . import permissions


class TimelineViewSet(ReadOnlyListViewSet):
    serializer_class = serializers.TimelineSerializer

    content_type = None

    def get_content_type(self):
        app_name, model = self.content_type.split(".", 1)
        return get_object_or_404(ContentType, app_label=app_name, model=model)

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
        return self.response_for_queryset(qs)


class ProfileTimeline(TimelineViewSet):
    content_type = "users.user"
    permission_classes = (permissions.UserTimelinePermission,)

    def get_timeline(self, user):
        return service.get_profile_timeline(user, accessing_user=self.request.user)


class UserTimeline(TimelineViewSet):
    content_type = "users.user"
    permission_classes = (permissions.UserTimelinePermission,)

    def get_timeline(self, user):
        return service.get_user_timeline(user, accessing_user=self.request.user)


class ProjectTimeline(TimelineViewSet):
    content_type = "projects.project"
    permission_classes = (permissions.ProjectTimelinePermission,)

    def get_timeline(self, project):
        return service.get_project_timeline(project, accessing_user=self.request.user)
