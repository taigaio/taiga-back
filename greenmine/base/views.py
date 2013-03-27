# -*- coding: utf-8 -*-

import datetime
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.views.generic.base import View
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User
from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.utils.decorators import method_decorator
from django.utils import timezone
from django import http

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(('GET',))
def api_root(request, format=None):
    return Response({
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


class LazyEncoder(DjangoJSONEncoder):
    """
    JSON encoder class for encode correctly traduction strings.
    Is for ajax response encode.
    """

    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        elif isinstance(obj, datetime.datetime):
            obj = timezone.localtime(obj)
        return super(LazyEncoder, self).default(obj)


def request_json_to_dict(request):
    try:
        body = request.body.decode('utf-8')
        return json.loads(body)
    except Exception:
        return {}


def to_json(data):
    return json.dumps(data)


class Login(View):
    def post(self, request):
        data = request_json_to_dict(request)

        username = data.get('username', None)
        password = data.get('password', None)

        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                user = authenticate(username=username, password=password)
                login(request, user)
                return http.HttpResponse(to_json({'token': request.session.session_key}))
        except User.DoesNotExist:
            pass

        return http.HttpResponseBadRequest()

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(Login, self).dispatch(*args, **kwargs)


class Logout(View):
    def post(self, request):
        logout(request)
        return http.HttpResponse()

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(Login, self).dispatch(*args, **kwargs)
