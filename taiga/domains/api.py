# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
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

from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from taiga.base.api import GenericViewSet
from taiga.base.api import ListModelMixin
from taiga.base.api import UpdateModelMixin
from taiga.base import exceptions as exc

from .base import get_active_domain
from .serializers import DomainSerializer
from .serializers import DomainMemberSerializer
from .permissions import DomainPermission
from .permissions import DomainMembersPermission
from .models import Domain
from .models import DomainMember


class DomainViewSet(UpdateModelMixin, GenericViewSet):
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

    def update(self, request, *args, **kwargs):
        raise exc.NotSupported()

    def partial_update(self, request, *args, **kwargs):
        raise exc.NotSupported()

    def create(self, request, **kwargs):
        self.kwargs['pk'] = request.domain.pk
        return super().update(request, pk=request.domain.pk, **kwargs)


class DomainMembersViewSet(ListModelMixin, UpdateModelMixin, GenericViewSet):
    permission_classes = (IsAuthenticated, DomainMembersPermission,)
    serializer_class = DomainMemberSerializer
    queryset = DomainMember.objects.all()

    def get_queryset(self):
        domain = get_active_domain()
        qs = super().get_queryset()
        return qs.filter(domain=domain).distinct()
