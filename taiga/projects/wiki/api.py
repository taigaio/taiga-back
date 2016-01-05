# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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

from django.utils.translation import ugettext as _

from taiga.base.api.permissions import IsAuthenticated

from taiga.base import filters
from taiga.base import exceptions as exc
from taiga.base import response
from taiga.base.api import ModelCrudViewSet, ModelListViewSet
from taiga.base.api.utils import get_object_or_404
from taiga.base.decorators import list_route
from taiga.projects.models import Project
from taiga.mdrender.service import render as mdrender

from taiga.projects.notifications.mixins import WatchedResourceMixin, WatchersViewSetMixin
from taiga.projects.history.mixins import HistoryResourceMixin
from taiga.projects.occ import OCCResourceMixin


from . import models
from . import permissions
from . import serializers


class WikiViewSet(OCCResourceMixin, HistoryResourceMixin, WatchedResourceMixin, ModelCrudViewSet):
    model = models.WikiPage
    serializer_class = serializers.WikiPageSerializer
    permission_classes = (permissions.WikiPagePermission,)
    filter_backends = (filters.CanViewWikiPagesFilterBackend,)
    filter_fields = ("project", "slug")
    queryset = models.WikiPage.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        qs = self.attach_watchers_attrs_to_queryset(qs)
        return qs

    @list_route(methods=["GET"])
    def by_slug(self, request):
        slug = request.QUERY_PARAMS.get("slug", None)
        project_id = request.QUERY_PARAMS.get("project", None)
        wiki_page = get_object_or_404(models.WikiPage, slug=slug, project_id=project_id)
        return self.retrieve(request, pk=wiki_page.pk)

    @list_route(methods=["POST"])
    def render(self, request, **kwargs):
        content = request.DATA.get("content", None)
        project_id = request.DATA.get("project_id", None)

        if not content:
            raise exc.WrongArguments({"content": _("'content' parameter is mandatory")})

        if not project_id:
            raise exc.WrongArguments({"project_id": _("'project_id' parameter is mandatory")})

        project = get_object_or_404(Project, pk=project_id)

        self.check_permissions(request, "render", project)

        data = mdrender(project, content)
        return response.Ok({"data": data})

    def pre_save(self, obj):
        if not obj.owner:
            obj.owner = self.request.user
        obj.last_modifier = self.request.user

        super().pre_save(obj)


class WikiWatchersViewSet(WatchersViewSetMixin, ModelListViewSet):
    permission_classes = (permissions.WikiPageWatchersPermission,)
    resource_model = models.WikiPage


class WikiLinkViewSet(ModelCrudViewSet):
    model = models.WikiLink
    serializer_class = serializers.WikiLinkSerializer
    permission_classes = (permissions.WikiLinkPermission,)
    filter_backends = (filters.CanViewWikiPagesFilterBackend,)
    filter_fields = ["project"]
