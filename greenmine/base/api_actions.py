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
        return HttpResponse()

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(Login, self).dispatch(*args, **kwargs)
