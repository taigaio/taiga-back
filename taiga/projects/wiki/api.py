# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.translation import gettext as _

from taiga.base import exceptions as exc
from taiga.base import filters
from taiga.base import response
from taiga.base.api import ModelCrudViewSet
from taiga.base.api import ModelListViewSet
from taiga.base.api.mixins import BlockedByProjectMixin
from taiga.base.api.utils import get_object_or_404
from taiga.base.decorators import list_route

from taiga.mdrender.service import render as mdrender

from taiga.projects.history.mixins import HistoryResourceMixin
from taiga.projects.history.services import take_snapshot
from taiga.projects.models import Project
from taiga.projects.notifications.mixins import WatchedResourceMixin
from taiga.projects.notifications.mixins import WatchersViewSetMixin
from taiga.projects.notifications.services import analize_object_for_watchers
from taiga.projects.notifications.services import send_notifications
from taiga.projects.occ import OCCResourceMixin

from . import models
from . import permissions
from . import serializers
from . import validators
from . import utils as wiki_utils


class WikiViewSet(OCCResourceMixin, HistoryResourceMixin, WatchedResourceMixin,
                  BlockedByProjectMixin, ModelCrudViewSet):

    model = models.WikiPage
    serializer_class = serializers.WikiPageSerializer
    validator_class = validators.WikiPageValidator
    permission_classes = (permissions.WikiPagePermission,)
    filter_backends = (filters.CanViewWikiPagesFilterBackend,)
    filter_fields = ("project", "slug")
    queryset = models.WikiPage.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        qs = wiki_utils.attach_extra_info(qs, user=self.request.user)
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


class WikiLinkViewSet(BlockedByProjectMixin, ModelCrudViewSet):
    model = models.WikiLink
    serializer_class = serializers.WikiLinkSerializer
    validator_class = validators.WikiLinkValidator
    permission_classes = (permissions.WikiLinkPermission,)
    filter_backends = (filters.CanViewWikiPagesFilterBackend,)
    filter_fields = ["project"]

    def post_save(self, obj, created=False):
        if created:
            self._create_wiki_page_when_create_wiki_link_if_not_exist(self.request, obj)
        super().pre_save(obj)

    def _create_wiki_page_when_create_wiki_link_if_not_exist(self, request, wiki_link):
        try:
            self.check_permissions(request, "create_wiki_page", wiki_link)
        except exc.PermissionDenied:
            # Create only the wiki link because the user doesn't have permission.
            pass
        else:
            # Create the wiki link and the wiki page if not exist.
            wiki_page, created = models.WikiPage.objects.get_or_create(
                slug=wiki_link.href,
                project=wiki_link.project,
                defaults={"owner": self.request.user, "last_modifier": self.request.user})

            if created:
                # Create the new history entry, Set watcher for the new wiki page
                # and send notifications about the new page created
                history = take_snapshot(wiki_page, user=self.request.user)
                analize_object_for_watchers(wiki_page, history.comment, history.owner)
                send_notifications(wiki_page, history=history)
