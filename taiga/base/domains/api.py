# -*- coding: utf-8 -*-

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from django.http import Http404

from taiga.base.api import ModelCrudViewSet, UpdateModelMixin
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
    queryset = DomainMember.objects.all()
