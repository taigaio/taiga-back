# -*- coding: utf-8 -*-
import uuid

from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.views import login as auth_login, logout as auth_logout
from django.conf import settings
from django.db.models import Q
from django import http

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, generics, viewsets

import django_filters
from haystack import query, inputs
from djmail.template_mail import MagicMailBuilder

from greenmine.base.serializers import (LoginSerializer, UserLogged,
                                        UserSerializer, RoleSerializer,
                                        SearchSerializer)

from greenmine.base.models import User, Role
from greenmine.base import exceptions as excp
from greenmine.scrum import models


class RolesViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = RoleSerializer

    def list(self, request, pk=None):
        queryset = Role.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            role = Role.objects.get(pk=pk)
        except Role.DoesNotExist:
            raise excp.NotFound()

        serializer = self.serializer_class(role)
        return Response(serializer.data)


class UsersViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def get_list_queryset(self):
        own_projects = (models.Project.objects
                            .filter(members=self.request.user))

        project = self.request.QUERY_PARAMS.get('project', None)
        if project is not None:
            own_projects = own_projects.filter(pk=project)

        queryset = (User.objects.filter(projects__in=own_projects)
                        .order_by('username').distinct())

        return queryset

    def list(self, request, pk=None):
        queryset = self.get_list_queryset()
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        return Response({})

    @action(methods=["POST"], permission_classes=[])
    def login(self, request, pk=None):
        username = request.DATA.get('username', None)
        password = request.DATA.get('password', None)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail": "Invalid username or password"},
                                            status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({"detail": "Invalid username or password"},
                                            status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        login(request, user)

        serializer = UserSerializer(user)
        response_data = serializer.data
        response_data["token"] = request.session.session_key

        return Response(response_data)

    @action(methods=["POST"], permission_classes=[])
    def password_recovery(self, request, pk=None):
        username_or_email = request.DATA.get('username', None)

        if not username_or_email:
            return Response({"detail": "Invalid username or password"}, status.HTTP_400_BAD_REQUEST)

        try:
            queryset = User.objects.all()
            user = queryset.get(Q(username=username_or_email) |
                                    Q(email=username_or_email))
        except User.DoesNotExist:
            return Response({"detail": "Invalid username or password"}, status.HTTP_400_BAD_REQUEST)

        user.token = str(uuid.uuid1())
        user.save(update_fields=["token"])

        mbuilder = MagicMailBuilder()
        email = mbuilder.password_recovery(user.email, {"user": user})

        return Response({"detail": "Mail sended successful!"})

    @action(methods=["GET", "POST"])
    def logout(self, request, pk=None):
        logout(request)
        return Response()


class Search(viewsets.ViewSet):
    def list(self, request, **kwargs):
        text = request.QUERY_PARAMS.get('text', "")
        project_id = request.QUERY_PARAMS.get('project', None)

        try:
            project = self._get_project(project_id)
        except models.Project.DoesNotExist:
            raise excp.PermissionDenied({"detail": "Wrong project id"})

        #if not text:
        #    raise excp.BadRequest("text parameter must be contains text")

        queryset = query.SearchQuerySet()
        queryset = queryset.filter(text=inputs.AutoQuery(text))
        queryset = queryset.filter(project_id=project_id)

        return_data = SearchSerializer(queryset)
        return Response(return_data.data)

    def _get_project(self, project_id):
        own_projects = (models.Project.objects
                            .filter(members=self.request.user))

        return own_projects.get(pk=project_id)
