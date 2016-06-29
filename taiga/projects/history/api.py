# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
from django.utils.translation import ugettext as _
from django.utils import timezone

from taiga.base import response
from taiga.base.decorators import detail_route
from taiga.base.api import ReadOnlyListViewSet
from taiga.mdrender.service import render as mdrender

from . import permissions
from . import serializers
from . import services


class HistoryViewSet(ReadOnlyListViewSet):
    serializer_class = serializers.HistoryEntrySerializer

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
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(queryset, many=True)

        return response.Ok(serializer.data)

    @detail_route(methods=['get'])
    def comment_versions(self, request, pk):
        obj = self.get_object()
        history_entry_id = request.QUERY_PARAMS.get('id', None)
        history_entry = services.get_history_queryset_by_model_instance(obj).filter(id=history_entry_id).first()

        self.check_permissions(request, 'comment_versions', history_entry)

        if history_entry is None:
            return response.NotFound()

        history_entry.attach_user_info_to_comment_versions()
        return response.Ok(history_entry.comment_versions)

    @detail_route(methods=['post'])
    def edit_comment(self, request, pk):
        obj = self.get_object()
        history_entry_id = request.QUERY_PARAMS.get('id', None)
        history_entry = services.get_history_queryset_by_model_instance(obj).filter(id=history_entry_id).first()
        obj = services.get_instance_from_key(history_entry.key)
        comment = request.DATA.get("comment", None)

        self.check_permissions(request, 'edit_comment', history_entry)

        if history_entry is None:
            return response.NotFound()

        if comment is None:
            return response.BadRequest({"error": _("comment is required")})

        if history_entry.delete_comment_date or history_entry.delete_comment_user:
            return response.BadRequest({"error": _("deleted comments can't be edited")})

        # comment_versions can be None if there are no historic versions of the comment
        comment_versions = history_entry.comment_versions or []
        comment_versions.append({
            "date": history_entry.created_at,
            "comment": history_entry.comment,
            "comment_html": history_entry.comment_html,
            "user": {
                "id": request.user.pk,
            }
        })

        history_entry.edit_comment_date = timezone.now()
        history_entry.comment = comment
        history_entry.comment_html = mdrender(obj.project, comment)
        history_entry.comment_versions = comment_versions
        history_entry.save()
        return response.Ok()

    @detail_route(methods=['post'])
    def delete_comment(self, request, pk):
        obj = self.get_object()
        history_entry_id = request.QUERY_PARAMS.get('id', None)
        history_entry = services.get_history_queryset_by_model_instance(obj).filter(id=history_entry_id).first()

        self.check_permissions(request, 'delete_comment', history_entry)

        if history_entry is None:
            return response.NotFound()

        if history_entry.delete_comment_date or history_entry.delete_comment_user:
            return response.BadRequest({"error": _("Comment already deleted")})

        history_entry.delete_comment_date = timezone.now()
        history_entry.delete_comment_user = {"pk": request.user.pk, "name": request.user.get_full_name()}
        history_entry.save()
        return response.Ok()

    @detail_route(methods=['post'])
    def undelete_comment(self, request, pk):
        obj = self.get_object()
        history_entry_id = request.QUERY_PARAMS.get('id', None)
        history_entry = services.get_history_queryset_by_model_instance(obj).filter(id=history_entry_id).first()

        self.check_permissions(request, 'undelete_comment', history_entry)

        if history_entry is None:
            return response.NotFound()

        if not history_entry.delete_comment_date and not history_entry.delete_comment_user:
            return response.BadRequest({"error": _("Comment not deleted")})

        history_entry.delete_comment_date = None
        history_entry.delete_comment_user = None
        history_entry.save()
        return response.Ok()

    # Just for restframework! Because it raises
    # 404 on main api root if this method not exists.
    def list(self, request):
        return response.NotFound()

    def retrieve(self, request, pk):
        obj = self.get_object()
        self.check_permissions(request, "retrieve", obj)
        qs = services.get_history_queryset_by_model_instance(obj)
        qs = services.prefetch_owners_in_history_queryset(qs)
        return self.response_for_queryset(qs)


class UserStoryHistory(HistoryViewSet):
    content_type = "userstories.userstory"
    permission_classes = (permissions.UserStoryHistoryPermission,)


class TaskHistory(HistoryViewSet):
    content_type = "tasks.task"
    permission_classes = (permissions.TaskHistoryPermission,)


class IssueHistory(HistoryViewSet):
    content_type = "issues.issue"
    permission_classes = (permissions.IssueHistoryPermission,)


class WikiHistory(HistoryViewSet):
    content_type = "wiki.wikipage"
    permission_classes = (permissions.WikiHistoryPermission,)
