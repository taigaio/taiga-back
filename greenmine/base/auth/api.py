# -*- coding: utf-8 -*-

from django.db.models.loading import get_model
from django.contrib.auth import logout, login, authenticate
from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status, viewsets
from rest_framework.decorators import list_route

from greenmine.base.models import SiteMember
from greenmine.base.sites import get_active_site
from greenmine.base.users.models import User, Role
from greenmine.base.users.serializers import UserSerializer
from greenmine.base import exceptions as exc
from greenmine.base import auth

from .serializers import (PublicRegisterSerializer,
                          PrivateRegisterSerializer,
                          PrivateGenericRegisterSerializer,
                          PrivateRegisterExistingSerializer)


class AuthViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)

    def _create_response(self, user):
        serializer = UserSerializer(user)
        response_data = serializer.data
        response_data["auth_token"] = auth.get_token_for_user(user)
        return response_data

    def _create_site_member(self, user):
        site = get_active_site()

        if SiteMember.objects.filter(site=site, user=user).count() == 0:
            site_member = SiteMember(site=site, user=user, email=user.email,
                                     is_owner=False, is_staff=False)
            site_member.save()

    def _send_public_register_email(self, user):
        context = {"user": user}

        mbuilder = MagicMailBuilder()
        email = mbuilder.public_register_user(user.email, context)
        email.send()

    def _public_register(self, request):
        if not request.site.public_register:
            raise exc.BadRequest("Public register is disabled for this site.")

        serializer = PublicRegisterSerializer(data=request.DATA)
        if not serializer.is_valid():
            raise exc.BadRequest(serializer.errors)

        data = serializer.data

        user = User(username=data["username"],
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    email=data["email"])
        user.set_password(data["password"])
        user.save()

        self._create_site_member(user)

        #self._send_public_register_email(user)

        response_data = self._create_response(user)
        return Response(response_data, status=status.HTTP_201_CREATED)

    def _send_private_register_email(self, user, **kwargs):
        context = {"user": user}
        context.update(kwargs)

        mbuilder = MagicMailBuilder()
        email = mbuilder.private_register_user(user.email, context)
        email.send()

    def _private_register(self, request):
        base_serializer = PrivateGenericRegisterSerializer(data=request.DATA)
        if not base_serializer.is_valid():
            raise exc.BadRequest(base_serializer.errors)

        membership_model = get_model("projects", "Membership")
        try:
            membership = membership_model.objects.get(token=base_serializer.data["token"])
        except membership_model.DoesNotExist as e:
            raise exc.BadRequest("Invalid token") from e

        if base_serializer.data["existing"]:
            serializer = PrivateRegisterExistingSerializer(data=request.DATA)
            if not serializer.is_valid():
                raise exc.BadRequest(serializer.errors)

            user = get_object_or_404(User, username=serializer.data["username"])
            if not user.check_password(serializer.data["password"]):
                raise exc.BadRequest({"password": "Incorrect password"})

        else:
            serializer = PrivateRegisterSerializer(data=request.DATA)
            if not serializer.is_valid():
                raise exc.BadRequest(serializer.errors)

            data = serializer.data
            user = User(username=data["username"],
                        first_name=data["first_name"],
                        last_name=data["last_name"],
                        email=data["email"])
            user.set_password(data["password"])
            user.save()

        self._create_site_member(user)

        membership.user = user
        membership.save()

        #self._send_private_register_email(user, membership=membership)

        response_data = self._create_response(user)
        return Response(response_data, status=status.HTTP_201_CREATED)

    @list_route(methods=["POST"], permission_classes=[AllowAny])
    def register(self, request, **kwargs):
        type = request.DATA.get("type", None)
        if type == "public":
            return self._public_register(request)
        elif type == "private":
            return self._private_register(request)

        raise exc.BadRequest("invalid register type")

    def create(self, request, **kwargs):
        username = request.DATA.get('username', None)
        password = request.DATA.get('password', None)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise exc.BadRequest("Invalid username or password")

        if not user.check_password(password):
            raise exc.BadRequest("Invalid username or password")

        response_data = self._create_response(user)
        return Response(response_data, status=status.HTTP_200_OK)
