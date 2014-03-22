# -*- coding: utf-8 -*-

from django.db.models.loading import get_model
from django.db.models import Q
from django.contrib.auth import logout, login, authenticate
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status, viewsets
from taiga.base.decorators import list_route

from taiga.domains.models import DomainMember
from taiga.domains import get_active_domain
from taiga.base.users.models import User, Role
from taiga.base.users.serializers import UserSerializer
from taiga.base import exceptions as exc
from taiga.base import auth

from .serializers import (PublicRegisterSerializer,
                          PrivateRegisterSerializer,
                          PrivateGenericRegisterSerializer,
                          PrivateRegisterExistingSerializer)


class AuthViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)

    def _create_response(self, user):
        serializer = UserSerializer(user)
        response_data = serializer.data

        domain = get_active_domain()
        response_data['is_site_owner'] = domain.user_is_owner(user)
        response_data['is_site_staff'] = domain.user_is_staff(user)
        response_data["auth_token"] = auth.get_token_for_user(user)
        return response_data

    def _create_domain_member(self, user):
        domain = get_active_domain()

        if domain.members.filter(user=user).count() == 0:
            domain_member = DomainMember(domain=domain, user=user, email=user.email,
                                     is_owner=False, is_staff=False)
            domain_member.save()

    def _send_public_register_email(self, user):
        context = {"user": user}

        mbuilder = MagicMailBuilder()
        email = mbuilder.public_register_user(user.email, context)
        email.send()

    def _public_register(self, request):
        if not request.domain.public_register:
            raise exc.BadRequest(_("Public register is disabled for this domain."))

        serializer = PublicRegisterSerializer(data=request.DATA)
        if not serializer.is_valid():
            raise exc.BadRequest(serializer.errors)

        data = serializer.data

        if User.objects.filter(Q(username=data["username"]) | Q(email=data["email"])).exists():
            raise exc.BadRequest(_("This username or email is already in use."))

        user = User(username=data["username"],
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    email=data["email"])
        user.set_password(data["password"])
        user.save()

        self._create_domain_member(user)
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
            raise exc.BadRequest(_("Invalid token")) from e

        if base_serializer.data["existing"]:
            serializer = PrivateRegisterExistingSerializer(data=request.DATA)
            if not serializer.is_valid():
                raise exc.BadRequest(serializer.errors)

            user = get_object_or_404(User, username=serializer.data["username"])
            if not user.check_password(serializer.data["password"]):
                raise exc.BadRequest({"password": _("Incorrect password")})

        else:
            serializer = PrivateRegisterSerializer(data=request.DATA)
            if not serializer.is_valid():
                raise exc.BadRequest(serializer.errors)

            data = serializer.data

            if User.objects.filter(Q(username=data["username"]) | Q(email=data["email"])).exists():
                raise exc.BadRequest(_("This username or email is already in use."))

            user = User(username=data["username"],
                        first_name=data["first_name"],
                        last_name=data["last_name"],
                        email=data["email"])
            user.set_password(data["password"])
            user.save()

        self._create_domain_member(user)

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

        raise exc.BadRequest(_("invalid register type"))

    # Login view: /api/v1/auth
    def create(self, request, **kwargs):
        username = request.DATA.get('username', None)
        password = request.DATA.get('password', None)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise exc.BadRequest(_("Invalid username or password"))

        if not user.check_password(password):
            raise exc.BadRequest(_("Invalid username or password"))

        response_data = self._create_response(user)
        return Response(response_data, status=status.HTTP_200_OK)
