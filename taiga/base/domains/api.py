# Copyright 2014 Andrey Antukh <niwi@niwi.be>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# y ou may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from django.http import Http404

from taiga.base.api import ModelCrudViewSet, UpdateModelMixin

from .base import get_active_domain
from .serializers import DomainSerializer, DomainMemberSerializer
from .permissions import DomainMembersPermission, DomainPermission
from .models import DomainMember, Domain


class DomainViewSet(UpdateModelMixin, viewsets.GenericViewSet):
    permission_classes = (DomainPermission,)
    serializer_class = DomainSerializer
    queryset = Domain.objects.all()

    def list(self, request, **kwargs):
        domain_data = DomainSerializer(request.domain).data
        if request.domain.user_is_normal_user(request.user):
            domain_data['projects'] = None
        elif request.user.is_anonymous():
            domain_data['projects'] = None
        return Response(domain_data)

    def update(self, request, **kwargs):
        raise Http404

    def create(self, request, **kwargs):
        self.kwargs['pk'] = request.domain.pk
        return super().update(request, pk=request.domain.pk, **kwargs)


class DomainMembersViewSet(ModelCrudViewSet):
    permission_classes = (IsAuthenticated, DomainMembersPermission,)
    serializer_class = DomainMemberSerializer

    def get_queryset(self):
        return DomainMember.objects.filter(domain=get_active_domain()).distinct()
