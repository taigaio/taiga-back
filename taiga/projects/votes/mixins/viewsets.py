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

from django.core.exceptions import ObjectDoesNotExist

from taiga.base import response
from taiga.base.api import viewsets
from taiga.base.api.utils import get_object_or_404
from taiga.base.decorators import detail_route

from taiga.projects.votes import serializers
from taiga.projects.votes import services
from taiga.projects.votes.utils import attach_total_voters_to_queryset, attach_is_voter_to_queryset


class VotedResourceMixin:
    # Note: Update get_queryset method:
    #           def get_queryset(self):
    #               qs = super().get_queryset()
    #               return self.attach_votes_attrs_to_queryset(qs)

    def attach_votes_attrs_to_queryset(self, queryset):
        qs = attach_total_voters_to_queryset(queryset)

        if self.request.user.is_authenticated():
            qs = attach_is_voter_to_queryset(self.request.user, qs)

        return qs

    @detail_route(methods=["POST"])
    def upvote(self, request, pk=None):
        obj = self.get_object()
        self.check_permissions(request, "upvote", obj)

        services.add_vote(obj, user=request.user)
        return response.Ok()

    @detail_route(methods=["POST"])
    def downvote(self, request, pk=None):
        obj = self.get_object()
        self.check_permissions(request, "downvote", obj)

        services.remove_vote(obj, user=request.user)
        return response.Ok()


class VotersViewSetMixin:
    # Is a ModelListViewSet with two required params: permission_classes and resource_model
    serializer_class = serializers.VoterSerializer
    list_serializer_class = serializers.VoterSerializer
    permission_classes = None
    resource_model = None

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get("pk", None)
        resource_id = kwargs.get("resource_id", None)
        resource = get_object_or_404(self.resource_model, pk=resource_id)

        self.check_permissions(request, 'retrieve', resource)

        try:
            self.object = services.get_voters(resource).get(pk=pk)
        except ObjectDoesNotExist: # or User.DoesNotExist
            return response.NotFound()

        serializer = self.get_serializer(self.object)
        return response.Ok(serializer.data)

    def list(self, request, *args, **kwargs):
        resource_id = kwargs.get("resource_id", None)
        resource = get_object_or_404(self.resource_model, pk=resource_id)

        self.check_permissions(request, 'list', resource)

        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        resource = self.resource_model.objects.get(pk=self.kwargs.get("resource_id"))
        return services.get_voters(resource)
