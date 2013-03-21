from django.views.generic.base import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse

from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User

import json


class Login(View):
    def post(self, request):
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        print username
        print password

        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                user = authenticate(username=username, password=password)
                login(request, user)
                return HttpResponse(json.dumps({'token': request.session.session_key, 'error': False}))
        except User.DoesNotExist:
            pass

        return HttpResponse(json.dumps({'error': True}))

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
