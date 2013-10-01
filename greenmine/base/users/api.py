# -*- coding: utf-8 -*-

from django.db.models.loading import get_model
from django.contrib.auth import logout, login, authenticate

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, viewsets

from djmail.template_mail import MagicMailBuilder

from greenmine.base import exceptions as excp

from .serializers import (
    LoginSerializer,
    UserLogged,
    UserSerializer,
    RoleSerializer,
)

from .models import User, Role

import uuid


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
        project_model = get_model("scrum", "Project")
        own_projects = (project_model.objects
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
    def password_recovery(self, request, pk=None):
        username_or_email = request.DATA.get('username', None)

        if not username_or_email:
            return Response({"detail": "Invalid username or password"},
                            status.HTTP_400_BAD_REQUEST)

        try:
            queryset = User.objects.all()
            user = queryset.get(Q(username=username_or_email) |
                                    Q(email=username_or_email))
        except User.DoesNotExist:
            return Response({"detail": "Invalid username or password"},
                            status.HTTP_400_BAD_REQUEST)

        user.token = str(uuid.uuid1())
        user.save(update_fields=["token"])

        mbuilder = MagicMailBuilder()
        email = mbuilder.password_recovery(user.email, {"user": user})

        return Response({"detail": "Mail sended successful!"})


class LoginViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)

    def create(self, request, **kwargs):
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


class LogoutViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def list(self, request, **kwargs):
        return self.logout(request)

    def create(self, request, **kwargs):
        return self.logout(request)

    def logout(self, request):
        logout(request)
        return Response({})
