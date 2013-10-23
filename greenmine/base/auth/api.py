# -*- coding: utf-8 -*-

from django.db.models.loading import get_model
from django.contrib.auth import logout, login, authenticate

from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status, viewsets

from greenmine.base import exceptions as exc
from greenmine.base import auth

from greenmine.base.users.models import User, Role
from greenmine.base.users.serializers import UserSerializer


class AuthViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)

    def create(self, request, **kwargs):
        username = request.DATA.get('username', None)
        password = request.DATA.get('password', None)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise exc.BadRequest("Invalid username or password")

        if not user.check_password(password):
            raise exc.BadRequest("Invalid username or password")

        serializer = UserSerializer(user)
        response_data = serializer.data
        response_data["auth_token"] = auth.get_token_for_user(user)
        return Response(response_data, status=status.HTTP_200_OK)
