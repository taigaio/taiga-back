# -*- coding: utf-8 -*-

from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.views import login as auth_login, logout as auth_logout
from django import http

from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework import generics

from haystack import query, inputs

from greenmine.base.serializers import LoginSerializer, UserLogged, UserSerializer, RoleSerializer
from greenmine.base.serializers import SearchSerializer
from greenmine.base.models import User, Role
from greenmine.scrum import models
from django.conf import settings

import django_filters


class ApiRoot(APIView):
    def get(self, request, format=None):
        return Response({
            'login': reverse('login', request=request, format=format),
            'logout': reverse('logout', request=request, format=format),
            'projects': reverse('project-list', request=request, format=format),
            'milestones': reverse('milestone-list', request=request, format=format),
            'user-stories': reverse('user-story-list', request=request, format=format),
            'user-stories/statuses': reverse('user-story-status-list', request=request, format=format),
            'user-stories/points': reverse('points-list', request=request, format=format),
            'issues/attachments': reverse('issues-attachment-list', request=request, format=format),
            'issues/statuses': reverse('issues-status-list', request=request, format=format),
            'issues/types': reverse('issues-type-list', request=request, format=format),
            'issues': reverse('issues-list', request=request, format=format),
            'tasks': reverse('tasks-list', request=request, format=format),
            'tasks/statuses': reverse('tasks-status-list', request=request, format=format),
            'tasks/attachments': reverse('tasks-attachment-list', request=request, format=format),
            'severities': reverse('severity-list', request=request, format=format),
            'priorities': reverse('priority-list', request=request, format=format),
            'documents': reverse('document-list', request=request, format=format),
            'questions': reverse('question-list', request=request, format=format),
            'wiki/pages': reverse('wiki-page-list', request=request, format=format),
            'users': reverse('user-list', request=request, format=format),
            'roles': reverse('user-roles', request=request, format=format),
            'search': reverse('search', request=request, format=format),
        })


class RoleList(generics.ListCreateAPIView):
    model = Role
    serializer_class = RoleSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.model.objects.all()


class RoleDetail(generics.RetrieveAPIView):
    model = Role
    serializer_class = RoleSerializer
    permission_classes = (IsAuthenticated,)


class UserFilter(django_filters.FilterSet):
    class Meta:
        model = User
        fields = ['is_active']


class UserList(generics.ListCreateAPIView):
    model = User
    serializer_class = UserSerializer
    filter_class = UserFilter
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        projects = models.Project.objects.filter(members=self.request.user)

        #Project filtering
        project = self.request.QUERY_PARAMS.get('project', None)
        if project is not None:
            projects = projects.filter(id=project)

        return super(UserList, self).get_queryset().filter(projects__in=projects)\
                    .order_by('id').distinct()

    def pre_save(self, obj):
        pass


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    model = User
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

import uuid
from django.db.models import Q
from djmail.template_mail import MagicMailBuilder


class RecoveryPassword(APIView):
    def post(self, request):
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


class Login(APIView):
    def post(self, request, format=None):
        username = request.DATA.get('username', None)
        password = request.DATA.get('password', None)

        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                user = authenticate(username=username, password=password)
                login(request, user)

                return_data = LoginSerializer(UserLogged(**{
                    'token': request.session.session_key,
                    'username': request.user.username,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                    'email': request.user.email,
                    'last_login': request.user.last_login,
                    'color': request.user.color,
                    'description': request.user.description,
                    'default_language': request.user.default_language,
                    'default_timezone': request.user.default_timezone,
                    'colorize_tags': request.user.colorize_tags,
                }))

                return Response(return_data.data)
        except User.DoesNotExist:
            pass

        return Response({"detail": "Invalid username or password"}, status.HTTP_400_BAD_REQUEST)




class Logout(APIView):
    def post(self, request, format=None):
        logout(request)
        return Response()


class Search(APIView):
    def get(self, request, format=None):
        text = request.QUERY_PARAMS.get('text', None)
        project = request.QUERY_PARAMS.get('project', None)

        if text and project:
            #TODO: permission check
            queryset = query.SearchQuerySet()
            queryset = queryset.filter(text=inputs.AutoQuery(text))
            queryset = queryset.filter(project_id=project)

            return_data = SearchSerializer(queryset)
            return Response(return_data.data)

        return Response({"detail": "Parameter text can't be empty"}, status.HTTP_400_BAD_REQUEST)




