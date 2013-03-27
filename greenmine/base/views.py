# -*- coding: utf-8 -*-

from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.views import login as auth_login, logout as auth_logout
from django import http

from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.response import Response

from greenmine.base.serializers import LoginSerializer, UserLogged


class ApiRoot(APIView):
    def get(self, request, format=None):
        return Response({
            'login': reverse('login', request=request, format=format),
            'logout': reverse('logout', request=request, format=format),
            'projects': reverse('project-list', request=request, format=format),
            'milestones': reverse('milestone-list', request=request, format=format),
            'user-stories': reverse('user-story-list', request=request, format=format),
            'changes': reverse('change-list', request=request, format=format),
            'change-attachments': reverse('change-attachment-list', request=request, format=format),
            'tasks': reverse('task-list', request=request, format=format),
            'severities': reverse('severity-list', request=request, format=format),
            'issue-status': reverse('issue-status-list', request=request, format=format),
            'task-status': reverse('task-status-list', request=request, format=format),
            'user-story-status': reverse('user-story-status-list', request=request, format=format),
            'priorities': reverse('priority-list', request=request, format=format),
            'issue-types': reverse('issue-type-list', request=request, format=format),
            'points': reverse('points-list', request=request, format=format),
        })


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
                }))

                return http.HttpResponse(JSONRenderer().render(return_data.data),
                                         content_type="application/json",
                                         status=201)
        except User.DoesNotExist:
            pass

        return http.HttpResponseBadRequest()


class Logout(APIView):
    def post(self, request, format=None):
        logout(request)
        return http.HttpResponse()
